import sys
import threading
import cv2
import keyboard
import pyautogui
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPalette, QBrush
from PyQt5.QtWidgets import QWidget, QApplication
from playsound import playsound
from gaze_tracking import GazeTracking

# 마우스 이벤트 변수
sensitivity_x = 400
is_mouse_down = False
is_next = False

counting = 0


# 음성 출력 함수
def play_narrator(msg, file_name):
    playsound("./audio./" + file_name + "_audio.mp3")
    print(msg + '가 출력됩니다. - 파일명 : [' + file_name + '_audio.mp3]')


class main(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calibration")

        """변수 선언"""
        self.titleClass = None

        # 현재 디스플레이 사이즈
        self.screen_width, self.screen_height = pyautogui.size()

        # 카메라 초기세팅
        self.webCam = 1
        self.gaze = GazeTracking()
        self.counting = 0

        # 설정된 민감도
        self.sens = None
        self.load_sens()  # 파일 안의 값을 기준으로 초기화

        # 색상표
        self.color = {'gray': (153, 153, 153),
                      'green': (255, 149, 35),
                      'darkGray': (51, 51, 51),
                      'white': (255, 255, 255),
                      'red': (153, 153, 204)}

        # 민감도
        self.sensitivity = 1  # (0~2)

        # 방향
        self.direction = 0  # (0~4, 위, 아래, 왼쪽, 오른쪽)

        # rect 시작위치, 종료위치, 텍스트 내용과 위치
        self.rectLoc = [
            [(700, 185), (750, 235), ("up", (710, 215))],
            [(700, 245), (750, 295), ("down", (700, 275))],
            [(700, 305), (750, 355), ("left", (706, 335))],
            [(700, 365), (750, 415), ("right", (703, 395))]
        ]

        """버튼,라벨 생성"""
        self.btn_next1 = QPushButton(self)
        self.btn_next2 = QPushButton(self)
        self.btn_next3 = QPushButton(self)
        self.btn_next4 = QPushButton(self)
        self.textLabel0 = QLabel(self)
        self.textLabel1 = QLabel(self)
        self.textLabel2 = QLabel(self)
        self.textLabel3 = QLabel(self)
        self.textLabel4 = QLabel(self)
        self.textLabel5 = QLabel(self)
        self.textLabel6 = QLabel(self)
        self.textLabel7 = QLabel(self)
        self.textLabel8 = QLabel(self)

        """버튼, 라벨 붙이기"""
        # 다음 버튼
        self.btn_next1.setText("다음")
        self.btn_next1.setGeometry(900, 920, 200, 100)  # x, y, 버튼 가로, 버튼 세로
        self.btn_next1.clicked.connect(self.next_clicked)
        self.btn_next1.setStyleSheet('border: 2px solid #d0d0d0; font: 30pt "배달의민족 을지로체 TTF"; border-radius: 20px; background-color: rgb(35, 149, 255); border-style: outset; color:white;')

        # 뒤로 가기 버튼
        self.btn_next4.setText("뒤로가기")
        self.btn_next4.setGeometry(1800, 20, 100, 50)  # x, y, 버튼 가로, 버튼 세로
        self.btn_next4.clicked.connect(self.back_clicked)
        self.btn_next4.setStyleSheet(
            'border: 2px solid #d0d0d0; font: 14pt "배달의민족 을지로체 TTF"; border-radius: 20px; background-color: rgb(255, 0, 0); border-style: outset; color:white;')

        # 플레이 버튼
        self.btn_next2.setText("Play")
        self.btn_next2.setGeometry(1150, 910, 200, 100)  # x, y, 버튼 가로, 버튼 세로
        self.btn_next2.clicked.connect(self.play_clicked)

        self.btn_next2.setStyleSheet('border: 2px solid #d0d0d0; font: 30pt "배달의민족 을지로체 TTF"; border-radius: 20px; background-color: rgb(35, 149, 255); border-style: outset; color:white;')

        # 이전 버튼
        self.btn_next3.setText("Back")
        self.btn_next3.setGeometry(650, 910, 200, 100)  # x, y, 버튼 가로, 버튼 세로
        self.btn_next3.clicked.connect(self.set_notice)

        self.btn_next3.setStyleSheet('border: 2px solid #d0d0d0; font: 30pt "배달의민족 을지로체 TTF"; border-radius: 20px; background-color: rgb(35, 149, 255); border-style: outset; color:white;')

        # 민감도
        self.textLabel1.setText(repr(self.sens['up']))
        self.textLabel1.resize(1800, 80)
        self.textLabel1.move(1000, 220)
        self.textLabel1.setStyleSheet("font: 30pt Comic Sans MS")

        self.textLabel2.setText(repr(self.sens['down']))
        self.textLabel2.resize(1800, 80)
        self.textLabel2.move(1020, 340)
        self.textLabel2.setStyleSheet("font: 30pt Comic Sans MS")

        self.textLabel3.setText(repr(self.sens['left']))
        self.textLabel3.resize(1800, 80)
        self.textLabel3.move(1020, 460)
        self.textLabel3.setStyleSheet("font: 30pt Comic Sans MS")

        self.textLabel4.setText(repr(self.sens['right']))
        self.textLabel4.resize(1800, 80)
        self.textLabel4.move(1040, 580)
        self.textLabel4.setStyleSheet("font: 30pt Comic Sans MS")

        # csv파일로 부터 읽은 값 보이기
        self.show_fix()
        self.set_notice()

        # threading
        self.cam_th = threading.Thread(target=self.cameraON)
        self.cam_trigger = False
        print('def __init__')

    def load_sens(self):
        self.r_sens = pd.read_csv('./file/sensitivity.csv')  # 파일로 부터 읽어 온 sens 값
        self.sens = {'up': self.r_sens['up'], 'down': self.r_sens['down'], 'right': self.r_sens['right'], 'left': self.r_sens['left']}

    def valueHandler(self, value):
        scaleValue = float(value) / 100
        print(scaleValue, type(scaleValue))

    def set_notice(self):
        # 배경설정 전체 화면에 맞게 설정
        self.background_path = "./image/notice.png"
        self.oImage = QImage(self.background_path)
        self.sImage = self.oImage.scaled(QSize(self.screen_width, self.screen_height))

        # 파렛트 설정
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.sImage))
        self.setPalette(self.palette)

        self.textLabel1.setVisible(False)
        self.textLabel2.setVisible(False)
        self.textLabel3.setVisible(False)
        self.textLabel4.setVisible(False)
        self.btn_next1.setVisible(True)
        self.btn_next4.setVisible(True)
        self.btn_next2.setVisible(False)
        self.btn_next3.setVisible(False)


        self.cam_th = threading.Thread(target=self.cameraON)
        self.cam_trigger = False
        print('def set_notice')

    def set_check(self):
        # 배경설정 전체 화면에 맞게 설정
        self.background_path = "./image/check.png"
        self.oImage = QImage(self.background_path)
        self.sImage = self.oImage.scaled(QSize(self.screen_width, self.screen_height))

        # 파렛트 설정
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.sImage))
        self.setPalette(self.palette)

        self.textLabel1.setVisible(True)
        self.textLabel2.setVisible(True)
        self.textLabel3.setVisible(True)
        self.textLabel4.setVisible(True)
        self.btn_next1.setVisible(False)
        self.btn_next4.setVisible(False)
        self.btn_next2.setVisible(True)
        self.btn_next3.setVisible(True)
        self.textLabel1.setText(repr(self.sens['up'][0]))
        self.textLabel2.setText(repr(self.sens['down'][0]))
        self.textLabel3.setText(repr(self.sens['left'][0]))
        self.textLabel4.setText(repr(self.sens['right'][0]))
        print('def set_check')

    # notice 화면에 있는 뒤로가기 버튼
    def back_clicked(self):
        self.titleClass.show()
        self.hide()

    def play_clicked(self):
        '''# 민감도 파일 저장
        with open("./file/sensitibity.txt", 'w') as f:
            for k in self.sens.values():
                f.writelines(str(k))'''
        self.titleClass.show()
        self.set_notice()
        self.hide()
        print('def play_clicked')

    def open(self):
        self.set_check()
        self.update()
        self.show()
        print('def open')

    '''def valueHandler(self, value):
        pass'''

    def cameraON(self):
        self.webCam = cv2.VideoCapture(0)
        self.cam_trigger = True
        print('def cameraON')

    def next_clicked(self):
        global sensitivity_x
        global is_mouse_down
        global counting

        self.hide()
        self.cam_th.run()

        # 윈도우 설정
        cv2.namedWindow("calibration", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        print('def next_clicked')

        while True:

            if self.cam_trigger is True:
                _, camFrame = self.webCam.read()
                camFrame = cv2.flip(camFrame, 1)
                camFrame = cv2.resize(camFrame, dsize=(800, 600), interpolation=cv2.INTER_AREA)

                # 얼굴 측정
                self.gaze.refresh(camFrame)
                camFrame = self.gaze.annotated_frame()

                # 좌측 상단 텍스트
                text = ""
                text1 = ""

                # if self.gaze.is_blinking():
                #     text = "Blinking"
                if self.gaze.is_right():
                    text = "Looking right"
                elif self.gaze.is_left():
                    text = "Looking left"
                elif self.gaze.is_center():
                    text = "Looking center"

                if self.gaze.is_up():
                    text1 = "Looking up"
                elif self.gaze.is_down():
                    text1 = "Looking down"
                elif self.gaze.is_center():
                    text1 = "Looking center"

                cv2.putText(camFrame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
                cv2.putText(camFrame, text1, (90, 100), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)

                # 하단의 민감도 기본 회색 틀 (숫자, 원, 텍스트, 네모, 라인, 화살표라인)
                cv2.putText(camFrame, repr((sensitivity_x - 250) / 100), (385, 520), cv2.FONT_HERSHEY_DUPLEX, 0.6, self.color["green"], 1)
                cv2.line(camFrame, (250, 550), (550, 550), self.color["gray"], 6)

                # 우측의 방향 선택
                cv2.line(camFrame, (725, 190), (725, 400), self.color["gray"], 2)
                cv2.arrowedLine(camFrame, (725, 155), (725, 105), self.color["gray"], 2, tipLength=0.5)
                cv2.arrowedLine(camFrame, (725, 445), (725, 495), self.color["gray"], 2, tipLength=0.5)

                # 우측 하단의 next 버튼
                cv2.rectangle(camFrame, (690, 535), (760, 565), self.color["green"], -1)
                cv2.putText(camFrame, "next", (700, 555), cv2.FONT_HERSHEY_DUPLEX, 0.7,
                            self.color["white"], 1)

                # 우측 하단의 init 버튼
                cv2.rectangle(camFrame, (590, 535), (660, 565), self.color["green"], -1)
                cv2.putText(camFrame, "init", (609, 555), cv2.FONT_HERSHEY_DUPLEX, 0.7, self.color["white"], 1)

                # 좌측 하단의 뒤로가기 버튼
                cv2.rectangle(camFrame, (100, 535), (170, 565), self.color["gray"], -1)
                cv2.putText(camFrame, "back", (108, 555), cv2.FONT_HERSHEY_DUPLEX, 0.7, self.color["darkGray"], 1)



                # 슬라이드 선택 원 (파란 원)
                cv2.circle(camFrame, (sensitivity_x, 550), 10, self.color['green'], -1)

                # 다음 화면 넘어가게 하기
                global is_next

                if is_next is True:
                    # 종료시에 webCam 끄고, window 닫고, 다음 화면으로 전환한다.
                    self.webCam.release()
                    cv2.destroyAllWindows()
                    is_next = False
                    break

                # 800 600 네모
                for idx in range(len(self.rectLoc)):
                    if idx is self.direction:
                        cv2.rectangle(camFrame, self.rectLoc[idx][0], self.rectLoc[idx][1], self.color["green"], -1)
                        cv2.putText(camFrame, self.rectLoc[idx][2][0], self.rectLoc[idx][2][1], cv2.FONT_HERSHEY_DUPLEX, 0.7, self.color["white"], 1)
                    else:
                        cv2.rectangle(camFrame, self.rectLoc[idx][0], self.rectLoc[idx][1], self.color["gray"], -1)
                        cv2.putText(camFrame, self.rectLoc[idx][2][0], self.rectLoc[idx][2][1], cv2.FONT_HERSHEY_DUPLEX, 0.7, self.color["darkGray"], 1)

                if self.gaze.pupils_located:
                    if self.direction is 0:     # recommand up
                        cv2.putText(camFrame, "recommand : " + str(round(self.gaze.vertical_ratio(),2)), (90,140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 1, cv2.LINE_AA)

                    elif self.direction is 1:    # recommand down
                        cv2.putText(camFrame, "recommand : " + str(round(self.gaze.vertical_ratio(),2)), (90,140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 1, cv2.LINE_AA)

                    elif self.direction is 2:   # recommand left
                        cv2.putText(camFrame, "recommand : " + str(round(self.gaze.horizontal_ratio(),2)), (90,140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 1, cv2.LINE_AA)

                    elif self.direction is 3:   #recommand right
                        cv2.putText(camFrame, "recommand : " + str(round(self.gaze.horizontal_ratio(),2)), (90,140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 1, cv2.LINE_AA)
                else:
                    pass

                # 키보드 입력 및 이벤트
                if keyboard.is_pressed('left arrow'):
                    print('keyboard pressed')

                    if sensitivity_x > 250:
                        sensitivity_x -= 1
                elif keyboard.is_pressed('right arrow'):
                    if sensitivity_x < 550:
                        sensitivity_x += 1
                elif keyboard.is_pressed('up arrow'):
                    if self.direction > 0:
                        self.direction -= 1
                        self.show_fix()
                elif keyboard.is_pressed('down arrow'):
                    if self.direction < 3:
                        self.direction += 1
                        self.show_fix()
                elif keyboard.is_pressed('enter'):  # init
                    if self.direction is 0:
                        self.sens['up'] = 1.5
                    elif self.direction is 1:
                        self.sens['down'] = 1.5
                    elif self.direction is 2:
                        self.sens['left'] = 1.5
                    elif self.direction is 3:
                        self.sens['right'] = 1.5

                    self.show_fix()
                    thread_sound = threading.Thread(target=play_narrator, args=("효과음", "ding",))
                    thread_sound.start()
                elif keyboard.is_pressed('n'):
                    self.open()
                    is_next = True

                # 키보드 릴리즈 이벤트 수정바람
                # elif keyboard.release('down arrow') or keyboard.release('up arrow') or keyboard.release('right arrow') or keyboard.release('left arrow'):
                #     print('keyboard released')
                #     self.set_sensitivity()
                else:
                    pass

                # 민감도 조절
                '''self.gaze.change_limit(self.direction, self.sensitivity)'''

                # 윈도우 띄우기
                cv2.imshow("calibration", camFrame)
                cv2.setMouseCallback('calibration', self.mouseEvent)

                if cv2.waitKey(1) == 27:
                    break

    # 수정된 민감도 조정 및 화면에 바로 띄우기
    def set_sensitivity(self):
        if self.direction is 0:
            self.sens['up'] = (sensitivity_x - 250) / 100
        elif self.direction is 1:
            self.sens['down'] = (sensitivity_x - 250) / 100
        elif self.direction is 2:
            self.sens['left'] = (sensitivity_x - 250) / 100
        elif self.direction is 3:
            self.sens['right'] = (sensitivity_x - 250) / 100
        self.r_sens['up'] = self.sens['up']
        self.r_sens['down'] = self.sens['down']
        self.r_sens['right'] = self.sens['right']
        self.r_sens['left'] = self.sens['left']
        self.r_sens = self.r_sens[['up', 'down', 'right', 'left']]
        self.r_sens.to_csv('./file/sensitivity.csv')
        self.load_sens()
        self.gaze.load_threshold()

    # 슬라이드에 fix 된 값 보여주기
    def show_fix(self):
        global sensitivity_x
        if self.direction is 0:
            sensitivity_x = int(self.sens['up'] * 100.0 + 250.0)
        elif self.direction is 1:
            sensitivity_x = int(self.sens['down'] * 100.0 + 250.0)
        elif self.direction is 2:
            sensitivity_x = int(self.sens['left'] * 100.0 + 250.0)
        elif self.direction is 3:
            sensitivity_x = int(self.sens['right'] * 100.0 + 250.0)

    # 마우스 이벤트
    def mouseEvent(self, event, x, y, flags, param):
        global sensitivity_x
        global is_mouse_down
        global is_next

        if event == cv2.EVENT_LBUTTONDOWN:
            print('button click')
            # 슬라이드
            if 250 <= x <= 550 and 545 <= y <= 555:
                is_mouse_down = True
                sensitivity_x = x
            # 우측 방향 선택 버튼
            if 700 <= x <= 750 and 185 <= y <= 235:  # up button
                self.direction = 0
                self.show_fix()

            elif 700 <= x <= 750 and 245 <= y <= 295:  # down button
                self.direction = 1
                self.show_fix()

            elif 700 <= x <= 750 and 305 <= y <= 355:  # left button
                self.direction = 2
                self.show_fix()

            elif 700 <= x <= 750 and 365 <= y <= 415:  # right button
                self.direction = 3
                self.show_fix()

            elif 690 <= x <= 760 and 535 <= y <= 565:  # 다음 버튼
                self.open()
                is_next = True

            elif 100 <= x <= 170 and 535 <= y <= 565:  # back 버튼
                is_next = True
                self.cam_th = threading.Thread(target=self.cameraON)
                self.showFullScreen()

                # 초기화 버튼
            elif 590 <= x <= 660 and 535 <= y <= 565:  # init 버튼
                if self.direction is 0:
                    self.sens['up'] = 1.5
                elif self.direction is 1:
                    self.sens['down'] = 1.5
                elif self.direction is 2:
                    self.sens['left'] = 1.5
                elif self.direction is 3:
                    self.sens['right'] = 1.5

                self.show_fix()
                thread_sound = threading.Thread(target=play_narrator, args=("효과음", "ding",))
                thread_sound.start()

        elif event == cv2.EVENT_MOUSEMOVE and is_mouse_down is True:

            print('button click')

            if 250 <= x <= 550 and 545 <= y <= 555:
                sensitivity_x = x
            elif x < 250:
                sensitivity_x = 250
            elif x > 550:
                sensitivity_x = 550

        elif event == cv2.EVENT_LBUTTONUP:

            is_mouse_down = False
            self.set_sensitivity()

    def starter(self, titleClass):
        self.titleClass = titleClass
        self.showFullScreen()
        print('def start')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = main()
    form.showFullScreen()
    sys.exit(app.exec_())
