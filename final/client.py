import cv2
import sys
from PyQt5 import uic
import PyQt5.QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import gtts
import playsound
import gaze_tracking
import time
import threading
import NewGallery
import pandas as pd
import dlib
import serial
import SendMessage

# 아두이노
try:
    ard = serial.Serial('COM3', 9600)  # 창문
    ser = serial.Serial('COM5', 9600)  # Start serial communication // 침대
except Exception as ex:
    print("아두이노 시리얼 에러\n{}".format(ex))
    pass

window = False
bad = False
is_setStyle_blue = False   # 파란색으로 색칠 되었는지 여부

"""새로 추가된 부분"""
face_detector = dlib.get_frontal_face_detector()
faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eyeCascade = cv2.CascadeClassifier('haarcascade_eye.xml')


def play_narrator(button=None, file_name=""):
    if file_name is not "":
        now_name = file_name
    else:
        now_name = button.objectName()
    print(now_name)
    playsound.playsound("./audio/" + now_name + "_audio.mp3")
    print('파일명 : [' + now_name + '_audio.mp3]')


def save_narrator(msg, file_name):
    engine = gtts.gTTS(text=msg, lang='ko')
    engine.save("./audio/" + file_name + "_audio.mp3")
    print(msg + '의 음성이 [' + file_name + '_audio.mp3] 파일로 저장 되었습니다.')


# UI 읽기
form_class = uic.loadUiType('./ui/Ui.ui')[0]


