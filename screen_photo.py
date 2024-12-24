import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import hashlib

class ImageCropper:
    def __init__(self, root):
        self.root = root
        self.root.title("图片裁剪工具")

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

        # 设置预览框的大小
        self.preview_width = 200
        self.preview_height = 200

        # 创建主存储目录
        self.base_dir = "crops"
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        # 创建界面
        self.create_widgets()

    def get_image_hash(self, image_path):
        """生成图片文件的hash值作为文件夹名"""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:12]

    def create_widgets(self):
        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # 左侧框架（用于主图片）
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", expand=True, fill="both")

        # 右侧框架（用于预览和历史记录）
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", padx=10)

        # 创建按钮
        self.select_button = tk.Button(left_frame, text="选择图片", command=self.select_image)
        self.select_button.pack(pady=5)

        # 创建画布
        self.canvas = tk.Canvas(left_frame, cursor="cross")
        self.canvas.pack(expand=True, fill="both")

        # 创建历史记录列表框
        history_label = tk.Label(right_frame, text="历史截图:")
        history_label.pack(pady=(0, 5))

        self.history_listbox = tk.Listbox(right_frame, width=30, height=15)
        self.history_listbox.pack(fill="both", expand=True)

        # 创建预览框架
        preview_frame = tk.Frame(right_frame, width=self.preview_width, height=self.preview_height)
        preview_frame.pack_propagate(False)
        preview_frame.pack(pady=10)

        # 创建预览标签
        self.preview_label = tk.Label(preview_frame, text="暂无截图", bg='#f0f0f0')
        self.preview_label.pack(expand=True, fill="both")

        # 创建删除按钮
        self.delete_button = tk.Button(right_frame, text="删除选中截图", command=self.delete_selected)
        self.delete_button.pack(pady=5)
        self.delete_button.config(state="disabled")

        # 显示信息标签
        self.info_label = tk.Label(left_frame, text="请选择要处理的图片")
        self.info_label.pack(pady=5)

        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_select_history)

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

            # 显示图片
            self.show_image()

            # 更新历史记录
            self.update_history_list()

            # 更新信息
            self.info_label.config(text=f"当前图片: {os.path.basename(file_path)}")

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

    def delete_selected(self):
        """删除选中的历史截图"""
        selection = self.history_listbox.curselection()
        if selection:
            filename = self.history_listbox.get(selection[0])
            file_path = os.path.join(self.current_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.update_history_list()
                self.preview_label.config(image='', text="暂无截图", bg='#f0f0f0')
                self.info_label.config(text=f"已删除: {filename}")

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

    def show_image(self):
        # 清除画布上的所有内容
        self.canvas.delete("all")
        self.photo = ImageTk.PhotoImage(self.image)
        # 创建滚动区域大小与图片大小一致
        self.canvas.config(scrollregion=(0, 0, self.image.width, self.image.height))
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(
                self.rect,
                self.start_x, self.start_y,
                event.x, event.y
            )

    def on_release(self, event):
        if self.rect and self.image and self.current_folder:
            coords = self.canvas.coords(self.rect)
            x1, y1, x2, y2 = [int(coord) for coord in coords]

            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            if x1 != x2 and y1 != y2:
                cropped = self.image.crop((x1, y1, x2, y2))

                # 转换为 RGB 模式以支持 JPEG
                if cropped.mode == 'RGBA':
                    cropped = cropped.convert('RGB')

                # 保存截图
                next_number = self.get_next_number()
                save_path = os.path.join(self.current_folder, f"{next_number}.jpg")
                cropped.save(save_path)
                self.update_history_list()
                self.info_label.config(text=f"已保存: {next_number}.jpg")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x600")
    app = ImageCropper(root)
    root.mainloop()