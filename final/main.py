"""
각 Class 관리 및 실행 파일이 존재하는지 여부 파악 후
main Class 를 띄운다.
"""

import sys
import os
import client
import title_
import calibration
from PyQt5.QtWidgets import *
from PyQt5 import uic
import ctypes
import pandas as pd

# UI 파일 로드
form_class = uic.loadUiType('./ui/init.ui')[0]

# 파일 로드
audio_path = "./audio"
audio_file = os.listdir(audio_path)

image_path = "./image"
image_file = os.listdir(image_path)

ui_path = "./ui"
ui_file = os.listdir(ui_path)

py_path = "./"
py_file = os.listdir(py_path)
py_file = [file for file in py_file if file.endswith(".py")]
print(py_file)


class main(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 변수 초기화
        self.count_files = len(ui_file) + len(audio_file) + len(image_file) + len(py_file) + 4
        self.count_now = 0
        self.titleClass = None
        self.clientClass = None
        self.calibrationClass = None
        self.calibration_file = None
        self.start_btn.setEnabled(False)

        # 버튼 연결
        self.start_btn.clicked.connect(self.starter)

        # self focusing
        self.focusWidget()

    def load(self):
        self.italicText("audio 파일을 검사합니다.")
        for k in audio_file:
            self.updateProcess(k)

        self.italicText("image 파일을 검사합니다.")
        for k in image_file:
            self.updateProcess(k)

        self.italicText("ui 파일을 검사합니다.")
        for k in ui_file:
            self.updateProcess(k)

        self.italicText("py 파일을 검사합니다.")
        for k in py_file:
            self.updateProcess(k)

        self.italicText("title 객체를 생성합니다...")
        self.titleClass = title_.Title()
        self.updateProcess("title Instance")

        self.italicText("calibration 객체를 생성합니다...")
        self.calibrationClass = calibration.main()
        self.updateProcess("calibration Instance")

        self.italicText("client 객체를 생성합니다...")
        self.clientClass = client.main()
        self.updateProcess("client Instance")

        try:
            self.italicText("교정 파일을 읽어옵니다...")
            self.calibration_file = pd.read_csv('./file/sensitivity.csv')
        except FileNotFoundError:
            self.messageBox("알림", "교정 파일을 읽어올 수 없습니다. start를 누르고 교정을 진행해주세요.")
            self.calibration_file = None
        self.updateProcess("교정파일 처리 완료")
        self.start_btn.setEnabled(True)

    @staticmethod
    def messageBox(title, text, style=0):
        return ctypes.windll.user32.MessageBoxW(None, text, title, style)

    def updateProcess(self, msg):
        self.count_now += 1
        self.init_progress.setValue(self.count_now / self.count_files * 100)
        self.appendText(msg)

    def italicText(self, msg):
        self.init_text.setFontItalic(True)
        self.init_text.append("\n" + msg)
        self.init_text.setFontItalic(False)

    def appendText(self, msg):
        self.init_text.append(str(msg).ljust(30) + "..... OK")

    def starter(self):
        self.titleClass.showUI(self.clientClass, self.calibrationClass)
        self.hide()

    def __del__(self):
        print("main.py의 main Class(이)가 정상적으로 소멸되었습니다.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = main()
    myWindow.show()
    myWindow.load()
    app.exec_()
