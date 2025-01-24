# -*- coding:utf-8 -*-
# @Author: scofield
# @Time: 2025/1/24 11:21
# @File: app.py

"""
功能描述：
    1. 程序实现用户输入流程以及选择流程种允许项。
    2. 程序允许添加、删除流程步骤，允许保存流程步骤为json格式。
    3. 允许客户输入json流程后读取流程

使用说明：
    运行程序后，根据需求选择流程，允许保存流程，暂未实现运行

"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("流程步骤添加器")
        self.root.geometry('400x500+300+100')

        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=10)

        self.add_button = tk.Button(self.buttons_frame, text="添加", command=self.add_step)
        self.add_button.pack(side='left', padx=5)

        self.run_button = tk.Button(self.buttons_frame, text="运行", command=self.run_steps)
        self.run_button.pack(side='left', padx=5)

        self.save_button = tk.Button(self.buttons_frame, text="保存流程", command=self.save_steps)
        self.save_button.pack(side='left', padx=5)

        self.load_button = tk.Button(self.buttons_frame, text="读取流程", command=self.load_steps)
        self.load_button.pack(side='left', padx=5)

        self.delete_all_button = tk.Button(self.buttons_frame, text="全部删除", command=self.delete_all_steps)
        self.delete_all_button.pack(side='left', padx=5)

        self.steps_container = tk.Frame(self.root)
        self.steps_container.pack(fill=tk.BOTH, expand=True, pady=10)

        self.canvas = tk.Canvas(self.steps_container)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.steps_container, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.steps_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")

        self.steps = []

    def add_step(self):
        step_label = ttk.Label(self.steps_frame, text=f"步骤 {len(self.steps) + 1}:")
        step_label.grid(row=len(self.steps), column=0, padx=5, pady=5, sticky="w")

        step_combobox = ttk.Combobox(self.steps_frame, values=["单击", "滑动"], state="readonly")
        step_combobox.grid(row=len(self.steps), column=1, padx=5, pady=5)
        step_combobox.current(0)

        delete_button = tk.Button(self.steps_frame, text="删除", command=lambda index=len(self.steps): self.delete_step(index))
        delete_button.grid(row=len(self.steps), column=2, padx=5, pady=5)

        self.steps.append((step_combobox, delete_button, step_label))

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def delete_step(self, index):
        self.steps[index][0].destroy()
        self.steps[index][1].destroy()
        self.steps[index][2].destroy()
        del self.steps[index]

        for i in range(index, len(self.steps)):
            self.steps[i][0].grid(row=i, column=1, padx=5, pady=5)
            self.steps[i][1].grid(row=i, column=2, padx=5, pady=5)
            self.steps[i][1].config(command=lambda i=i: self.delete_step(i))
            self.steps[i][2].grid(row=i, column=0, padx=5, pady=5, sticky="w")
            self.steps[i][2].config(text=f"步骤 {i + 1}:")

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def delete_all_steps(self):
        for step in self.steps:
            step[0].destroy()
            step[1].destroy()
            step[2].destroy()
        self.steps.clear()

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def run_steps(self):
        for i, (combobox, _, _) in enumerate(self.steps):
            print(f'第{i + 1}步：', combobox.get())
            if combobox.get() == '单击':
                print('执行单击方法')
            elif combobox.get() == '滑动':
                print('执行滑动方法')

    def save_steps(self):
        if not self.steps:
            messagebox.showwarning("警告", "没有步骤可以保存！")
            return

        steps_data = [{"step": i + 1, "action": combobox.get()} for i, (combobox, _, _) in enumerate(self.steps)]
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON 文件", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(steps_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", "流程已保存！")

    def load_steps(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON 文件", "*.json")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    steps_data = json.load(f)

                self.delete_all_steps()

                for step in steps_data:
                    self.add_step()
                    self.steps[-1][0].set(step["action"])

                messagebox.showinfo("成功", "流程已加载！")
            except Exception as e:
                messagebox.showerror("错误", f"加载流程失败：{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
