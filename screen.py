# -*- coding:utf-8 -*-
# @Author: KwokFu
# @Time: 2024/12/24 11:21
# @File: screen.py

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QFrame

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('流程步骤示例')
        self.setGeometry(100, 100, 300, 200)
        self.initUI()

    def initUI(self):
        # 创建垂直布局
        vertical_layout = QVBoxLayout()

        # 创建水平布局用于放置按钮
        button_layout = QHBoxLayout()

        # 创建“添加”和“运行”按钮
        self.add_button = QPushButton('添加', self)
        self.run_button = QPushButton('运行', self)

        # 将按钮添加到水平布局
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.run_button)

        # 创建一个分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        # 将水平布局添加到垂直布局
        vertical_layout.addWidget(line)
        vertical_layout.addLayout(button_layout)

        # 设置窗口的布局
        self.setLayout(vertical_layout)

        # 存储步骤和下拉框
        self.steps = []

        # 连接按钮的点击信号到槽函数
        self.add_button.clicked.connect(self.add_combobox)
        self.run_button.clicked.connect(self.run_steps)


    def add_combobox(self):
        # 创建步骤标签和下拉框
        step_number = len(self.steps) + 1
        step_label = QLabel(f"步骤{step_number}: 样式", self)
        combobox = QComboBox(self)
        combobox.addItems(["单击", "滑动"])

        # 创建一个水平布局用于放置步骤标签和下拉框
        step_layout = QHBoxLayout()
        step_layout.addWidget(step_label)
        step_layout.addWidget(combobox)

        # 添加到垂直布局中，位于按钮上方
        self.layout().insertLayout(len(self.steps), step_layout)

        # 存储步骤信息
        self.steps.append((step_label, combobox))

    def run_steps(self):
        # 打印每个下拉框的选择
        for step_label, combobox in self.steps:
            print(f"{step_label.text}: {combobox.currentText()}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())