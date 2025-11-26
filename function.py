import hashlib
import os
import shutil
import tempfile
import time

import keyboard
import pyautogui
import pyperclip

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

_image_cache = {}


def _get_ascii_safe_path(image_path: str) -> str:
    """
    OpenCV 在 Windows 下无法读取包含非 ASCII 字符的路径。
    当检测到路径包含中文等字符时，将图片复制到临时目录的 ASCII 路径后返回。
    """
    if not image_path:
        return image_path

    abs_path = os.path.abspath(image_path)

    if abs_path.isascii():
        return abs_path

    global _image_cache
    try:
        src_mtime = os.path.getmtime(abs_path)
    except OSError:
        return abs_path
    cached = _image_cache.get(abs_path)
    if cached:
        cached_path, cached_mtime = cached
        if os.path.exists(cached_path) and cached_mtime == src_mtime:
            return cached_path

    temp_dir = os.path.join(tempfile.gettempdir(), "auto_input_images")
    os.makedirs(temp_dir, exist_ok=True)
    suffix = os.path.splitext(abs_path)[1]
    hashed_name = hashlib.md5(abs_path.encode("utf-8")).hexdigest()
    temp_path = os.path.join(temp_dir, f"{hashed_name}{suffix}")

    shutil.copy2(abs_path, temp_path)
    _image_cache[abs_path] = (temp_path, src_mtime)
    return temp_path

# 操作函数
def input_text(text, max_retry: int = 3):
    """将文本写入剪贴板后粘贴，失败时自动重试并降级为逐字输入。"""
    normalized = text if isinstance(text, str) else str(text)

    for attempt in range(1, max_retry + 1):
        try:
            pyperclip.copy(normalized)
            time.sleep(0.05)  # 等待剪贴板可用
            if pyperclip.paste() != normalized:
                raise ValueError("剪贴板内容与目标不一致")

            keyboard.press_and_release('ctrl+v')
            time.sleep(0.2)
            print(f"粘贴成功（第 {attempt} 次尝试）: {normalized}")
            return True
        except Exception as exc:
            print(f"粘贴失败（第 {attempt} 次尝试）: {exc}")
            time.sleep(0.3)

    # 降级方案：逐字符输入，避免流程完全中断
    print("多次粘贴失败，切换为逐字符输入模式")
    pyautogui.typewrite(normalized, interval=0.02)
    time.sleep(0.2)
    return True

def find_and_click(image_path, d_x=0, d_y=0, click_times=0):
    while True:
        safe_path = image_path
        try:
            safe_path = _get_ascii_safe_path(image_path)
            location = pyautogui.locateOnScreen(safe_path, confidence=0.9)
            if location:
                center = pyautogui.center(location)
                click_position = (center.x + d_x, center.y + d_y)
                for _ in range(click_times):
                    pyautogui.click(click_position)
                time.sleep(1)
                print(f"图像识别: 横轴平移{d_x}, 纵轴平移{d_y}, 成功点击 {safe_path} ,点击{click_times}次")
                return True
            else:
                print(f"未找到目标 {safe_path}，重试中...")
        except Exception as e:
            print(f"未找到目标 {safe_path}，重试中...")
            time.sleep(1)

def move_and_click(X, Y, scroll_times=0, scroll_distance=0, click_times=0):
    try:
        x, y = pyautogui.position()
        pyautogui.moveTo(x-X, y - Y, duration=0.2)
        for _ in range(scroll_times):
            pyautogui.scroll(scroll_distance)

        for _ in range(click_times):
            pyautogui.click()
        print(f"鼠标移动: 横轴平移{X}, 纵轴平移{Y}, 滚动次数{scroll_times}, 滚动距离{scroll_distance},点击{click_times}次")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
# move_and_click(X=-150, Y= 0,click_time=1)


def wait(seconds: float = 1.0):
    """简单的等待函数，支持浮点秒数。"""
    try:
        duration = max(float(seconds), 0.0)
    except (TypeError, ValueError):
        duration = 0.0

    print(f"等待 {duration} 秒...")
    time.sleep(duration)

def read_excel_first_column(file_path: str):
    """
    读取 Excel 文件第一列的非空内容，保持原有顺序。
    """
    if load_workbook is None:
        raise RuntimeError("缺少 openpyxl 依赖，请先安装 openpyxl")

    if not file_path:
        raise ValueError("Excel 文件路径为空")

    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Excel 文件不存在: {abs_path}")

    workbook = load_workbook(abs_path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        values = []
        for row in sheet.iter_rows(min_row=1, max_col=1, values_only=True):
            cell_value = row[0]
            if cell_value is None:
                continue
            text = str(cell_value).strip()
            if text:
                values.append(text)
    finally:
        workbook.close()

    if not values:
        raise ValueError(f"Excel 文件第一列没有可用数据: {abs_path}")
    return values

def if_image_condition_check(image_path_1, image_path_2):
    """
    检查屏幕上是否存在指定的两个图片之一，并返回相应的分支。

    Args:
        image_path_1: 第一个要检查的图片路径。
        image_path_2: 第二个要检查的图片路径。

    Returns:
        str:  如果识别到 image_path_1，返回 "image1_output"。
              如果识别到 image_path_2，返回 "image2_output"。
              如果两个图片都未找到，返回 "not_found_output"。
    """
    safe_image_1 = _get_ascii_safe_path(image_path_1)
    safe_image_2 = _get_ascii_safe_path(image_path_2)

    print(f"IF 条件检查函数执行: 检查 图片1: {safe_image_1}, 图片2: {safe_image_2}") # 调试信息

    location_1 = pyautogui.locateOnScreen(safe_image_1, confidence=0.9) # 识别 图片1
    if location_1:
        print(f"IF 条件检查函数: 识别到 图片1: {safe_image_1}") # 调试信息
        return "image1_output" # 返回 "image1_output" 分支

    location_2 = pyautogui.locateOnScreen(safe_image_2, confidence=0.9) # 识别 图片2
    if location_2:
        print(f"IF 条件检查函数: 识别到 图片2: {safe_image_2}") # 调试信息
        return "image2_output" # 返回 "image2_output" 分支

    print(f"IF 条件检查函数: 未找到 图片1: {safe_image_1} 和 图片2: {safe_image_2}") # 调试信息
    return "not_found_output" # 如果两个图片都未找到，返回 "not_found_output" 分支
