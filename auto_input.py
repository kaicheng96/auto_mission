import pyautogui
import pyperclip
import time
import keyboard

# 找到点击输入
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

# 找到然后点击
def find_and_click(image_path, d_x=0, d_y=0, interval=0):
    while True:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.9)
            if location:
                center = pyautogui.center(location)
                click_position = (center.x + d_x, center.y + d_y)
                pyautogui.click(click_position)  # 点击目标区域
                print(f"成功点击 {image_path}")
                time.sleep(interval)
                return True
            else:
                pass
        except Exception as e:
            time.sleep(interval)

# 拉动滚轮
def scroll(move_down_distance, scroll_times, scroll_distance):
    try:
        x, y = pyautogui.position()
        pyautogui.moveTo(x, y - move_down_distance, duration=0.1)

        # 滚动鼠标滚轮
        for _ in range(scroll_times):
            pyautogui.scroll(scroll_distance)
            # time.sleep(0.5)  # 等待滚轮动作完成
    except Exception as e:
        print(f"执行过程中发生错误: {e}")


def process(option_1, option_2, option_3, config, type):
    # 1
    find_and_click(config['1'])
    input_text(text=option_1)
    # 2
    find_and_click(config['2'])
    find_and_click(config['3'])
    # 3
    find_and_click(config['4'])
    scroll(move_down_distance=-200, scroll_times=2, scroll_distance=-150)
    find_and_click(config['5'])
    # 4
    find_and_click(config['6'])
    find_and_click(option_2)
    # 5
    find_and_click(config['8'])
    find_and_click(config['9'])
    # 6
    find_and_click(config['10'])
    find_and_click(config['11'])
    # 7
    find_and_click(config['12'])
    input_text(text="47")
    find_and_click(config['13'])
    # 8
    find_and_click(config['14'])
    if type == "5G":
        scroll(move_down_distance=100, scroll_times=2, scroll_distance=-150)
    find_and_click(option_3)
    # 9
    find_and_click(config['16'])
    find_and_click(config['17'])
    # 10
    find_and_click(config['18'])
    input_text(text="华为维修服务中心")
    # 11
    find_and_click(config['19'])
    input_text(text="0755-28560555")
    # 12
    find_and_click(config['20'])
    input_text(text="广东省东莞市松山湖高雄路2号华为蓝思8号楼8号货台")
    # 13
    find_and_click(config['21'], d_x=100)
    from datetime import datetime, timedelta
    future_date = datetime.now() + timedelta(days=29)
    deal_time = future_date.strftime("%Y-%m-%d %H:%M")
    input_text(text=deal_time)



def run_type(type):
    if type == "5G_1":
        process(options["5G_1"], options["无线网5G"], options["gNodeB"], config, type)
    elif type == "FDD_1":
        process(options["FDD_1"], options["无线网FDD"], options["eNodeB"], config, type)
    elif type == "LTE_1":
        process(options["LTE_1"], options["无线网LTE"], options["eNodeB"], config, type)
    # elif type == "5G_2":
    #     process(options["5G_2"], options["无线网5G"], options["gNodeB"], config, type)
    # elif type == "FDD_2":
    #     process(options["FDD_2"], options["无线网FDD"], options["eNodeB"], config, type)
    # elif type == "LTE_2":
    #     process(options["LTE_2"], options["无线网LTE"], options["eNodeB"], config, type)


config = {
    "1": "click_photo/image1.jpg",
    "2": "click_photo/image2.jpg",
    "3": "click_photo/image3.jpg",
    "4": "click_photo/image4.jpg",
    "5": "click_photo/image5.jpg",
    "6": "click_photo/image6.jpg",
    # "7": "click_photo/5G.jpg",
    "8": "click_photo/image7.jpg",
    "9": "click_photo/image8.jpg",
    "10": "click_photo/image9.jpg",
    "11": "click_photo/image10.jpg",
    "12": "click_photo/image11.jpg",
    "13": "click_photo/image12.jpg",
    "14": "click_photo/image13.jpg",
    # "15": "click_photo/gNodeB.jpg",
    "16": "click_photo/image15.jpg",
    "17": "click_photo/image16.jpg",
    "18": "click_photo/text2.jpg",
    "19": "click_photo/text3.jpg",
    "20": "click_photo/text4.jpg",
    "21": "click_photo/time.jpg",
}
options = {
    "5G_1": "广东东莞无线基站华为5G正常送修",
    "FDD_1": "广东东莞无线基站华为FDD正常送修",
    "LTE_1": "广东东莞无线基站华为LTE正常送修",
    # "5G_2": "广东东莞无线基站华为5G坏件归还",
    # "FDD_2": "广东东莞无线基站华为FDD坏件归还",
    # "LTE_2": "广东东莞无线基站华为LTE坏件归还",
    "无线网5G": "click_photo/5G.jpg",
    "无线网FDD": "click_photo/FDD.jpg",
    "无线网LTE": "click_photo/LTE.jpg",
    "gNodeB": "click_photo/gNodeB.jpg",
    "eNodeB": "click_photo/eNodeB.jpg"
}

# if __name__ == "__main__":
#     run_type("5G")
