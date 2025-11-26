# -*- coding:utf-8 -*-
# @Author: scofield
# @Time: 2025/2/06 22:21
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
from tkinter import ttk, messagebox, filedialog
import json
import os
import threading
from flow_manager import FlowManager
from function import find_and_click, input_text, move_and_click, wait, read_excel_first_column

class Process:
    def __init__(self, master, flow_manager: FlowManager):
        # 使用 Frame 作为主容器
        self.frame = tk.Frame(master, bg='#f0f0f0')
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.flow_manager = flow_manager
        self.flow_manager.register_listener(self.handle_flow_event)

        # 流程设置框架
        self.flow_frame = ttk.Frame(self.frame)
        self.flow_frame.pack(pady=(10, 0), padx=10, fill='x')

        ttk.Label(self.flow_frame, text="流程名称:").pack(side='left')
        self.flow_name_var = tk.StringVar()
        self.flow_name_entry = ttk.Entry(self.flow_frame, textvariable=self.flow_name_var, width=25)
        self.flow_name_entry.pack(side='left', padx=5)

        self.add_flow_button = ttk.Button(self.flow_frame, text="添加流程", command=self.create_flow)
        self.add_flow_button.pack(side='left', padx=5)

        self.select_flow_button = ttk.Button(self.flow_frame, text="读取流程", command=self.select_existing_flow)
        self.select_flow_button.pack(side='left', padx=5)

        self.current_flow_label = ttk.Label(self.flow_frame, text="当前流程: 未设置")
        self.current_flow_label.pack(side='left', padx=10)

        # 按钮框架
        self.buttons_frame = ttk.Frame(self.frame)
        self.buttons_frame.pack(pady=10, padx=10, fill='x')

        button_config = {
            '添加': self.add_step,
            '运行': self.run_steps,
            '全部删除': self.delete_all_steps,
            '保存流程': self.save_steps
        }

        self.loop_count_var = tk.StringVar(value="1")
        self.loop_count_entry = None

        self.run_button = None
        for text, command in button_config.items():
            btn = ttk.Button(self.buttons_frame, text=text, command=command)
            btn.pack(side='left', padx=5)
            if text == '运行':
                self.run_button = btn

        ttk.Label(self.buttons_frame, text="循环次数:").pack(side='left', padx=(15, 5))
        self.loop_count_entry = ttk.Entry(self.buttons_frame, textvariable=self.loop_count_var, width=6)
        self.loop_count_entry.pack(side='left')
        self.image_dir = None
        self._is_running = False

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

    def create_flow(self):
        flow_name = self.flow_name_var.get().strip()
        if not flow_name:
            messagebox.showwarning("提示", "流程名称不能为空。")
            return
        try:
            self.flow_manager.set_flow_name(flow_name)
        except ValueError as exc:
            messagebox.showerror("错误", str(exc))
            return
        except OSError as exc:
            messagebox.showerror("错误", f"创建流程目录失败: {exc}")
            return

        messagebox.showinfo("成功", f"流程 '{flow_name}' 已准备就绪。")

    def select_existing_flow(self):
        initial_dir = self.flow_manager.base_dir
        directory = filedialog.askdirectory(initialdir=initial_dir, title="选择流程文件夹")
        if not directory:
            return
        try:
            self.flow_manager.set_flow_from_directory(directory)
        except ValueError as exc:
            messagebox.showerror("错误", str(exc))
            return

        flow_name = self.flow_manager.get_flow_name() or ""
        self.flow_name_var.set(flow_name)

        json_path = self.flow_manager.get_json_path()
        if json_path and os.path.exists(json_path):
            if self._load_steps_from_file(json_path):
                messagebox.showinfo("成功", f"流程 '{flow_name}' 已加载并切换完成！")
        else:
            self.delete_all_steps()
            messagebox.showinfo("提示", f"流程 '{flow_name}' 已切换，但未找到保存的步骤。")

    def get_available_images(self):
        if not self.image_dir or not os.path.exists(self.image_dir):
            return []
        return [
            f for f in os.listdir(self.image_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
        ]

    def refresh_image_sources(self):
        image_files = self.get_available_images()
        for step in self.steps:
            widget = step.get('params_widgets', {}).get('image_path')
            if widget:
                current_value = widget.get()
                widget['values'] = image_files
                if current_value and current_value not in image_files:
                    widget.set('')

    def handle_flow_event(self, event):
        if event == "flow_changed":
            flow_name = self.flow_manager.get_flow_name() or "未设置"
            self.image_dir = self.flow_manager.get_screenshot_dir()
            self.current_flow_label.config(text=f"当前流程: {flow_name}")
            self.refresh_image_sources()
        elif event == "screenshots_updated":
            self.refresh_image_sources()

    def add_step(self):
        row = len(self.steps)
        step_label = ttk.Label(self.steps_frame, text=f"步骤 {row + 1}:")
        step_label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

        step_combobox = ttk.Combobox(
            self.steps_frame,
            values=["find_and_click", "input_text", "move_and_click", "wait", "input_from_excel"],
            state="readonly",
            width=15
        )
        step_combobox.grid(row=row, column=1, padx=5, pady=5)
        step_combobox.current(0)

        params_frame = ttk.Frame(self.steps_frame, width=200)
        params_frame.grid(row=row, column=2, padx=5, pady=5, sticky="w")

        control_frame = ttk.Frame(self.steps_frame)
        control_frame.grid(row=row, column=3, padx=5, pady=5, sticky="e")

        delete_button = ttk.Button(control_frame, text="删除", width=6)
        delete_button.pack(side="left", padx=(0, 6))

        move_group = ttk.Frame(control_frame)
        move_group.pack(side="left")

        move_up_button = ttk.Button(move_group, text="上移", width=5)
        move_up_button.pack(fill="x")

        move_down_button = ttk.Button(move_group, text="下移", width=5)
        move_down_button.pack(fill="x", pady=(4, 0))

        step_data = {
            'label': step_label,
            'combobox': step_combobox,
            'params_frame': params_frame,
            'control_frame': control_frame,
            'delete_button': delete_button,
            'move_up_button': move_up_button,
            'move_down_button': move_down_button,
            'params': {},
            'params_widgets': {}
        }

        step_combobox.bind('<<ComboboxSelected>>', lambda e, entry=step_data: self._on_action_changed(entry))
        delete_button.config(command=lambda entry=step_data: self._delete_step_by_ref(entry))
        move_up_button.config(command=lambda entry=step_data: self._move_step(entry, -1))
        move_down_button.config(command=lambda entry=step_data: self._move_step(entry, 1))

        self.steps.append(step_data)

        self.update_step_params(len(self.steps) - 1)

        self._refresh_step_layout()

    def _on_action_changed(self, step_entry):
        index = self._get_step_index(step_entry)
        if index is None:
            return
        self.update_step_params(index)

    def _delete_step_by_ref(self, step_entry):
        index = self._get_step_index(step_entry)
        if index is None:
            return
        self.delete_step(index)

    def _move_step(self, step_entry, direction: int):
        index = self._get_step_index(step_entry)
        if index is None:
            return
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.steps):
            return
        self.steps[index], self.steps[new_index] = self.steps[new_index], self.steps[index]
        self._refresh_step_layout()

    def _refresh_step_layout(self):
        for i, step in enumerate(self.steps):
            step['label'].grid_configure(row=i)
            step['combobox'].grid_configure(row=i)
            step['params_frame'].grid_configure(row=i)
            step['control_frame'].grid_configure(row=i)

            step['label'].config(text=f"步骤 {i + 1}:")
            up_state = tk.DISABLED if i == 0 else tk.NORMAL
            down_state = tk.DISABLED if i == len(self.steps) - 1 else tk.NORMAL
            step['move_up_button'].config(state=up_state)
            step['move_down_button'].config(state=down_state)

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _get_step_index(self, step_entry):
        try:
            return self.steps.index(step_entry)
        except ValueError:
            return None

    def update_step_params(self, index):
        # 清除之前的参数输入区和控件引用
        for widget in self.steps[index]['params_frame'].winfo_children():
            widget.destroy()
        self.steps[index]['params_widgets'] = {}  # 重置参数控件引用

        action = self.steps[index]['combobox'].get()

        image_files = self.get_available_images()

        # 创建参数控件并记录到params_widgets
        if action == 'find_and_click':
            # 图片路径
            combo_image = ttk.Combobox(
                self.steps[index]['params_frame'],
                values=image_files,
                width=28
            )
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

        elif action == 'wait':
            entry_seconds = ttk.Entry(self.steps[index]['params_frame'], width=8)
            entry_seconds.insert(0, '1')
            entry_seconds.grid(row=0, column=1)
            self.steps[index]['params_widgets']['seconds'] = entry_seconds
            ttk.Label(self.steps[index]['params_frame'], text="等待秒数:").grid(row=0, column=0, sticky="w")

        elif action == 'input_from_excel':
            entry_excel = ttk.Entry(self.steps[index]['params_frame'], width=20)
            entry_excel.grid(row=0, column=1, padx=(0, 5))
            self.steps[index]['params_widgets']['excel_path'] = entry_excel

            def browse_file(entry_ref=entry_excel):
                file_path = filedialog.askopenfilename(
                    title="选择 Excel 文件",
                    filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
                )
                if file_path:
                    entry_ref.delete(0, tk.END)
                    entry_ref.insert(0, file_path)

            browse_button = ttk.Button(self.steps[index]['params_frame'], text="浏览", command=browse_file, width=6)
            browse_button.grid(row=0, column=2)
            ttk.Label(self.steps[index]['params_frame'], text="Excel 路径:").grid(row=0, column=0, sticky="w")

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def save_steps(self):
        if not self.flow_manager.has_flow():
            messagebox.showwarning("提示", "请先创建并选择流程，再保存步骤。")
            return

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
                elif param_key == 'seconds':
                    try:
                        value = float(value) if value else 0.0
                    except ValueError:
                        value = 0.0

                params[param_key] = value

            steps_data['steps'].append({
                "action": action,
                "params": params
            })

        file_path = self.flow_manager.get_json_path()
        if not file_path:
            messagebox.showerror("错误", "无法获取流程保存路径。")
            return

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(steps_data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("成功", f"流程已保存到 {file_path}")

    def load_steps(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON 文件", "*.json")])
        if not file_path:
            return
        if self._load_steps_from_file(file_path):
            messagebox.showinfo("成功", "流程已加载！")

    def _load_steps_from_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                steps_data = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")
            return False

        # 清除现有步骤
        self.delete_all_steps()

        # 添加新步骤
        for step_data in steps_data.get('steps', []):
            self.add_step()
            current_step = self.steps[-1]
            action = step_data['action']
            current_step['combobox'].set(action)

            # 强制更新参数界面
            self.update_step_params(len(self.steps) - 1)

            # 填充参数值
            for param_key, param_value in step_data.get('params', {}).items():
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

        return True

    def delete_step(self, index):
        self.steps[index]['label'].destroy()
        self.steps[index]['combobox'].destroy()
        self.steps[index]['params_frame'].destroy()
        self.steps[index]['control_frame'].destroy()
        del self.steps[index]

        self._refresh_step_layout()

    def delete_all_steps(self):
        for step in self.steps:
            step['label'].destroy()
            step['combobox'].destroy()
            step['params_frame'].destroy()
            step['control_frame'].destroy()
        self.steps.clear()

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def run_steps(self):
        """执行所有步骤（异步避免阻塞 UI）"""
        if self._is_running:
            messagebox.showinfo("提示", "流程正在运行，请稍候。")
            return

        if not self.steps:
            messagebox.showwarning("提示", "没有可执行的步骤。")
            return
        
        if not self.flow_manager.has_flow():
            messagebox.showwarning("提示", "请先创建并选择流程。")
            return

        screenshot_dir = self.flow_manager.get_screenshot_dir()
        loop_value = self.loop_count_var.get().strip()
        if not loop_value:
            loop_times = 1
            self.loop_count_var.set("1")
        else:
            try:
                loop_times = int(loop_value)
            except ValueError:
                messagebox.showwarning("提示", "循环次数必须是整数。")
                return
            if loop_times <= 0:
                messagebox.showwarning("提示", "循环次数必须大于 0。")
                return

        self._is_running = True
        self._set_run_button_state(disabled=True)

        worker = threading.Thread(
            target=self._run_steps_worker,
            args=(screenshot_dir, loop_times),
            daemon=True
        )
        worker.start()

    def _prepare_excel_inputs(self, loop_times: int):
        excel_inputs = {}
        for index, step in enumerate(self.steps):
            if step['combobox'].get() != 'input_from_excel':
                continue
            params_widgets = step.get('params_widgets', {})
            path_widget = params_widgets.get('excel_path')
            if not path_widget:
                raise ValueError(f"步骤 {index + 1}: 未找到 Excel 路径输入框")
            excel_path = path_widget.get().strip()
            if not excel_path:
                raise ValueError(f"步骤 {index + 1}: Excel 路径不能为空")
            try:
                values = read_excel_first_column(excel_path)
            except Exception as exc:
                raise ValueError(f"步骤 {index + 1}: Excel 读取失败: {exc}") from exc
            if len(values) < loop_times:
                raise ValueError(f"步骤 {index + 1}: Excel 数据不足，只有 {len(values)} 行，无法满足 {loop_times} 次循环")
            excel_inputs[index] = values
        return excel_inputs

    def _run_steps_worker(self, screenshot_dir, loop_times):
        try:
            excel_inputs = self._prepare_excel_inputs(loop_times)
            for loop_index in range(loop_times):
                print(f"\n开始执行第 {loop_index + 1}/{loop_times} 轮流程")
                for i, step in enumerate(self.steps, 1):
                    action = step['combobox'].get()
                    params_widgets = step.get('params_widgets', {})
                    
                    print(f"\n执行步骤 {i}: {action}")
                    
                    if action == 'find_and_click':
                        image_path_widget = params_widgets.get('image_path')
                        if not image_path_widget:
                            print(f"步骤 {i}: 缺少图片路径参数")
                            continue
                        
                        image_filename = image_path_widget.get().strip()
                        if not image_filename:
                            print(f"步骤 {i}: 图片路径为空")
                            continue
                        
                        if screenshot_dir and os.path.exists(screenshot_dir):
                            full_image_path = os.path.join(screenshot_dir, image_filename)
                        else:
                            full_image_path = image_filename
                        
                        d_x_widget = params_widgets.get('d_x')
                        d_x = int(d_x_widget.get() or 0) if d_x_widget else 0
                        
                        d_y_widget = params_widgets.get('d_y')
                        d_y = int(d_y_widget.get() or 0) if d_y_widget else 0
                        
                        click_times_widget = params_widgets.get('click_times')
                        click_times = int(click_times_widget.get() or 1) if click_times_widget else 1
                        
                        find_and_click(
                            image_path=full_image_path,
                            d_x=d_x,
                            d_y=d_y,
                            click_times=click_times
                        )
                    
                    elif action == 'input_text':
                        text_widget = params_widgets.get('text')
                        if not text_widget:
                            print(f"步骤 {i}: 缺少文本参数")
                            continue
                        
                        text = text_widget.get().strip()
                        if not text:
                            print(f"步骤 {i}: 输入文本为空")
                            continue

                        input_text(text=text)
                    
                    elif action == 'input_from_excel':
                        excel_values = excel_inputs.get(i - 1)
                        if not excel_values:
                            print(f"步骤 {i}: 未准备好 Excel 数据")
                            continue
                        text = excel_values[loop_index]
                        print(f"步骤 {i}: Excel 输入 -> {text}")
                        input_text(text=text)

                    elif action == 'move_and_click':
                        X_widget = params_widgets.get('X')
                        X = int(X_widget.get() or 0) if X_widget else 0
                        
                        Y_widget = params_widgets.get('Y')
                        Y = int(Y_widget.get() or 0) if Y_widget else 0
                        
                        scroll_times_widget = params_widgets.get('scroll_times')
                        scroll_times = int(scroll_times_widget.get() or 0) if scroll_times_widget else 0
                        
                        scroll_distance_widget = params_widgets.get('scroll_distance')
                        scroll_distance = int(scroll_distance_widget.get() or 0) if scroll_distance_widget else 0
                        
                        click_times_widget = params_widgets.get('click_times')
                        click_times = int(click_times_widget.get() or 1) if click_times_widget else 1
                        
                        move_and_click(
                            X=X,
                            Y=Y,
                            scroll_times=scroll_times,
                            scroll_distance=scroll_distance,
                            click_times=click_times
                        )
                    
                    elif action == 'wait':
                        seconds_widget = params_widgets.get('seconds')
                        if seconds_widget:
                            try:
                                seconds = float(seconds_widget.get() or 0)
                            except ValueError:
                                seconds = 0.0
                        else:
                            seconds = 0.0
                        wait(seconds)
                    
                    else:
                        print(f"步骤 {i}: 未知操作类型 '{action}'")
                        continue
        except Exception as exc:
            self._notify_async_error(exc)
            print(f"执行错误: {exc}")
        finally:
            self.frame.after(0, self._on_run_finished)

        print("\n所有轮次执行完成！")

    def _notify_async_error(self, exc: Exception):
        self.frame.after(0, lambda: messagebox.showerror("错误", f"执行步骤时发生错误: {str(exc)}"))

    def _on_run_finished(self):
        self._is_running = False
        self._set_run_button_state(disabled=False)

    def _set_run_button_state(self, disabled: bool):
        if self.run_button:
            state = tk.DISABLED if disabled else tk.NORMAL
            self.run_button.config(state=state)

if __name__ == "__main__":
    root = tk.Tk()
    app = Process(root)
    root.geometry("1000x600")
    root.mainloop()

