# -*- coding:utf-8 -*-
# @Author: scofield
# @Time: 2025/1/28 22:21
# @File: Process.py

"""
功能描述：
    1. 程序实现用户输入流程以及选择流程种允许项。
    2. 程序允许添加、删除流程步骤，允许保存流程步骤为json格式。
    3. 允许客户输入json流程后读取流程

使用说明：
    运行程序后，根据需求选择流程，允许保存流程，流程运行暂未实现

"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

class Process:
    def __init__(self, master):
        # 使用 Frame 作为主容器
        self.frame = tk.Frame(master, bg='#f0f0f0')
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 按钮框架
        self.buttons_frame = ttk.Frame(self.frame)
        self.buttons_frame.pack(pady=10, padx=10, fill='x')

        button_config = {
            '添加': self.add_step,
            '运行': self.run_steps,
            '全部删除': self.delete_all_steps,
            '保存流程': self.save_steps,
            '读取流程': self.load_steps
        }

        for text, command in button_config.items():
            btn = ttk.Button(self.buttons_frame, text=text, command=command)
            btn.pack(side='left', padx=5)
        # todo 照片地址
        self.image_dir = r"D:\PycharmProjects\auto_input\crops\9583e152d327"

        # 步骤容器
        self.steps_container = ttk.Frame(self.frame)
        self.steps_container.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        self.canvas = tk.Canvas(self.steps_container, bg='#f0f0f0')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.steps_container, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.steps_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")

        self.steps = []


    def add_step(self):
        step_label = ttk.Label(self.steps_frame, text=f"步骤 {len(self.steps) + 1}:")
        step_label.grid(row=len(self.steps), column=0, padx=5, pady=5, sticky="w")

        step_combobox = ttk.Combobox(self.steps_frame,
                                     values=["find_and_click", "input_text", "move_and_click"],
                                     state="readonly",
                                     width=15
                                     )
        step_combobox.grid(row=len(self.steps), column=1, padx=5, pady=5)
        step_combobox.current(0)
        step_combobox.bind('<<ComboboxSelected>>', lambda e, index=len(self.steps): self.update_step_params(index))

        params_frame = ttk.Frame(self.steps_frame, width=200)
        params_frame.grid(row=len(self.steps), column=2, padx=5, pady=5, sticky="w")

        delete_button = ttk.Button(self.steps_frame, text="删除", command=lambda index=len(self.steps): self.delete_step(index))
        delete_button.grid(row=len(self.steps), column=3, padx=5, pady=5)

        self.steps.append({
            'label': step_label,
            'combobox': step_combobox,
            'params_frame': params_frame,
            'delete_button': delete_button,
            'params': {}
        })

        self.update_step_params(len(self.steps) - 1)

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def update_step_params(self, index):
        # 清除之前的参数输入区和控件引用
        for widget in self.steps[index]['params_frame'].winfo_children():
            widget.destroy()
        self.steps[index]['params_widgets'] = {}  # 重置参数控件引用

        action = self.steps[index]['combobox'].get()

        image_files = [f for f in os.listdir(self.image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))] \
            if os.path.exists(self.image_dir) else []

        # 创建参数控件并记录到params_widgets
        if action == 'find_and_click':
            # 图片路径
            combo_image = ttk.Combobox(self.steps[index]['params_frame'], values=image_files, width=28)
            combo_image.grid(row=0, column=1, columnspan=5, sticky="we")
            self.steps[index]['params_widgets']['image_path'] = combo_image

            # X/Y偏移
            entry_dx = ttk.Entry(self.steps[index]['params_frame'], width=5)
            entry_dx.insert(0, '0')
            entry_dx.grid(row=1, column=1, sticky="w")
            self.steps[index]['params_widgets']['d_x'] = entry_dx

            entry_dy = ttk.Entry(self.steps[index]['params_frame'], width=5)
            entry_dy.insert(0, '0')
            entry_dy.grid(row=1, column=3, sticky="w")
            self.steps[index]['params_widgets']['d_y'] = entry_dy

            # 点击次数
            entry_clicks_1 = ttk.Entry(self.steps[index]['params_frame'], width=5)
            entry_clicks_1.insert(0, '1')
            entry_clicks_1.grid(row=1, column=5)
            self.steps[index]['params_widgets']['click_times'] = entry_clicks_1

            # 添加标签
            ttk.Label(self.steps[index]['params_frame'], text="图片路径:").grid(row=0, column=0, sticky="w")
            ttk.Label(self.steps[index]['params_frame'], text="X偏移:").grid(row=1, column=0, sticky="w")
            ttk.Label(self.steps[index]['params_frame'], text="Y偏移:").grid(row=1, column=2, sticky="w")
            ttk.Label(self.steps[index]['params_frame'], text="点击次数:").grid(row=1, column=4, sticky="w")

        elif action == 'input_text':
            entry_text = ttk.Entry(self.steps[index]['params_frame'], width=30)
            entry_text.grid(row=0, column=1)
            self.steps[index]['params_widgets']['text'] = entry_text
            ttk.Label(self.steps[index]['params_frame'], text="输入文本:").grid(row=0, column=0, sticky="w")

        elif action == 'move_and_click':
            # 坐标参数
            entry_x = ttk.Entry(self.steps[index]['params_frame'], width=5)
            entry_x.insert(0, '0')
            entry_x.grid(row=0, column=1)
            self.steps[index]['params_widgets']['X'] = entry_x

            entry_y = ttk.Entry(self.steps[index]['params_frame'], width=5)
            entry_y.insert(0, '0')
            entry_y.grid(row=0, column=3)
            self.steps[index]['params_widgets']['Y'] = entry_y

            # 滚动参数
            entry_scroll_times = ttk.Entry(self.steps[index]['params_frame'], width=5)
            entry_scroll_times.insert(0, '0')
            entry_scroll_times.grid(row=1, column=1)
            self.steps[index]['params_widgets']['scroll_times'] = entry_scroll_times

            entry_scroll_dist = ttk.Entry(self.steps[index]['params_frame'], width=5)
            entry_scroll_dist.insert(0, '0')
            entry_scroll_dist.grid(row=1, column=3)
            self.steps[index]['params_widgets']['scroll_distance'] = entry_scroll_dist

            # 点击次数
            entry_clicks_2 = ttk.Entry(self.steps[index]['params_frame'], width=3)
            entry_clicks_2.insert(0, '1')
            entry_clicks_2.grid(row=1, column=5)
            self.steps[index]['params_widgets']['click_times'] = entry_clicks_2

            # 添加标签
            ttk.Label(self.steps[index]['params_frame'], text="X移动:").grid(row=0, column=0, sticky="w")
            ttk.Label(self.steps[index]['params_frame'], text="Y移动:").grid(row=0, column=2, sticky="w")
            ttk.Label(self.steps[index]['params_frame'], text="滚动次数:").grid(row=1, column=0, sticky="w")
            ttk.Label(self.steps[index]['params_frame'], text="滚动距离:").grid(row=1, column=2, sticky="w")
            ttk.Label(self.steps[index]['params_frame'], text="点击次数:").grid(row=1, column=4, sticky="w")


        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def save_steps(self):
        steps_data = {"steps": []}
        for step in self.steps:
            action = step['combobox'].get()
            params = {}

            for param_key, widget in step['params_widgets'].items():
                value = widget.get()

                # 类型转换
                if param_key in ['d_x', 'd_y', 'X', 'Y', 'click_times', 'scroll_times', 'scroll_distance']:
                    try:
                        value = int(value) if value else 0
                    except ValueError:
                        value = 0

                params[param_key] = value

            steps_data['steps'].append({
                "action": action,
                "params": params
            })

        # 保存文件
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")]
        )

        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(steps_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", "流程已保存！")

    def load_steps(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON 文件", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                steps_data = json.load(f)

            # 清除现有步骤
            self.delete_all_steps()

            # 添加新步骤
            for step_data in steps_data['steps']:
                self.add_step()
                current_step = self.steps[-1]
                action = step_data['action']
                current_step['combobox'].set(action)

                # 强制更新参数界面
                self.update_step_params(len(self.steps) - 1)

                # 填充参数值
                for param_key, param_value in step_data['params'].items():
                    if param_key in current_step['params_widgets']:
                        widget = current_step['params_widgets'][param_key]

                        # 清除现有内容
                        if isinstance(widget, ttk.Combobox):
                            widget.set('')
                        elif isinstance(widget, ttk.Entry):
                            widget.delete(0, tk.END)

                        # 插入新值
                        value = str(param_value)
                        if isinstance(widget, ttk.Combobox):
                            widget.set(value)
                        else:
                            widget.insert(0, value)

            messagebox.showinfo("成功", "流程已加载！")

        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")

    def delete_step(self, index):
        self.steps[index]['label'].destroy()
        self.steps[index]['combobox'].destroy()
        self.steps[index]['params_frame'].destroy()
        self.steps[index]['delete_button'].destroy()
        del self.steps[index]

        # 重新调整剩余步骤的标签和索引
        for i in range(index, len(self.steps)):
            self.steps[i]['label'].config(text=f"步骤 {i + 1}:")
            self.steps[i]['delete_button'].config(command=lambda i = i: self.delete_step(i))

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def delete_all_steps(self):
        for step in self.steps:
            step['label'].destroy()
            step['combobox'].destroy()
            step['params_frame'].destroy()
            step['delete_button'].destroy()
        self.steps.clear()

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def run_steps(self):
        for step in self.steps:
            print(f"步骤: {step['combobox'].get()}")
            for child in step['params_frame'].winfo_children():
                if isinstance(child, ttk.Entry):
                    key = child.master.grid_slaves(column=0)[0]['text'].replace(':', '')
                    print(f"{key}: {child.get()}")

if __name__ == "__main__":
    root = tk.Tk()
    app = Process(root)
    root.geometry("1000x600")
    root.mainloop()

