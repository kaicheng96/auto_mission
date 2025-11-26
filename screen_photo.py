# -*- coding:utf-8 -*-
# @Author: Scofield
# @Time: 2025/2/06 22:21
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
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
import cv2

class ImageCropper:
    def __init__(self, master, root, flow_manager):
        self.root = root
        self.flow_manager = flow_manager
        self.flow_manager.register_listener(self.handle_flow_event)
        self.frame = tk.Frame(master, bg='#d9d9d9')
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 移除窗口尺寸相关的属性
        self.right_frame_visible = True

        # 初始化其他变量
        self.image = None
        self.photo = None
        self.video_cap = None
        self.canvas = None
        self.preview_label = None
        self.preview_image = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.current_folder = None
        self.original_image_path = None

        self.video_playing = False  # 视频播放状态
        self.video_paused = False  # 视频暂停状态
        self.video_frame_count = 0  # 视频总帧数
        self.video_current_frame = 0  # 当前帧
        self.video_slider = None  # 视频进度条

        # 设置预览框的大小
        self.preview_width = 150
        self.preview_height = 150

        # 创建界面
        self.create_widgets()

    # def toggle_right_frame(self):
    #     """只显示或隐藏右侧图片显示区域，不改变窗口大小"""
    #     if self.right_frame_visible:
    #         # 隐藏右侧区域
    #         self.right_frame.pack_forget()
    #         self.toggle_button.config(text="显示图片")
    #     else:
    #         # 显示右侧区域
    #         self.right_frame.pack(side="right", expand=True, fill="both")
    #         self.toggle_button.config(text="隐藏图片")
    #     self.right_frame_visible = not self.right_frame_visible
    def toggle_right_frame(self):
        """只显示或隐藏右侧图片显示区域，同时调整窗口大小"""
        if self.right_frame_visible:
            # 记录当前窗口大小
            self.root.update_idletasks()
            self.original_width = self.root.winfo_width()

            # 隐藏右侧区域
            self.right_frame.pack_forget()
            self.toggle_button.config(text="显示图片")

            # 调整窗口宽度
            new_width = max(250, self.original_width - self.right_frame.winfo_width())  # 避免窗口过小
            self.root.geometry(f"{new_width}x{self.root.winfo_height()}")
        else:
            # 显示右侧区域
            self.right_frame.pack(side="right", expand=True, fill="both")
            self.toggle_button.config(text="隐藏图片")

            # 恢复窗口宽度
            self.root.geometry(f"{self.original_width}x{self.root.winfo_height()}")

        self.right_frame_visible = not self.right_frame_visible

    def select_media(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Media files", "*.jpg *.jpeg *.png *.bmp *.mp4 *.avi *.mov")]
        )

        if not file_path:
            return  # 用户取消选择

        if not self.flow_manager.has_flow():
            messagebox.showwarning("提示", "请先在左侧输入流程名称并点击“添加流程”。")
            return

        self.current_folder = self.flow_manager.get_screenshot_dir()
        if not self.current_folder:
            messagebox.showerror("错误", "无法获取流程截图目录。")
            return

        # 重置之前的状态
        self.image = None
        self.photo = None
        if self.video_cap:
            self.video_cap.release()
        self.video_cap = None
        self.canvas.delete("all")
        file_ext = file_path.lower().split('.')[-1]

        if file_ext in ('jpg', 'jpeg', 'png', 'bmp'):
            # 处理图片
            self.original_image_path = file_path
            self.image = Image.open(file_path)
            self.size_label.config(text=f"原始尺寸: {self.image.width} x {self.image.height}像素")
            self.show_media()


        elif file_ext in ('mp4', 'avi', 'mov'):

            # 处理视频
            self.original_video_path = file_path
            self.video_cap = cv2.VideoCapture(file_path)

            # 初始化视频参数
            self.video_fps = self.video_cap.get(cv2.CAP_PROP_FPS)
            self.video_frame_count = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_current_frame = 0
            self.video_playing = False
            self.video_paused = True

            success, frame = self.video_cap.read()

            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                # 获取视频原始分辨率
                video_width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                video_height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                # 调整 Canvas 适应视频大小
                self.canvas.config(width=video_width, height=video_height)

                # 使用统一的定位方式
                self.photo = ImageTk.PhotoImage(image)
                self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
                self.size_label.config(text=f"视频尺寸: {video_width} x {video_height} 像素")

                # 创建视频控制条
                self.create_video_controls()

        # 更新历史记录
        self.update_history_list()

        # 自动选中最后一项并预览
        if self.history_listbox.size() > 0:
            last_index = self.history_listbox.size() - 1
            self.history_listbox.selection_clear(0, tk.END)
            self.history_listbox.selection_set(last_index)
            self.history_listbox.see(last_index)

            last_filename = self.history_listbox.get(last_index)
            last_file_path = os.path.join(self.current_folder, last_filename)
            self.show_preview(last_file_path)

            self.delete_button.config(state="normal")
            self.info_label.config(text=f"当前文件: {os.path.basename(file_path)}, 选中文件: {last_filename}")
        else:
            self.preview_label.config(image='', text="目录为空，没有文件可以预览", bg='#f0f0f0')
            self.delete_button.config(state="disabled")
            self.info_label.config(text=f"当前文件: {os.path.basename(file_path)}")

    def play_video(self):
        """播放视频"""
        if self.video_playing and self.video_cap:
            if self.video_current_frame >= self.video_frame_count:
                # 如果到达视频末尾，重置到开始
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.video_current_frame = 0

            ret, frame = self.video_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                self.photo = ImageTk.PhotoImage(image)

                # 清除之前的图像
                self.canvas.delete("all")
                # 使用与初始加载相同的定位方式
                self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

                self.video_current_frame += 1
                self.video_slider.set(self.video_current_frame)

                # 使用 after 方法安排下一帧
                delay = int(1000 / self.video_fps)  # 将帧率转换为毫秒延迟
                self.root.after(delay, self.play_video)
            else:
                # 视频结束，重置状态
                self.video_playing = False
                self.video_paused = True
                self.play_button.config(text="播放")

    def create_video_controls(self):
        """创建视频控制条"""
        # 如果已存在控制框架，先移除
        if hasattr(self, 'control_frame'):
            self.control_frame.destroy()

        self.control_frame = tk.Frame(self.right_frame)
        self.control_frame.pack(fill="x", pady=5)

        # 播放/暂停按钮
        self.play_button = tk.Button(self.control_frame, text="播放", command=self.toggle_video_play)
        self.play_button.pack(side="left", padx=5)

        # 视频进度条
        self.video_slider = tk.Scale(self.control_frame, from_=0, to=self.video_frame_count,
                                     orient="horizontal", length=400)
        self.video_slider.pack(side="left", padx=5, fill="x", expand=True)
        self.video_slider.bind("<ButtonRelease-1>", self.on_slider_release)

    def toggle_video_play(self):
        """切换视频播放/暂停状态"""
        if not self.video_cap:
            return

        if self.video_playing:
            self.video_playing = False
            self.video_paused = True
            self.play_button.config(text="播放")
        else:
            self.video_playing = True
            self.video_paused = False
            self.play_button.config(text="暂停")
            self.play_video()

    def on_slider_release(self, event):
        """当用户拖动进度条时，跳转到指定帧"""
        if self.video_cap:
            frame_pos = int(self.video_slider.get())
            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            self.video_current_frame = frame_pos

            # 读取并显示当前帧
            ret, frame = self.video_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                self.photo = ImageTk.PhotoImage(image)

                # 获取画布尺寸
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                # 清除之前的图像
                self.canvas.delete("all")
                # 创建新图像
                self.canvas.create_image(canvas_width // 2, canvas_height // 2,
                                         anchor="center", image=self.photo)

    def show_video_frame(self):
        """显示当前视频帧"""
        if self.video_cap:
            ret, frame = self.video_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                self.photo = ImageTk.PhotoImage(image)
                self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
                self.canvas.image = self.photo

    def on_canvas_configure(self, event):
        """当画布大小改变时，更新滚动条"""
        if self.image or self.video_cap:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        """鼠标滚轮事件处理"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_canvas_scroll(self, *args):
        """画布滚动事件处理"""
        if self.image or self.video_cap:
            self.canvas.yview(*args)

    def get_canvas_coordinates(self, event):
        """获取画布上的实际坐标"""
        # 获取画布的当前滚动位置
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        return x, y

    # def show_image(self):
    #     # 清除画布上的所有内容
    #     self.canvas.delete("all")
    #     self.photo = ImageTk.PhotoImage(self.image)
    #
    #     # 创建滚动区域大小与图片大小一致
    #     self.canvas.config(scrollregion=(0, 0, self.image.width, self.image.height))
    #     self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
    #
    #     # 更新坐标显示
    #     self.coord_label.config(text="坐标: (0, 0)")
    def show_media(self):
        # 清除画布上的所有内容
        self.canvas.delete("all")

        if self.image:  # 图片模式
            self.photo = ImageTk.PhotoImage(self.image)
            # 创建滚动区域大小与图片大小一致
            self.canvas.config(scrollregion=(0, 0, self.image.width, self.image.height))
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        elif self.video_cap:  # 视频模式
            success, frame = self.video_cap.read()
            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                self.photo = ImageTk.PhotoImage(image)
                # 创建滚动区域大小与视频帧大小一致
                self.canvas.config(scrollregion=(0, 0, image.width, image.height))
                self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.canvas.image = self.photo
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
        if (self.rect and self.image and self.current_folder) or (self.rect and self.video_cap and self.current_folder):
            x, y = self.get_canvas_coordinates(event)
            x1, y1 = self.start_x, self.start_y
            x2, y2 = x, y

            # 获取画布的滚动位置
            scroll_x = self.canvas.xview()[0]
            scroll_y = self.canvas.yview()[0]

            # 调整坐标，考虑滚动位置
            canvas_height = self.canvas.winfo_height()
            scroll_offset_y = scroll_y * canvas_height

            # 确保坐标顺序正确（小值在前）
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            # 应用滚动条偏移
            y1 = y1 - scroll_offset_y
            y2 = y2 - scroll_offset_y

            if x1 != x2 and y1 != y2:
                if self.image:  # 图片模式保持不变
                    cropped = self.image.crop((int(x1), int(y1), int(x2), int(y2)))
                    if cropped.mode == 'RGBA':
                        cropped = cropped.convert('RGB')
                    next_number = self.get_next_number()
                    save_path = os.path.join(self.current_folder, f"{next_number}.jpg")
                    cropped.save(save_path)
                    self.update_history_list()
                    self.flow_manager.notify_screenshots_updated()
                    self.info_label.config(text=f"已保存截图 {next_number}.jpg ({int(x2 - x1)}x{int(y2 - y1)}像素)")
                    self.show_preview(save_path)

                elif self.video_cap:  # 视频模式
                    # 保存当前帧位置
                    current_frame_pos = int(self.video_cap.get(cv2.CAP_PROP_POS_FRAMES))

                    # 获取当前帧
                    ret, frame = self.video_cap.read()
                    if ret:
                        # 获取视频的原始尺寸，用于边界检查
                        original_width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        original_height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                        # 直接使用调整后的画布坐标，仅做边界检查
                        crop_x1 = max(0, min(int(x1), original_width))
                        crop_y1 = max(0, min(int(y1), original_height))
                        crop_x2 = max(0, min(int(x2), original_width))
                        crop_y2 = max(0, min(int(y2), original_height))

                        try:
                            # 直接在原始帧上截取指定区域
                            cropped_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2].copy()
                            if cropped_frame.size > 0:  # 确保截取的区域有效
                                # 转换颜色空间并创建图像对象
                                cropped_frame_rgb = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
                                cropped_image = Image.fromarray(cropped_frame_rgb)

                                # 保存截图
                                next_number = self.get_next_number()
                                save_path = os.path.join(self.current_folder, f"{next_number}.jpg")
                                cropped_image.save(save_path)

                                # 更新界面
                                self.update_history_list()
                                self.flow_manager.notify_screenshots_updated()
                                self.info_label.config(text=f"已保存截图 {next_number}.jpg ({crop_x2 - crop_x1}x{crop_y2 - crop_y1}像素)")
                                self.show_preview(save_path)
                            else:
                                self.info_label.config(text="截图区域无效，请重新选择")
                        except Exception as e:
                            self.info_label.config(text=f"截图失败: {str(e)}")

                        # 恢复视频帧位置
                        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_pos)

    def update_history_list(self):
        """更新历史记录列表"""
        self.history_listbox.delete(0, tk.END)
        if self.current_folder and os.path.exists(self.current_folder):
            files = [f for f in os.listdir(self.current_folder) if f.endswith('.jpg')]
            files.sort(key=lambda x: int(x.split('.')[0]))
            for file in files:
                self.history_listbox.insert(tk.END, file)

    def handle_flow_event(self, event):
        if event == "flow_changed":
            self.current_folder = self.flow_manager.get_screenshot_dir()
            self.update_history_list()
            if self.history_listbox.size() == 0:
                self.preview_label.config(image='', text="暂无截图", bg='#f0f0f0')
                self.delete_button.config(state="disabled")
        elif event == "screenshots_updated":
            self.update_history_list()

    def get_next_number(self):
        """获取下一个可用的编号"""
        if not os.path.exists(self.current_folder):
            return 1
        files = [f for f in os.listdir(self.current_folder) if f.endswith('.jpg')]
        if not files:
            return 1
        numbers = [int(f.split('.')[0]) for f in files if f.split('.')[0].isdigit()]
        return max(numbers) + 1 if numbers else 1

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
                self.flow_manager.notify_screenshots_updated()

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

    def create_widgets(self):
        # 创建主框架，在右侧区域中布局
        main_frame = tk.Frame(self.frame)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # 左侧框架（用于预览和历史记录）
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", padx=10)

        # 右侧框架（用于主图片显示及操作）
        self.right_frame = tk.Frame(main_frame)  # 将right_frame设为实例变量，方便隐藏/显示
        self.right_frame.pack(side="right", expand=True, fill="both")

        # 创建按钮框架
        button_frame = tk.Frame(left_frame)
        button_frame.pack(pady=5)

        self.select_button = tk.Button(button_frame, text="选择文件", command=self.select_media)
        self.select_button.pack(side="left", padx=2)

        # 添加显示/隐藏按钮
        self.toggle_button = tk.Button(button_frame, text="隐藏图片", command=self.toggle_right_frame)
        self.toggle_button.pack(side="left", padx=2)

        # 创建按钮和信息显示区
        control_frame = tk.Frame(self.right_frame)
        control_frame.pack(fill="x", pady=5)

        # 添加尺寸信息标签
        self.size_label = tk.Label(control_frame, text="原始尺寸: -")
        self.size_label.pack(side="left", padx=5, pady=10)

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

        self.history_listbox = tk.Listbox(left_frame, width=20, height=15)
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

if __name__ == "__main__":
    from flow_manager import FlowManager

    flow_manager = FlowManager()
    root = tk.Tk()
    right_container = tk.Frame(root)
    app = ImageCropper(right_container, root, flow_manager)
    right_container.pack(fill=tk.BOTH, expand=True)  # 添加这行代码
    root.mainloop()