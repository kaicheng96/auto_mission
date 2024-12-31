# -*- coding:utf-8 -*-
# @Author: KwokFu
# @Time: 2024/12/24 11:21
# @File: app.py

import tkinter as tk
from tkinter import ttk


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("流程步骤添加器")
        # self.root.configure(background='blue')
        self.root.geometry('400x400+300+100')

        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=10)

        self.add_button = tk.Button(self.buttons_frame, text="添加", command=self.add_step)
        self.add_button.pack(side='left', padx=5)

        self.run_button = tk.Button(self.buttons_frame, text="运行", command=self.run_steps)
        self.run_button.pack(side='left', padx=5)

        # 创建一个容器用于放置步骤组合框和滚动条
        self.steps_container = tk.Frame(self.root)
        self.steps_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建一个画布用于放置步骤组合框，并使其可滚动
        self.canvas = tk.Canvas(self.steps_container)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建一个滚动条并绑定到画布
        self.scrollbar = ttk.Scrollbar(self.steps_container, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置画布的滚动区域
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # 创建一个内部框架，用于放置步骤组合框
        self.steps_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")

        # 创建一个内部框架，用于放置步骤组合框
        self.steps_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")

        self.steps = []

    def add_step(self):
        step_label = ttk.Label(self.steps_frame, text=f"步骤 {len(self.steps) + 1}:")
        step_label.grid(row=len(self.steps), column=0, padx=5, pady=5, sticky="w")

        step_combobox = ttk.Combobox(self.steps_frame, values=["单击", "滑动"], state="readonly")
        step_combobox.grid(row=len(self.steps), column=1, padx=5, pady=5)
        step_combobox.current(0)  # 设置默认选项为"单击"

        self.steps.append(step_combobox)

        # 更新滚动区域
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        # self.steps.append(step_combobox)

    def run_steps(self):
        for step in self.steps:
            print(step.get())  # 这里仅打印出每个步骤的选择，实际应用中可以执行相应的操作


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
