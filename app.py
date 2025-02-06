# -*- coding:utf-8 -*-
# @Author: scofield
# @Time: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}  # 动态生成当前时间
# @File: app.py

"""
功能描述：
    1. 程序实现用户输入流程以及选择流程种允许项。
    2. 程序允许添加、删除流程步骤，允许保存流程步骤为json格式。
    3. 允许客户输入json流程后读取流程

使用说明：
    运行程序后，根据需求选择流程，允许保存流程，流程运行暂未实现

"""

import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
import hashlib
from screen_photo import ImageCropper
from process import Process

if __name__ == "__main__":
    root = tk.Tk()
    root.title("图片裁剪工具")
    root.geometry("1400x700")  # 设置窗口初始大小

    # 创建一个可调整大小的 PanedWindow
    paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)

    # 左侧容器
    left_container = tk.Frame(paned_window)
    app_a = Process(left_container)  # 添加 `Process` 界面

    # 右侧容器
    right_container = tk.Frame(paned_window)
    image_cropper = ImageCropper(right_container, root)  # 添加 `ImageCropper` 界面

    # 添加两个容器到 `PanedWindow`
    paned_window.add(left_container, minsize=300, width=650)  # 允许最小宽度
    paned_window.add(right_container, minsize=300)  # 允许最小宽度

    root.mainloop()

