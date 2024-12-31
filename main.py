import json
import os
from function import *


# 识别照片生成config
def generate_config_from_photos(folder_path):
    """
    根据指定文件夹下的照片生成配置字典。
    :param folder_path: 照片所在的文件夹路径
    :return: 生成的配置字典
    """
    config = {}
    # 遍历文件夹
    for file_name in os.listdir(folder_path):
        # 检查文件是否为照片（这里假设照片的扩展名为.jpg）
        if file_name.endswith(".jpg"):
            # 获取照片的编号（假设照片名称为数字.jpg）
            photo_number = file_name.split('.')[0]
            # 构建配置字典
            config[photo_number] = os.path.join(folder_path, file_name)

    return config


# 从 JSON 文件加载流程
def load_process_from_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


# 动态执行 JSON 流程
def execute_process(json_data, config, **kwargs):
    for step in json_data["steps"]:
        action = step["action"]
        params = step["params"]

        # 动态调用对应函数
        if action == "find_and_click":
            find_and_click(config[params["key"]], d_x=params.get("d_x", 0), d_y=params.get("d_y", 0), interval=params.get("interval", 0.5))
        elif action == "input_text":
            text = params["text"]
            if text in kwargs:  # 支持动态变量
                text = kwargs[text]
            input_text(text, interval=params.get("interval", 0.5))
        elif action == "move":
            move(X=params["X"], Y=params["Y"], scroll_times=params["scroll_times"], scroll_distance=params["scroll_distance"])

        else:
            print(f"未知操作: {action}")

# def main(json_file, config ,options):
def main(json_file=None):
    # 后续生成json保存并命名、传递进来
    json_file = "annex/test.json"

    # 识别文件夹下面的照片，然后根据名称编号
    # 示例配置
    # config = {
    #     "1": "annex/click_photo/1.jpg",
    #     "2": "annex/click_photo/2.jpg"
    # }

    # 使用示例
    folder_path = 'annex/click_photo'  # 请替换为你的实际文件夹路径
    config = generate_config_from_photos(folder_path)

    # 示例选项
    options = {
        "option_1": "测试文本1",
        "option_2": "测试文本2",
        "option_3": "测试文本3"
    }

    # 加载 JSON 流程并执行
    process_json = load_process_from_json(json_file)
    execute_process(process_json, config, **options)

if __name__ == "__main__":
    main()