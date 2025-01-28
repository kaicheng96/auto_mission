# -*- coding:utf-8 -*-
# @Author: Scofield
# @Time: 2025/1/28 22:21
# @File: screen_photo.py

"""
功能描述：
    1. 程序实现用户输入一张照片后框选区域进行截图。
    2. 程序自动识别不同照片的哈希值，并把截图保持在以哈希值命名的文件夹下。
    3. 添加了可查看截图模块和删除截图模块。
    4. 预览模块默认读取最后一张截图，删除选中图默认选取上一张图，删到第一张图后开始往后删除。

使用说明：
    运行程序后，根据提示输入照片后便可截图。

程序返回：
    可根据本程序生成的哈希值获取截图位置
"""

import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import os
import hashlib


class ImageCropper:
    def __init__(self, root):
        self.root = root
        self.root.title("图片裁剪工具")

        # 保存原始窗口大小
        self.full_width = 1000
        self.full_height = 600
        self.compact_width = 300  # 收起时的宽度

        # 设置初始窗口大小
        self.root.geometry(f"{self.full_width}x{self.full_height}")

        # 初始化变量
        self.image = None
        self.photo = None
        self.canvas = None
        self.preview_label = None
        self.preview_image = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.current_folder = None
        self.original_image_path = None
        self.right_frame_visible = True  # 添加一个变量来跟踪right_frame的可见状态

        # 设置预览框的大小
        self.preview_width = 200
        self.preview_height = 200

        # 创建主存储目录
        self.base_dir = "crops"
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        # 创建界面
        self.create_widgets()

    def toggle_right_frame(self):
        """显示或隐藏右侧框架并调整窗口大小"""
        if self.right_frame_visible:
            self.right_frame.pack_forget()
            self.toggle_button.config(text="显示图片")
            self.root.geometry(f"{self.compact_width}x{self.full_height}")
        else:
            self.right_frame.pack(side="right", expand=True, fill="both")
            self.toggle_button.config(text="隐藏图片")
            self.root.geometry(f"{self.full_width}x{self.full_height}")
        self.right_frame_visible = not self.right_frame_visible

    def get_image_hash(self, image_path):
        """生成图片文件的hash值作为文件夹名"""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:12]

    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")]
        )

        if file_path:
            # 保存原始图片路径
            self.original_image_path = file_path

            # 创建该图片的专属文件夹
            folder_name = self.get_image_hash(file_path)
            self.current_folder = os.path.join(self.base_dir, folder_name)
            if not os.path.exists(self.current_folder):
                os.makedirs(self.current_folder)

            # 加载图片
            self.image = Image.open(file_path)

            # 显示图片尺寸信息
            self.size_label.config(text=f"原始尺寸: {self.image.width} x {self.image.height}像素")

            # 显示图片
            self.show_image()

            # 更新历史记录
            self.update_history_list()

            # 自动选中最后一张截图
            if self.history_listbox.size() > 0:
                last_index = self.history_listbox.size() - 1
                self.history_listbox.selection_clear(0, tk.END)
                self.history_listbox.selection_set(last_index)
                self.history_listbox.see(last_index)  # 确保最后一项可见

                # 显示最后一张照片的预览
                last_filename = self.history_listbox.get(last_index)
                last_file_path = os.path.join(self.current_folder, last_filename)
                self.show_preview(last_file_path)
                self.delete_button.config(state="normal")
                self.info_label.config(text=f"当前图片: {os.path.basename(file_path)}, 选中截图: {last_filename}")
            else:
                self.preview_label.config(image='', text="目录为空，没有文件可以预览", bg='#f0f0f0')
                self.delete_button.config(state="disabled")
                self.info_label.config(text=f"当前图片: {os.path.basename(file_path)}")

    def on_canvas_configure(self, event):
        """当画布大小改变时，更新滚动条"""
        if self.image:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        """鼠标滚轮事件处理"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_canvas_scroll(self, *args):
        """画布滚动事件处理"""
        if self.image:
            self.canvas.yview(*args)

    def get_canvas_coordinates(self, event):
        """获取画布上的实际坐标"""
        # 获取画布的当前滚动位置
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        return x, y

    def show_image(self):
        # 清除画布上的所有内容
        self.canvas.delete("all")
        self.photo = ImageTk.PhotoImage(self.image)

        # 创建滚动区域大小与图片大小一致
        self.canvas.config(scrollregion=(0, 0, self.image.width, self.image.height))
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        # 更新坐标显示
        self.coord_label.config(text="坐标: (0, 0)")

    def on_press(self, event):
        x, y = self.get_canvas_coordinates(event)
        self.start_x = x
        self.start_y = y

        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

        # 更新坐标显示
        self.coord_label.config(text=f"起始坐标: ({int(x)}, {int(y)})")

    def on_drag(self, event):
        if self.rect:
            x, y = self.get_canvas_coordinates(event)
            self.canvas.coords(
                self.rect,
                self.start_x, self.start_y,
                x, y
            )
            # 更新尺寸显示
            width = abs(x - self.start_x)
            height = abs(y - self.start_y)
            self.selection_size_label.config(text=f"选区尺寸: {int(width)} x {int(height)}像素")
            # 更新坐标显示
            self.coord_label.config(text=f"当前坐标: ({int(x)}, {int(y)})")

    def on_release(self, event):
        if self.rect and self.image and self.current_folder:
            x, y = self.get_canvas_coordinates(event)
            x1, y1 = self.start_x, self.start_y
            x2, y2 = x, y

            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            if x1 != x2 and y1 != y2:
                cropped = self.image.crop((int(x1), int(y1), int(x2), int(y2)))

                # 转换为 RGB 模式以支持 JPEG
                if cropped.mode == 'RGBA':
                    cropped = cropped.convert('RGB')

                # 保存截图
                next_number = self.get_next_number()
                save_path = os.path.join(self.current_folder, f"{next_number}.jpg")
                cropped.save(save_path)
                self.update_history_list()
                self.info_label.config(text=f"已保存截图 {next_number}.jpg ({int(x2 - x1)}x{int(y2 - y1)}像素)")
                self.show_preview(save_path)

    def create_widgets(self):
        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # 左侧框架（用于预览和历史记录）
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", padx=10)

        # 右侧框架（用于主图片）
        self.right_frame = tk.Frame(main_frame)  # 将right_frame设为实例变量
        self.right_frame.pack(side="right", expand=True, fill="both")

        # 创建按钮框架
        button_frame = tk.Frame(left_frame)
        button_frame.pack(pady=5)

        self.select_button = tk.Button(button_frame, text="选择图片", command=self.select_image)
        self.select_button.pack(side="left", padx=2)

        # 添加显示/隐藏按钮
        self.toggle_button = tk.Button(button_frame, text="隐藏图片", command=self.toggle_right_frame)
        self.toggle_button.pack(side="left", padx=2)

        # 创建按钮和信息显示区
        control_frame = tk.Frame(self.right_frame)
        control_frame.pack(fill="x", pady=5)

        # 添加尺寸信息标签
        self.size_label = tk.Label(control_frame, text="原始尺寸: -")
        self.size_label.pack(side="left", padx=5)

        self.coord_label = tk.Label(control_frame, text="坐标: (-,-)")
        self.coord_label.pack(side="left", padx=5)

        self.selection_size_label = tk.Label(control_frame, text="选区尺寸: -")
        self.selection_size_label.pack(side="left", padx=5)

        # 创建带滚动条的画布框架
        canvas_frame = tk.Frame(self.right_frame)
        canvas_frame.pack(expand=True, fill="both")

        # 创建画布和滚动条
        self.canvas = tk.Canvas(canvas_frame, cursor="cross")
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.on_canvas_scroll)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)

        # 配置画布的滚动
        self.canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # 放置画布和滚动条
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", expand=True, fill="both")

        # 显示信息标签
        self.info_label = tk.Label(self.right_frame, text="请选择要处理的图片")
        self.info_label.pack(pady=5)

        # 创建历史记录列表框
        history_label = tk.Label(left_frame, text="历史截图:")
        history_label.pack(pady=(0, 5))

        self.history_listbox = tk.Listbox(left_frame, width=30, height=15)
        self.history_listbox.pack(fill="both", expand=True)

        # 创建预览框架
        preview_frame = tk.Frame(left_frame, width=self.preview_width, height=self.preview_height)
        preview_frame.pack_propagate(False)
        preview_frame.pack(pady=10)

        # 创建预览标签
        self.preview_label = tk.Label(preview_frame, text="暂无截图", bg='#f0f0f0')
        self.preview_label.pack(expand=True, fill="both")

        # 创建删除按钮
        self.delete_button = tk.Button(left_frame, text="删除选中截图", command=self.delete_selected)
        self.delete_button.pack(pady=5)
        self.delete_button.config(state="disabled")

        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_select_history)


    def update_history_list(self):
        """更新历史记录列表"""
        self.history_listbox.delete(0, tk.END)
        if self.current_folder and os.path.exists(self.current_folder):
            files = [f for f in os.listdir(self.current_folder) if f.endswith('.jpg')]
            files.sort(key=lambda x: int(x.split('.')[0]))
            for file in files:
                self.history_listbox.insert(tk.END, file)

    def get_next_number(self):
        """获取下一个可用的编号"""
        if not os.path.exists(self.current_folder):
            return 1
        files = [f for f in os.listdir(self.current_folder) if f.endswith('.jpg')]
        if not files:
            return 1
        numbers = [int(f.split('.')[0]) for f in files if f.split('.')[0].isdigit()]
        return max(numbers) + 1 if numbers else 1

    # def delete_selected(self):
    #     """删除选中的历史截图"""
    #     selection = self.history_listbox.curselection()
    #     if selection:
    #         filename = self.history_listbox.get(selection[0])
    #         file_path = os.path.join(self.current_folder, filename)
    #         if os.path.exists(file_path):
    #             os.remove(file_path)
    #             self.update_history_list()
    #             self.preview_label.config(image='', text="暂无截图", bg='#f0f0f0')
    #             self.info_label.config(text=f"已删除: {filename}")

    def delete_selected(self):
        """删除选中的历史截图并自动选中上一张照片"""
        selection = self.history_listbox.curselection()
        if selection:
            current_index = selection[0]
            filename = self.history_listbox.get(current_index)
            file_path = os.path.join(self.current_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.update_history_list()

                # 获取更新后的文件列表
                files = [f for f in os.listdir(self.current_folder) if f.endswith('.jpg')]
                if files:
                    # 如果还有其他照片，计算上一张照片的索引
                    previous_index = max(0, current_index - 1)  # 确保索引不小于 0
                    self.history_listbox.selection_clear(0, tk.END)
                    self.history_listbox.selection_set(previous_index)
                    self.history_listbox.see(previous_index)  # 确保选中的项可见

                    # 显示上一张照片的预览
                    previous_filename = self.history_listbox.get(previous_index)
                    previous_file_path = os.path.join(self.current_folder, previous_filename)
                    self.show_preview(previous_file_path)
                    self.delete_button.config(state="normal")
                    self.info_label.config(text=f"已删除: {filename}，当前选中: {previous_filename}")
                else:
                    # 如果没有照片了，清空预览
                    self.preview_label.config(image='', text="暂无截图", bg='#f0f0f0')
                    self.delete_button.config(state="disabled")
                    self.info_label.config(text=f"已删除: {filename}，无上一张图")


    def on_select_history(self, event):
        """当选择历史记录中的项目时"""
        selection = self.history_listbox.curselection()
        if selection:
            filename = self.history_listbox.get(selection[0])
            file_path = os.path.join(self.current_folder, filename)
            self.show_preview(file_path)
            self.delete_button.config(state="normal")
        else:
            self.delete_button.config(state="disabled")

    def show_preview(self, image_path):
        """显示预览图片"""
        if os.path.exists(image_path):
            preview_image = Image.open(image_path)
            preview_image = self.fit_image_to_preview(preview_image)
            self.preview_image = ImageTk.PhotoImage(preview_image)
            self.preview_label.config(image=self.preview_image, bg='white')

    def fit_image_to_preview(self, image):
        """调整图片大小以适应预览框"""
        w, h = image.size
        aspect_ratio = w / h

        if aspect_ratio > 1:
            new_width = self.preview_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = self.preview_height
            new_width = int(new_height * aspect_ratio)

        if new_height > self.preview_height:
            new_height = self.preview_height
            new_width = int(new_height * aspect_ratio)
        if new_width > self.preview_width:
            new_width = self.preview_width
            new_height = int(new_width / aspect_ratio)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x600")
    app = ImageCropper(root)
    root.mainloop()