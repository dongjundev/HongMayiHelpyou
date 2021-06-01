from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import cv2
import glob
import threading
import sys

width = 0
height = 0
next_image = 0  # 이미지 인덱스 값
count = 0  # 이미지 몇 장인지 카운트
num_count = 0  # 시간 카운트
play = True
# 폴더 내 모든 jpg 이미지 파일 이름 가져오기
images = glob.glob('./Gallery/*.jpg')  # 3840 2160, 4032 3024

for fname in images:
    count += 1


# count = len(images)

class NewGallery(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gallery")
        self.setGeometry(0, 0, 1920, 1080)
        self.setStyleSheet('background-color: rgb(198, 214, 228);')

        ###
        self.client = None

        # 타이머
        self.start_timer()

        # 이미지 띄움
        global next_image
        global width
        global height

        self.imgsize = cv2.imread(images[next_image], cv2.IMREAD_COLOR)
        height, width, i_ch = self.imgsize.shape
        # print("width = ",width,"height = ",height)
        if width > height:
            image = QPixmap(images[next_image])
            change_image = image.scaled(1740, 1080, Qt.KeepAspectRatioByExpanding)
            self.image_label = QLabel("", self)
            self.image_label.setGeometry(0, 0, 1740, 1080)
            self.image_label.setPixmap(change_image)
        elif height < 720 and width < 1280:
            image = QPixmap(images[next_image])
            self.image_label.setGeometry(0, 0, 1280, 720)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setPixmap(image)
        else:
            image = QPixmap(images[next_image])
            transform = QTransform()
            transform.rotate(90)
            change_image = image.scaled(640, 720, Qt.KeepAspectRatioByExpanding)
            self.image_label = QLabel("", self)
            self.image_label.setGeometry(320, 0, 1280, 720)
            self.image_label.setPixmap(change_image.transformed(transform))

        # 다음 이미지 버튼
        self.btn_next = QPushButton(QIcon('./image/next.png'), "", self)
        self.btn_next.setIconSize(QSize(105, 105))
        self.btn_next.setStyleSheet(
            'background-color: rgb(255, 255, 255); border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
        self.btn_next.setGeometry(1755, 16, 150, 250)
        self.btn_next.clicked.connect(self.next_clicked)

        # 재생 버튼
        self.btn_play = QPushButton(QIcon('./image/pause.png'), "", self)
        self.btn_play.setIconSize(QSize(95, 95))
        self.btn_play.setStyleSheet(
            'background-color: rgb(255, 255, 255); border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
        self.btn_play.setGeometry(1755, 544, 150, 250)
        self.btn_play.clicked.connect(self.play_clicked)

        # 이전 이미지 버튼
        self.btn_back = QPushButton(QIcon('./image/back.png'), "", self)
        self.btn_back.setStyleSheet(
            'background-color: rgb(255, 255, 255); border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
        self.btn_back.setIconSize(QSize(105, 105

                                        ))
        self.btn_back.setGeometry(1755, 282, 150, 250)
        self.btn_back.clicked.connect(self.back_clicked)

        # 종료 버튼
        self.btn_exit = QPushButton(QIcon('./image/exit.png'), "", self)
        self.btn_exit.setStyleSheet(
            'background-color: rgb(255, 255, 255); border: 2px solid #d0d0d0; border-radius: 20px; border-style: outset;')
        self.btn_exit.setIconSize(QSize(100, 100))
        self.btn_exit.setGeometry(1755, 806, 150, 250)
        self.btn_exit.clicked.connect(self.close_window)

    def picture(self):
        if width > height:
            image = QPixmap(images[next_image])
            change_image = image.scaled(1740, 1080, Qt.KeepAspectRatioByExpanding)
            self.image_label = QLabel("", self)
            self.image_label.setGeometry(0, 0, 1740, 1080)
            self.image_label.setPixmap(change_image)
        elif height < 720 and width < 1280:
            image = QPixmap(images[next_image])
            self.image_label.setGeometry(0, 0, 1280, 720)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setPixmap(image)
        else:
            image = QPixmap(images[next_image])
            transform = QTransform()
            transform.rotate(90)
            change_image = image.scaled(640, 720, Qt.KeepAspectRatioByExpanding)
            self.image_label = QLabel("", self)
            self.image_label.setGeometry(320, 0, 1280, 720)
            self.image_label.setPixmap(change_image.transformed(transform))

    ######
    def close_window(self):
        global next_image
        global num_count
        self.client.btn_arr = [[self.client.bed_btn, self.client.eat_btn, self.client.light_btn, self.client.clear_btn],
                               [self.client.water_btn, self.client.eye_btn, self.client.toilet_btn, self.client.temperature_btn, self.client.cam_btn],
                               [self.client.window_btn, self.client.emergency_btn, self.client.out_btn, self.client.pose_btn, self.client.gallary]]  # 버튼 2차 배열
        next_image = 0
        self.timeVar.stop()
        num_count = 0
        self.close()

        self.client.btn_loc = self.client.save_btn_loc
        self.client.prevTime = 0  # 응답 시간을 위해 변수로 선언
        self.client.cur_state = ""  # 현재 눈 위치 상태
        self.client.btn_cycle = 0  # 버튼 클릭까지의 사이클

    def clientClass(self, clientClass=None):
        self.client = clientClass

    def show_image(self):
        global width, height
        image_size = cv2.imread(images[next_image], cv2.IMREAD_COLOR)
        height, width, image_ch = image_size.shape
        if width > height:
            image = QPixmap(images[next_image])
            change_image = image.scaled(1740, 1080, Qt.KeepAspectRatioByExpanding)
            self.image_label.setGeometry(0, 0, 1740, 1080)
            self.image_label.setPixmap(change_image)
        elif height < 720 and width < 1280:
            image = QPixmap(images[next_image])
            self.image_label.setGeometry(0, 0, 1280, 720)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setPixmap(image)
        else:
            image = QPixmap(images[next_image])
            transform = QTransform()
            transform.rotate(90)
            change_image = image.scaled(640, 720, Qt.KeepAspectRatioByExpanding)
            self.image_label.setGeometry(320, 0, 640, 720)
            self.image_label.setPixmap(change_image.transformed(transform))

    def play_clicked(self):
        global play
        if play == True:
            play = False
            self.btn_play.setIcon(QIcon('./image/play.png'))
            self.timeVar.stop()
        elif play == False:
            play = True

            self.btn_play.setIcon(QIcon('./image/pause.png'))
            self.timeVar.start()

    def back_clicked(self):
        global next_image
        next_image -= 1
        self.show_image()
        if next_image == -(count):
            next_image = 0

    def next_clicked(self):
        global next_image
        next_image += 1
        self.show_image()
        if next_image == count - 1:
            next_image = 0

    def start_timer(self):
        self.timeVar = QTimer()
        self.timeVar.setInterval(1000)
        self.timeVar.timeout.connect(self.addtime)
        self.timeVar.start()

    def addtime(self):

        global num_count
        global next_image
        num_count += 1
        print(num_count)
        if num_count == 5:
            num_count = 0
            next_image += 1
            self.show_image()
            # gal_th = threading.Thread(target=self.show_image)
            # gal_th.start()

        if next_image == count - 1:
            next_image = 0


def main():
    myWindow = NewGallery()
    myWindow.showFullScreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    myWindow = NewGallery()
    myWindow.showFullScreen()
    sys.exit(app.exec_())
