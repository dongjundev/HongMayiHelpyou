import sys

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QImage, QPalette, QBrush
from PyQt5.QtWidgets import *
from PyQt5 import uic
import pandas as pd

form_class = uic.loadUiType('./ui/Title_.ui')[0]
cam = True

class Title(QWidget, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Main")

        # 배경설정 전체 화면에 맞게 설정
        self.background_path = "./image/3.png"
        self.oImage = QImage(self.background_path)
        self.sImage = self.oImage.scaled(QSize(1920, 1080))

        # 파렛트 설정
        self.palette = QPalette()
        self.palette.setBrush(10, QBrush(self.sImage))
        self.setPalette(self.palette)

        # 버튼 이벤트 등록 ##
        self.re_btn.clicked.connect(lambda state, button=self.re_btn: self.btn_clicked(button))
        self.cal_btn.clicked.connect(lambda state, button=self.cal_btn: self.btn_clicked(button))
        self.start_btn.clicked.connect(lambda state, button=self.start_btn: self.btn_clicked(button))

        self.exec_btn.clicked.connect(self.exec)


        # self.search_btn.clicked.connect(lambda state, button = self.search_btn : self.btn_clicked(state, button))
        self.del_btn.clicked.connect(self.deleteFriend)



        # csv 파일로 부터 친구목록 (thread = id) 읽어 와서 리스트로 저장
        self.f = pd.read_csv('./file/friend.csv')

        # 친구목록 로드
        self.fillFriend()

        # 변수 선언
        self.clientClass = None
        self.calibrationClass = None

    def fillFriend(self):  # 타이틀 창에서 친구 목록 나타내기
        self.friendWidget.clear()
        self.f = pd.read_csv('./file/friend.csv')
        phone = self.f['phone'].tolist()
        name = self.f['name'].tolist()

        for p, n in zip(phone, name):
            tempItem = QListWidgetItem()
            tempItem.setText(n + ' / ' + str(p))
            self.friendWidget.addItem(tempItem)

    def btn_clicked(self, button):  # 버튼 이벤트 -> 버튼에 써진 텍스트로 이벤트 구분
        now_text = button.text()

        if now_text == '등록':
            if self.name_le is not '' and self.phone_le1 is not '' and self.phone_le2 is not '':
                # 번호는 010-0000-0000 형식으로 입력해야함
                num1 = self.phone_le1.text()
                num2 = self.phone_le2.text()

                num = '010-' + num1 + '-' + num2
                temp = pd.DataFrame({"name": [self.name_le.text()], "phone": [num]})

                self.f = pd.concat([self.f, temp], sort=False)
                self.f = self.f[['name', 'phone']]
                self.f.to_csv('./file/friend.csv')
                self.name_le.setText('')
                self.phone_le1.setText('')
                self.phone_le2.setText('')

            else:
                self.name_le.setText('입력을 확인하세요')
                self.phone_le1.setText('')
                self.phone_le2.setText('')

            self.fillFriend()

        elif now_text == '시작':
            self.clientClass.starter(self)
            self.hide()

        elif now_text == '교정':
            self.calibrationClass.starter(self)
            self.hide()

    def showUI(self, clientClass, calibrationClass):
        self.clientClass = clientClass
        self.calibrationClass = calibrationClass
        self.showFullScreen()

    def deleteFriend(self):  # 친구 삭제 이벤트 -> 선택된 열을 상수로 받아와서 csv파일에서 해당 열 삭제 -> 친구 목록 최신화
        row = self.friendWidget.currentRow()
        self.f = self.f.drop(self.f.index[row])
        self.f = self.f[['name', 'phone']]
        self.f.to_csv('./file/friend.csv')
        self.fillFriend()

    def exec(self):
        exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Title()
    w.showFullScreen()
    sys.exit(app.exec_())
