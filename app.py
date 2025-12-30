# -*- coding:utf-8 -*-
# @Author: scofield
# @Time: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}  # 动态生成当前时间
# @File: app.py
# 添加ai \添加if else\n excel参数
"""
功能描述：
    1.总客户端

使用说明：
    运行程序后，根据需求选择流程，允许保存流程，并且允许截图框选点击的区域

"""

import tkinter as tk
from screen_photo import ImageCropper
from process import Process
from flow_manager import FlowManager

if __name__ == "__main__":
    root = tk.Tk()
    root.title("自动化流程工具")
    root.geometry("1400x900")  # 设置窗口初始大小

    flow_manager = FlowManager()

    # 创建一个可调整大小的 PanedWindow
    paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)

    # 左侧容器
    left_container = tk.Frame(paned_window)
    app_a = Process(left_container, flow_manager)  # 添加 `Process` 界面

    # 右侧容器
    right_container = tk.Frame(paned_window)
    image_cropper = ImageCropper(right_container, root, flow_manager)  # 添加 `ImageCropper` 界面

    # 添加两个容器到 `PanedWindow`
    paned_window.add(left_container, minsize=800, width=900)  # 允许最小宽度
    paned_window.add(right_container, minsize=250)  # 允许最小宽度

    root.mainloop()

