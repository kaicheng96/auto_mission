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

def find_and_click(image_path, d_x=0, d_y=0, interval=0):
    while True:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.9)
            if location:
                center = pyautogui.center(location)
                click_position = (center.x + d_x, center.y + d_y)
                pyautogui.click(click_position)
                print(f"成功点击 {image_path}")
                time.sleep(interval)
                return True
            else:
                print(f"未找到目标 {image_path}，重试中...")
        except Exception as e:
            print(f"未找到目标 {image_path}，重试中...")
            time.sleep(interval)

def move(X, Y, scroll_times, scroll_distance):
    try:
        x, y = pyautogui.position()
        pyautogui.moveTo(x-X, y - Y, duration=0.1)
        for _ in range(scroll_times):
            pyautogui.scroll(scroll_distance)
        print(f"鼠标移动: 横轴平移{X}, 纵轴平移{Y}, 滚动次数{scroll_times}, 滚动距离{scroll_distance}")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")