from __future__ import division
import os
import cv2
import dlib
import numpy as np
from .calibration import Calibration
from .eye import Eye
from keras.models import load_model
from imutils import face_utils
import pandas as pd

# 얼굴의 각 구역 구분
JAWLINE_POINTS = list(range(0, 17))
LEFT_EYEBROW_POINTS = list(range(17, 22))
RIGHT_EYEBROW_POINTS = list(range(22, 27))
NOSE_POINTS = list(range(27, 36))
LEFT_EYE_POINTS = list(range(36, 42))
RIGHT_EYE_POINTS = list(range(42, 48))
MOUTH_OUTLINE_POINTS = list(range(48, 61))
MOUTH_INNER_POINTS = list(range(61, 68))
IMG_SIZE = (34, 26)

# calibration 용
limit_value = [[0.55, 0.45, 0.35], [0.65, 0.75, 0.85], [0.45, 0.35, 0.25], [0.55, 0.65, 0.75]]


class GazeTracking(object):
    """
    This class tracks the user's gaze.
    It provides useful information like the position of the eyes
    and pupils and allows to know if the eyes are open or closed
    """

    def __init__(self):
        self.frame = None
        self.eye_left = None
        self.eye_right = None
        self.calibration = Calibration()

        # _face_detector is used to detect faces
        # 아래의 변수는 클래스에 포함된 변수로써 얼굴을 탐지할때 사용한다.
        self._face_detector = dlib.get_frontal_face_detector()

        # _predictor is used to get facial landmarks of a given face
        # 아래의 변수는 주어진 얼굴의 특징점을 얻기위해 사용한다.
        cwd = os.path.abspath(os.path.dirname(__file__))
        model_path = os.path.abspath(os.path.join(cwd, "trained_models/shape_predictor_68_face_landmarks.dat"))  # 특징점을 찾기위한 데이터
        self._predictor = dlib.shape_predictor(model_path)  # predictor 에게 특징점 모델을 갖게한다.

        """추가된 부분"""
        self.limit_up = None
        self.limit_down = None
        self.limit_left = None
        self.limit_right = None

        # 감은 눈 학습된 모델 로드 (전역으로 설정)
        trained_path = os.path.abspath(os.path.join(cwd, "trained_models/2018_12_17_22_58_35.h5"))
        self.model = load_model(trained_path)

        self.load_threshold()
        """---------"""

    @property
    def pupils_located(self):
        """Check that the pupils have been located"""
        try:
            int(self.eye_left.pupil.x)
            int(self.eye_left.pupil.y)
            int(self.eye_right.pupil.x)
            int(self.eye_right.pupil.y)
            return True
        except :
            # print(ex)
            return False

    def _analyze(self):
        """Detects the face and initialize Eye objects"""
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_detector(frame)

        try:
            landmarks = self._predictor(frame, faces[0])
            self.eye_left = Eye(frame, landmarks, 0, self.calibration)
            self.eye_right = Eye(frame, landmarks, 1, self.calibration)

            """추가된 부분"""
            if self.pupils_located:
                # 2020.03.23, 추가
                # 오른쪽 눈 랜드마크 탐지 => 이미지 재활용하면 랜드마크 조심
                landmarks_display = np.matrix([[p.x, p.y] for p in landmarks.parts()])
                landmarks_display = landmarks_display[RIGHT_EYE_POINTS]
                for idx, point in enumerate(landmarks_display):
                    pos = (point[0, 0], point[0, 1])
                    cv2.circle(self.frame, pos, 1, color=(255, 0, 0), thickness=1)
            """---------"""

        except IndexError:
            self.eye_left = None
            self.eye_right = None

    def refresh(self, frame):  # 클라이언트 캠화면
        """
        Refreshes the frame and analyzes it.
        프레임을 업데이트 시키고 새로운 프레임을 분석한다.
        Arguments:
            frame (numpy.ndarray): The frame to analyze
            분석하기위한 프레임
        """
        self.frame = frame
        self.frame = self.im_trim(frame)
        self._analyze()


    # 이미지의 가로세로 불러온다.
    # 상하좌우 25% 삭제 후 자른 뒤 2배 키우는 함수
    # 어떤 스레드에서는 self.frame=frame 에서 _analyze 사용,
    # 어떤 스레드는 self.frame=self.im_trim(frame)에서 _analyze 사용
    # ==>> 오류 도출
    
    # ----> 해당 함수 사용 X
    
    def im_trim(self, img):  # 이미지 자르고 확대
        '''
        x = 10
        y = 10

        w = 500
        h = 300
        img_trim = img[y:y+h, x:x+w]
        return img_trim
        '''
        h, w = img.shape[:2]
        s_h = int(h * 0.25)
        f_h = int(h * 0.75)
        s_w = int(w * 0.25)
        f_w = int(w * 0.75)
        img_trim = img[s_h: f_h, s_w:f_w]
        img_trim = cv2.resize(img_trim, dsize=(0, 0), fx=2.0, fy=2.0)
        return img_trim


    def change_limit(self, direction, sensitibity):
        if direction is 0:
            self.limit_up = limit_value[0][sensitibity]
        elif direction is 1:
            self.limit_down = limit_value[1][sensitibity]
        elif direction is 2:
            self.limit_left = limit_value[2][sensitibity]
        elif direction is 3:
            self.limit_right = limit_value[3][sensitibity]

    def pupil_left_coords(self):
        """Returns the coordinates of the left pupil"""
        if self.pupils_located:
            x = self.eye_left.origin[0] + self.eye_left.pupil.x
            y = self.eye_left.origin[1] + self.eye_left.pupil.y
            return x, y

    def pupil_right_coords(self):
        """Returns the coordinates of the right pupil"""
        if self.pupils_located:
            x = self.eye_right.origin[0] + self.eye_right.pupil.x
            y = self.eye_right.origin[1] + self.eye_right.pupil.y
            return x, y

    def horizontal_ratio(self):
        """Returns a number between 0.0 and 1.0 that indicates the
        horizontal direction of the gaze. The extreme right is 0.0,
        the center is 0.5 and the extreme left is 1.0
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.x / (self.eye_left.center[0] * 2 - 10)
            pupil_right = self.eye_right.pupil.x / (self.eye_right.center[0] * 2 - 10)
            return (pupil_left + pupil_right) / 2

    def vertical_ratio(self):
        """Returns a number between 0.0 and 1.0 that indicates the
        vertical direction of the gaze. The extreme top is 0.0,
        the center is 0.5 and the extreme bottom is 1.0
        0.0에서 1.0 사이의 값을 반환합니다.
        이 숫자는 시선의 세로방향을 의미합니다. 극한의 top을 보고있다면 0.0
        중앙은 0.5, 아주 아래쪽을 본다면 1.0을 반환합니다.
        """
        if self.pupils_located:
            pupil_left = self.eye_left.pupil.y / (self.eye_left.center[1] * 2 - 10)
            pupil_right = self.eye_right.pupil.y / (self.eye_right.center[1] * 2 - 10)
            return (pupil_left + pupil_right) / 2

    def is_left(self):
        """
        Returns true if the user is looking to the right
        오른쪽을 보면 True를 반환합니다.
        """
        if self.pupils_located:
            return self.horizontal_ratio() <= self.limit_left  # 0.5

    def is_right(self):
        """
        Returns true if the user is looking to the left
        왼쪽을 보면 True를 반환합니다.
        """
        if self.pupils_located:
            return self.horizontal_ratio() >= self.limit_right  # 0.75

    def is_center(self):
        """
        Returns true if the user is looking to the center
        중앙을 보면 True를 반환합니다.
        """
        if self.pupils_located:
            return self.is_right() is not True and self.is_left() is not True

    def is_up(self):
        """위를 보면 True를 반환합니다."""
        if self.pupils_located:
            # print(self.vertical_ratio())
            return self.vertical_ratio() <= self.limit_up  # 0.65

    def is_down(self):
        """아래를 보면 True를 반환합니다."""
        if self.pupils_located:
            return self.vertical_ratio() >= self.limit_down  # and self.is_blinking() >= 0.8

    def crop_eye(self, img, eye_points):
        global IMG_SIZE
        x1, y1 = np.amin(eye_points, axis=0)
        x2, y2 = np.amax(eye_points, axis=0)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

        w = (x2 - x1) * 1.2
        h = w * IMG_SIZE[1] / IMG_SIZE[0]

        margin_x, margin_y = w / 2, h / 2

        min_x, min_y = max(int(cx - margin_x), 0), max(int(cy - margin_y), 0)
        max_x, max_y = min(int(cx + margin_x), cx), min(int(cy + margin_y), cy)

        eye_rect = np.rint([min_x, min_y, max_x, max_y]).astype(np.int)  # rint -> 가장 가까운 정수로 변환

        eye_img = img[eye_rect[1]:eye_rect[3], eye_rect[0]:eye_rect[2]]

        return eye_img, eye_rect

    # def is_blinkingblinking(self):
    #     """
    #     Returns true if the user closes his eyes
    #     눈을 감으면 Return True
    #     """
    #     if self.pupils_located:
    #         blinking_ratio = (self.eye_left.blinking + self.eye_right.blinking) / 2
    #         return blinking_ratio > 3.8

    def is_click(self):
        global IMG_SIZE
        state_l = None
        state_r = None
        """이거 유뮤 확인"""
        # img = cv2.resize(self.frame, dsize=(0, 0), fx=0.5, fy=0.5)
        img = self.frame
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = self._face_detector(gray)

        for face in faces:
            shapes = self._predictor(gray, face)
            shapes = face_utils.shape_to_np(shapes)

            eye_img_l, eye_rect_l = self.crop_eye(gray, eye_points=shapes[36:42])
            eye_img_r, eye_rect_r = self.crop_eye(gray, eye_points=shapes[42:48])

            eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE)
            eye_img_r = cv2.resize(eye_img_r, dsize=IMG_SIZE)
            eye_img_r = cv2.flip(eye_img_r, flipCode=1)  # 왼쪽눈 모델만 있어서 왼쪽을 플립

            eye_input_l = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
            eye_input_r = eye_img_r.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.

            pred_l = self.model.predict(eye_input_l)
            pred_r = self.model.predict(eye_input_r)

            # visualize
            state_l = 'O %.1f' if pred_l > 0.1 else '- %.1f'
            state_r = 'O %.1f' if pred_r > 0.1 else '- %.1f'

            state_l = state_l % pred_l
            state_r = state_r % pred_r

        return state_l, state_r

    def annotated_frame(self):
        """
        Returns the main frame with pupils highlighted
        동공 부분을 색칠하여 Return 합니다.
        """
        frame = self.frame.copy()

        if self.pupils_located:
            x_left, y_left = self.pupil_left_coords()
            x_right, y_right = self.pupil_right_coords()
            # color = (0, 255, 0)
            # cv2.line(frame, (x_left - 5, y_left), (x_left + 5, y_left), color)
            # cv2.line(frame, (x_left, y_left - 5), (x_left, y_left + 5), color)
            # cv2.line(frame, (x_right - 5, y_right), (x_right + 5, y_right), color)
            # cv2.line(frame, (x_right, y_right - 5), (x_right, y_right + 5), color)

            # 홍채 중앙에 빨간색 원을 표시한다.
            # cv2.circle(이미지, 좌표, 반지름, 색상, 두께)
            # [tip. thickness = -1, 안쪽이 채워진 원]
            red_color = (255, 0, 0)
            cv2.circle(frame, (x_left, y_left), 3, red_color, thickness=1)
            cv2.circle(frame, (x_right, y_right), 3, red_color, thickness=1)
        return frame

    """sensitivity.csv 불러오는 작업"""

    def load_threshold(self):  # sensitivity 읽어오기
        upper_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))  # 파일 위치 절대경로로 읽고
        path = os.path.abspath(os.path.join(upper_path, 'file/sensitivity.csv'))  # sensitivity를 부른다.
        self.ratio = pd.read_csv(path)  # csv 파일 읽어와서
        self.limit_down = self.ratio['down'][0]  # 모두 적용
        self.limit_up = self.ratio['up'][0]
        self.limit_right = self.ratio['right'][0]
        self.limit_left = self.ratio['left'][0]
