"""
简单的截图脚本：以当前鼠标所在位置为截图区域的左上角，截取 300x200 大小的图像。

运行步骤：
1. 执行脚本后有 2 秒缓冲时间，请将鼠标移动到目标区域左上角。
2. 到时间后脚本会自动截取图片，并保存在运行目录下的 screenshot_YYYYmmdd_HHMMSS.png。
"""

import argparse
from datetime import datetime
from pathlib import Path
import time

import pyautogui


def capture_mouse_region(width: int = 300, height: int = 200) -> Path:
    """以当前鼠标位置为左上角截取指定尺寸的屏幕区域。"""
    print("请在 2 秒内将鼠标移动到目标区域左上角…")
    time.sleep(2)

    x, y = pyautogui.position()
    print(f"捕获区域左上角：({x}, {y})，尺寸：{width}x{height}")

    screenshot = pyautogui.screenshot(region=(x, y, width, height))

    output_path = Path.cwd() / f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
    screenshot.save(output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="以鼠标当前位置为左上角截取指定尺寸的屏幕区域。"
    )
    parser.add_argument(
        "width",
        nargs="?",
        type=int,
        default=300,
        help="截取区域宽度（默认 300）",
    )
    parser.add_argument(
        "height",
        nargs="?",
        type=int,
        default=200,
        help="截取区域高度（默认 200）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        saved_path = capture_mouse_region(width=args.width, height=args.height)
        print(f"截图已保存：{saved_path}")
    except Exception as err:
        print(f"截图失败：{err}")