class main(QWidget, form_class, threading.Thread):

    def __init__(self):
        # UI 파일을 파이썬 코드에서 로드하기 위한 작업
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("May I Help You__Client")

        # UI property 를 이용하여 아래의 위젯을 보이지 않게한다. (위치 중요, 처음에 로딩시 뜨는 경우 있음)
        self.bed_widget.hide()
        self.eat_widget.hide()
        self.light_widget.hide()
        self.toilet_widget.hide()
        self.window_widget.hide()
        self.temperature_widget.hide()

        # 필요 변수 선언
        ###
        self.on_widget = False
        ###

        self.save_btn_loc = None
        self.gallery = False
        self.gallery_show = None
        self.titleClass = None
        self.cpt = None
        self.fps = 24
        self.frame = QLabel(self)
        self.timer = PyQt5.QtCore.QTimer()
        self.gaze = gaze_tracking.GazeTracking()
        self.btn_loc = [0, 0]  # 현재 선택된 위치
        self.prevTime = 0  # 응답 시간을 위해 변수로 선언
        self.cur_state = ""  # 현재 눈 위치 상태
        self.btn_cycle = 0  # 버튼 클릭까지의 사이클
        self.cam = True  # 캠 on/off
        self.eye = True  # 시선 on/off
        self.btn_arr = [[self.bed_btn, self.eat_btn, self.light_btn, self.textEdit, self.clear_btn],
                        [self.water_btn, self.eye_btn, self.toilet_btn, self.temperature_btn, self.cam_btn],
                        [self.window_btn, self.emergency_btn, self.out_btn, self.pose_btn, self.gallary]]  # 버튼 2차 배열
        # tracking 8개 버튼
        self.f = pd.read_csv('./file/friend.csv')
        self.bed_btn.clicked.connect(lambda state, widget=self.bed_widget: self.open_widget(state, widget))  # 침대
        self.eat_btn.clicked.connect(lambda state, widget=self.eat_widget: self.open_widget(state, widget))  # 식사
        self.light_btn.clicked.connect(lambda state, widget=self.light_widget: self.open_widget(state, widget))  # 전등
        self.water_btn.clicked.connect(lambda state, button=self.water_btn: self.btn_clicked(state, button))  # 물
        self.eye_btn.clicked.connect(self.eye_clicked)  # 중앙 버튼
        self.toilet_btn.clicked.connect(lambda state, widget=self.toilet_widget: self.open_widget(state, widget))  # 화장실
        self.window_btn.clicked.connect(lambda state, widget=self.window_widget: self.open_widget(state, widget))  # 창문
        self.emergency_btn.clicked.connect(
            lambda state, button=self.emergency_btn: self.btn_clicked(state, button))  # 비상호출
        self.out_btn.clicked.connect(lambda state, button=self.out_btn: self.btn_clicked(state, button))  # 외출

        # 식사
        self.hungry_btn.clicked.connect(
            lambda state, button=self.hungry_btn, widget=self.eat_widget: self.btn_clicked(state, button,
                                                                                           widget))  # 배고프다
        self.full_btn.clicked.connect(
            lambda state, button=self.full_btn, widget=self.eat_widget: self.btn_clicked(state, button, widget))  # 배부르다

        # 화장실
        self.big_btn.clicked.connect(
            lambda state, button=self.big_btn, widget=self.toilet_widget: self.btn_clicked(state, button, widget))  # 큰일
        self.small_btn.clicked.connect(
            lambda state, button=self.small_btn, widget=self.toilet_widget: self.btn_clicked(state, button,
                                                                                             widget))  # 작은일

        # 전등
        self.light_on_btn.clicked.connect(
            lambda state, button=self.light_on_btn, widget=self.light_widget: self.btn_clicked(state, button,
                                                                                               widget))  # 조명켜기
        self.light_off_btn.clicked.connect(
            lambda state, button=self.light_off_btn, widget=self.light_widget: self.btn_clicked(state, button,
                                                                                                widget))  # 조명끄기

        # 창문
        self.window_open_btn.clicked.connect(
            lambda state, button=self.window_open_btn, widget=self.window_widget: self.btn_clicked(state, button,
                                                                                                   widget))  # 창문열기
        self.window_close_btn.clicked.connect(
            lambda state, button=self.window_close_btn, widget=self.window_widget: self.btn_clicked(state, button,
                                                                                                    widget))  # 창문닫기

        # 침대
        self.bed_up_btn.clicked.connect(
            lambda state, button=self.bed_up_btn, widget=self.bed_widget: self.btn_clicked(state, button,
                                                                                           widget))  # 침대올리기
        self.bed_down_btn.clicked.connect(
            lambda state, button=self.bed_down_btn, widget=self.bed_widget: self.btn_clicked(state, button,
                                                                                             widget))  # 침대내리기

        # 온도
        self.hot_btn.clicked.connect(
            lambda state, button=self.hot_btn, widget=self.temperature_widget: self.btn_clicked(state, button,
                                                                                                widget))  # 뜨거움
        self.cold_btn.clicked.connect(
            lambda state, button=self.cold_btn, widget=self.temperature_widget: self.btn_clicked(state, button, widget))

        # 자세
        self.pose_btn.clicked.connect(lambda state, button=self.pose_btn: self.btn_clicked(state, button))

        # 좌측 버튼
        self.temperature_btn.clicked.connect(
            lambda state, widget=self.temperature_widget: self.open_widget(state, widget))
        self.cam_btn.clicked.connect(self.cam_clicked)  # CAM버튼
        self.clear_btn.clicked.connect(self.btn_clear)  # 삭제 버튼
        self.gallary.clicked.connect(self.gallery_clicked)  # Gallery 버튼

        # 백 버튼
        self.eat_back_btn.clicked.connect(lambda state, widget=self.eat_widget: self.back_btn_clicked(state, widget))
        self.bed_back_btn.clicked.connect(lambda state, widget=self.bed_widget: self.back_btn_clicked(state, widget))
        self.light_back_btn.clicked.connect(
            lambda state, widget=self.light_widget: self.back_btn_clicked(state, widget))
        self.toilet_back_btn.clicked.connect(
            lambda state, widget=self.toilet_widget: self.back_btn_clicked(state, widget))
        self.window_back_btn.clicked.connect(
            lambda state, widget=self.window_widget: self.back_btn_clicked(state, widget))
        self.temperature_back_btn.clicked.connect(
            lambda state, widget=self.temperature_widget: self.back_btn_clicked(state, widget))

        # 나가기
        self.exit_btn.clicked.connect(self.exit_clicked)

        # 스레드
        self.cam_th = threading.Thread(target=self.cameraON)
        self.cam_trigger = False

        self.frame_th = threading.Thread(target=self.nextFrameSlot)
        self.frame_trigger = False

        self.default_style_sheet = []

        for temp_arr in self.btn_arr:
            for btn in temp_arr:
                self.default_style_sheet.append(btn.styleSheet())

    def cameraON(self):
        self.cpt = cv2.VideoCapture(0)
        self.cam_trigger = True
        print('def cameraON')

    def exit_clicked(self):
        global is_setStyle_blue
        is_setStyle_blue = False
        self.timer.stop()
        self.cpt = None

        i = 0
        for temp_arr in self.btn_arr:
            for btn in temp_arr:
                btn.setStyleSheet(self.default_style_sheet[i])
                i += 1

        self.btn_loc = [0, 0]  # 현재 선택된 위치
        self.prevTime = 0  # 응답 시간을 위해 변수로 선언
        self.cur_state = ""  # 현재 눈 위치 상태
        self.btn_cycle = 0  # 버튼 클릭까지의 사이클
        self.cam = True  # 캠 on/off
        self.eye = True  # 시선 on/off
        self.btn_arr = [[self.bed_btn, self.eat_btn, self.light_btn, self.textEdit, self.clear_btn],
                        [self.water_btn, self.eye_btn, self.toilet_btn, self.temperature_btn, self.cam_btn],
                        [self.window_btn, self.emergency_btn, self.out_btn, self.pose_btn, self.gallary]]  # 버튼 2차 배열
        self.textEdit.setText("메세지 출력 :\n\n")
        # 스레드
        self.cam_trigger = False
        self.cam_th = threading.Thread(target=self.cameraON)
        self.frame_th = threading.Thread(target=self.nextFrameSlot)
        self.frame_trigger = False

        self.hide()
        self.titleClass.showFullScreen()


    def gallery_clicked(self):
        global is_setStyle_blue
        self.gallery_show = NewGallery.NewGallery()
        self.gallery_show.showFullScreen()
        self.gallery_show.clientClass(self)
        self.btn_arr = [[self.gallery_show.btn_next], [self.gallery_show.btn_back], [self.gallery_show.btn_play],
                         [self.gallery_show.btn_exit]]
        is_setStyle_blue = False
        self.save_btn_loc = self.btn_loc
        self.btn_loc = [0, 0]
        self.prevTime = 0  # 응답 시간을 위해 변수로 선언
        self.cur_state = ""  # 현재 눈 위치 상태
        self.btn_cycle = 0  # 버튼 클릭까지의 사이클

    def eye_clicked(self):
        if self.eye_btn.isChecked():
            self.eye = False
            print(self.eye)
        else:
            self.eye = True
            print(self.eye)

    def open_widget(self, state, m_widget):
        global is_setStyle_blue
        if self.eye:
            self.on_widget = True
            if m_widget.objectName() == "bed_widget":
                self.btn_arr = [[self.bed_up_btn, self.bed_down_btn, self.bed_back_btn]]
            elif m_widget.objectName() == "eat_widget":
                self.btn_arr = [[self.hungry_btn, self.full_btn, self.eat_back_btn]]
            elif m_widget.objectName() == "light_widget":
                self.btn_arr = [[self.light_on_btn, self.light_off_btn, self.light_back_btn]]
            elif m_widget.objectName() == "toilet_widget":
                self.btn_arr = [[self.small_btn, self.big_btn, self.toilet_back_btn]]
            elif m_widget.objectName() == "window_widget":
                self.btn_arr = [[self.window_open_btn, self.window_close_btn, self.window_back_btn]]
            elif m_widget.objectName() == "temperature_widget":
                self.btn_arr = [[self.cold_btn, self.hot_btn, self.temperature_back_btn]]

            is_setStyle_blue = False
            m_widget.show()
            self.save_btn_loc = self.btn_loc
            self.btn_loc = [0, 0]
            self.prevTime = 0  # 응답 시간을 위해 변수로 선언
            self.cur_state = ""  # 현재 눈 위치 상태
            self.btn_cycle = 0  # 버튼 클릭까지의 사이클
            self.cam_man()

    def cam_man(self):  # 뒤로가기 버튼클릭시 사용
        if self.cam:
            self.frame.show()
        else:
            self.frame.hide()

    def open_window_arduino(self):
        global window
        if not window:
            op = 'b'
            #      ard.write(op.encode())
            window = True

    def close_window_arduino(self):
        global window
        if window:
            op = 'a'
            #       ard.write(op.encode())
            window = False

    def up_bed_arduino(self):
        global ser
        op = 'b'

    #     ser.write(op.encode())

    def down_bed_arduino(self):
        global ser
        op = 'a'

    #    ser.write(op.encode())

    def btn_clicked(self, state, button, m_widget=None):
        global is_setStyle_blue
        is_setStyle_blue = False
        if self.eye:
            exist_line_text = self.textEdit.toPlainText()
            now_text = button.text()
            SendMessage.sendMessage(button.objectName())
            if button.objectName() == "emergency_btn":
                now_text = "비상호출"

            self.textEdit.setText(exist_line_text + now_text + "\n")
            thread_sound = threading.Thread(target=play_narrator, args=(button, ""))  # 이동할때 나오는 소리
            thread_sound.start()

            ###
            if m_widget is not None:
                m_widget.hide()
                cur_btn = self.btn_arr[self.btn_loc[0]][self.btn_loc[1]]
                cur_btn.setStyleSheet(
                    'background-color: rgb(255, 255, 255); font: 50pt "배달의민족 을지로체 TTF"; border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
                self.btn_loc = self.save_btn_loc

            ######
            # 창문
            if now_text == "창문 열기":
                self.open_window_arduino()
            elif now_text == "창문 닫기":
                self.close_window_arduino()

            # 침대
            if now_text == "올리기":
                self.up_bed_arduino()
            elif now_text == "내리기":
                self.down_bed_arduino()
            ######

            self.cam_man()
            self.btn_arr = [[self.bed_btn, self.eat_btn, self.light_btn, self.textEdit, self.clear_btn],
                            [self.water_btn, self.eye_btn, self.toilet_btn, self.temperature_btn, self.cam_btn],
                            [self.window_btn, self.emergency_btn, self.out_btn, self.pose_btn,
                             self.gallary]]  # 버튼 2차 배열
            self.prevTime = 0  # 응답 시간을 위해 변수로 선언
            self.cur_state = ""  # 현재 눈 위치 상태
            self.btn_cycle = 0  # 버튼 클릭까지의 사이클
            self.on_widget = False
            self.frame.setGeometry(self.textEdit.geometry())

    ###
    def back_btn_clicked(self, state, widget):  # 뒤로가기 버튼 클릭
        global is_setStyle_blue
        is_setStyle_blue = False
        widget.hide()
        self.on_widget = False
        cur_btn = self.btn_arr[self.btn_loc[0]][self.btn_loc[1]]
        cur_btn.setStyleSheet(
            'background-color: rgb(255, 255, 255); font: 50pt "배달의민족 을지로체 TTF"; border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
        self.frame.setGeometry(self.textEdit.geometry())
        self.cam_man()
        self.btn_arr = [[self.bed_btn, self.eat_btn, self.light_btn, self.textEdit, self.clear_btn],
                        [self.water_btn, self.eye_btn, self.toilet_btn, self.temperature_btn, self.cam_btn],
                        [self.window_btn, self.emergency_btn, self.out_btn, self.pose_btn, self.gallary]]  # 버튼 2차 배열
        self.btn_loc = self.save_btn_loc
        self.prevTime = 0  # 응답 시간을 위해 변수로 선언
        self.cur_state = ""  # 현재 눈 위치 상태
        self.btn_cycle = 0  # 버튼 클릭까지의 사이클


    def btn_clear(self):
        self.textEdit.setText("메세지 출력 :\n\n")

    def cam_clicked(self):
        if self.cam is True:
            self.frame.hide()
            self.cam = False
        else:
            self.frame.show()
            self.cam = True

    def starter(self, titleClass, calibration_file=None):
        # 카메라 준비
        self.gaze.load_threshold()
        self.cam_th.start()
        self.frame.setGeometry(1380, 17, 448, 326)  # (캠위치 x좌표, 캠위치 y좌표, 캠크기 x축, 캠크기 y축)
        self.frame.setScaledContents(True)
        self.titleClass = titleClass
        self.frame_trigger = True
        self.frame_th.start()
        '''self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000 / self.fps)'''

        if calibration_file is not None:
            self.init_gaze(calibration_file)

        self.showFullScreen()

    def verify_pupil(self, eyeDir, blink=0):
        global is_setStyle_blue
        if blink == 1:          # 눈 감았을 때
            if self.prevTime == \
                    0.0:
                self.prevTime = time.time()
                self.cur_state = eyeDir
                self.btn_cycle = 0
            else:
                _timer = time.time() - self.prevTime
                if _timer >= 4.0:       # 눈감은 상태로 4초이상 대기
                    self.prevTime = 0.0
                    self.cur_state = "Looking center"
                    self.btn_cycle = 0
                    thread_click = threading.Thread(target=play_narrator, args=(None, "ding"))  # 버튼 클릭 소리
                    thread_click.start()
                    return True
                else:
                    if self.btn_cycle < int(_timer):
                        self.btn_cycle = int(_timer)
                        if self.btn_cycle == 1:
                            thread_dame = threading.Thread(target=play_narrator, args=(None, "3"))  # 클릭
                            thread_dame.start()
                        if self.btn_cycle == 2:
                            thread_dame = threading.Thread(target=play_narrator, args=(None, "2"))  # 클릭
                            thread_dame.start()
                        if self.btn_cycle == 3:
                            thread_dame = threading.Thread(target=play_narrator, args=(None, "1"))  # 클릭
                            thread_dame.start()

        else:           # 눈 떴을 때
            # if self.cur_state == "click":
            #     self.prevTime = 0  # 응답 시간을 위해 변수로 선언
            #     self.cur_state = ""  # 현재 눈 위치 상태
            #     self.btn_cycle = 0  # 버튼 클릭까지의 사이클

            if eyeDir == "Looking center":
                self.prevTime = 0.0
                self.cur_state = eyeDir
                self.btn_cycle = 0
            elif self.prevTime != 0.0 and self.cur_state == eyeDir:
                _timer = time.time() - self.prevTime
                if _timer > 1.2:        # 3초 이상보면 버튼 이동
                    self.prevTime = 0.0
                    self.cur_state = "Looking center"
                    self.btn_cycle = 0
                    thread_ding = threading.Thread(target=play_narrator, args=(None, "ding"))  # 이동할때 나오는 소리
                    thread_ding.start()
                    cur_btn = self.btn_arr[self.btn_loc[0]][self.btn_loc[1]]
                    if cur_btn == self.clear_btn or cur_btn == self.cam_btn or cur_btn == self.gallary:  # 우측 3개 버튼
                        cur_btn.setStyleSheet(
                            'background-color: rgb(217, 217, 217); font: 20pt "배달의민족 을지로체 TTF"; border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
                    elif cur_btn == self.pose_btn:      #자세 버튼
                        cur_btn.setStyleSheet(
                            'background-color: rgb(255, 255, 255); font: 35pt "배달의민족 을지로체 TTF"; border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
                    else:  # 나머지 버튼
                        cur_btn.setStyleSheet(
                            'background-color: rgb(255, 255, 255); font: 50pt "배달의민족 을지로체 TTF"; border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
                    is_setStyle_blue = False
                    return True
            elif self.prevTime == 0.0 and self.cur_state != eyeDir:
                self.prevTime = time.time()
                self.cur_state = eyeDir
        return False

    def nextFrameSlot(self):
        global is_setStyle_blue
        while True:
            if self.frame_trigger is False:
                break

            if self.cam_trigger is True:
                try:
                    _, frame = self.cpt.read()
                except Exception as ex:
                    reply = QMessageBox.question(self, 'Error', '카메라를 찾지 못했습니다. 다시 시도해주세요.', QMessageBox.Ok)
                    print(ex)
                    if reply == QMessageBox.Ok:
                        self.exit_clicked()
                        break

                if frame is not None:
                    frame = cv2.flip(frame, 1)

                    self.gaze.refresh(frame)
                    frame = self.gaze.annotated_frame()
                    l_eye, r_eye = self.gaze.is_click()
                    #print(l_eye, r_eye)


                    if self.gaze.pupils_located:
                        """
                        [순서]
                        1. 좌, 우 판단
                        2. 센터라면 위, 아래 판단
                        3. 지정된 행동 1초 유지시 1칸 이동
                        4. 눈을 3초 이상 감으면 선택

                        [필요]
                        - 버튼을 넣는 2차원 배열
                        - 현재 나의 좌표
                        """

                        eyeDir = ""
                        #print(l_eye, r_eye)

                        if self.gaze.is_right():
                            eyeDir = "Looking right"
                            if self.verify_pupil(eyeDir):
                                self.btn_loc[1] = (self.btn_loc[1] + 1) % len(self.btn_arr[self.btn_loc[0]])
                                if self.btn_loc[0] is 0 and self.btn_loc[1] is 3:
                                    self.btn_loc[1] = 4

                        elif self.gaze.is_left():
                            eyeDir = "Looking left"
                            if self.verify_pupil(eyeDir):
                                self.btn_loc[1] = (self.btn_loc[1] - 1) % len(self.btn_arr[self.btn_loc[0]])
                                if self.btn_loc[1] < 0:
                                    self.btn_loc[1] = len(self.btn_arr[0]) - 1
                                elif self.btn_loc[0] is 0 and self.btn_loc[1] is 3:
                                    self.btn_loc[1] = 2

                        elif self.gaze.is_up():
                            eyeDir = "Looking up"
                            if self.verify_pupil(eyeDir):
                                self.btn_loc[0] = (self.btn_loc[0] - 1) % len(self.btn_arr)
                                if self.btn_loc[0] < 0:
                                    self.btn_loc[0] = len(self.btn_arr) - 1
                                elif self.btn_loc[0] is 0 and self.btn_loc[1] is 3:
                                    self.btn_loc[1] = 4

                        elif self.gaze.is_down():
                            eyeDir = "Looking down"
                            if self.verify_pupil(eyeDir):
                                self.btn_loc[0] = (self.btn_loc[0] + 1) % len(self.btn_arr)
                            elif self.btn_loc[0] is 0 and self.btn_loc[1] is 3:
                                self.btn_loc[1] = 4
                        else:
                            eyeDir = "Looking center"
                            self.verify_pupil(eyeDir)

                        self.btn_loc[1] %= len(self.btn_arr[self.btn_loc[0]])  # 버튼 점검
                        cur_btn = self.btn_arr[self.btn_loc[0]][self.btn_loc[1]]
                        if is_setStyle_blue is False:
                            if cur_btn == self.clear_btn or cur_btn == self.cam_btn or cur_btn == self.gallary:  # 우측 버튼3개
                                cur_btn.setStyleSheet(
                                    'background-color: rgb(204, 232, 255); font: 20pt "배달의민족 을지로체 TTF";border: 2px solid #afafaf; border-radius: 20px; border-style: inset;')
                            elif cur_btn == self.pose_btn:
                                cur_btn.setStyleSheet(
                                    'background-color: rgb(204, 232, 255); font: 35pt "배달의민족 을지로체 TTF"; border: 2px solid #d0d0d0; border-radius: 20px; border-style: inset;')
                            #elif cur_btn == self.bed_btn or cur_btn == self.eat_btn or cur_btn == self.light_btn or cur_btn == self.water_btn or cur_btn == self.eye_btn or cur_btn == self.toilet_btn or cur_btn == self.temperature_btn or cur_btn == self.window_btn or cur_btn == self.emergency_btn or cur_btn == self.out_btn:
                            else:
                                cur_btn.setStyleSheet(
                                    'background-color: rgb(204, 232, 255); font: 50pt "배달의민족 을지로체 TTF";border: 2px solid #afafaf; border-radius: 20px; border-style: inset;')
                            is_setStyle_blue = True
                        #print(self.btn_loc, eyeDir, self.cur_state, self.prevTime, len(self.btn_arr),len(self.btn_arr[0]))
                        cv2.putText(frame, eyeDir, (60, 40), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 0, 255), 2)
                    else:
                        if l_eye == '- 0.0' and r_eye == '- 0.0':
                            eyeDir = "click"
                            if self.verify_pupil(eyeDir, blink=1):
                                cur_btn = self.btn_arr[self.btn_loc[0]][self.btn_loc[1]]
                                cur_btn.click()
                        else:
                            self.cur_state = ""
                            self.btn_cycle = 0
                            self.prevTime = 0.0

                    frame_img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
                    pix = QPixmap.fromImage(frame_img)
                    self.frame.setPixmap(pix)
                    if self.on_widget is True:
                        if self.eye:
                            self.frame.move(736, 50)
                    else:
                        self.frame.setGeometry(self.textEdit.geometry())  # (캠위치 x좌표, 캠위치 y좌표, 캠크기 x축, 캠크기 y축) 텍스트에딧 자리로 캠창 이동


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = main()
    w.showFullScreen()
    sys.exit(app.exec_())
