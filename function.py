# -*- coding:utf-8 -*-
# @Author: Scofield
# @Time: 2025/1/28 22:21
# @File: function.py

"""
文件描述：
    程序所需的三个主要动作函数
    1.input_text:输入文字
    2.find_and_click：识别图像并且点击
"""


import pyautogui
import pyperclip
import time
import keyboard

# 操作函数
def input_text(text, interval=0):
    while True:
        try:
            pyperclip.copy(text)
            keyboard.press('ctrl')
            keyboard.press('v')
            keyboard.release('v')
            keyboard.release('ctrl')
            print("粘贴内容", pyperclip.paste())
            time.sleep(interval)
            return True
        except Exception as e:
            print(f"Exception occurred: {e}")
            time.sleep(interval)

def find_and_click(image_path, d_x=0, d_y=0, interval=0, click_times=0):
    while True:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.9)
            if location:
                center = pyautogui.center(location)
                click_position = (center.x + d_x, center.y + d_y)
                for _ in range(click_times):
                    pyautogui.click(click_position)
                time.sleep(interval)
                print(f"图像识别: 横轴平移{d_x}, 纵轴平移{d_y}, 成功点击 {image_path} ,点击{click_times}次")
                return True
            else:
                print(f"未找到目标 {image_path}，重试中...")
        except Exception as e:
            print(f"未找到目标 {image_path}，重试中...")
            time.sleep(interval)

def move_and_click(X, Y, scroll_times=0, scroll_distance=0, click_times=0):
    try:
        x, y = pyautogui.position()
        pyautogui.moveTo(x-X, y - Y, duration=0.1)
        for _ in range(scroll_times):
            pyautogui.scroll(scroll_distance)

        for _ in range(click_times):
            pyautogui.click()
        print(f"鼠标移动: 横轴平移{X}, 纵轴平移{Y}, 滚动次数{scroll_times}, 滚动距离{scroll_distance},点击{click_times}次")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
# move_and_click(X=-150, Y= 0,click_time=1)