# -*- coding:utf-8 -*-
# @Author: scofield
# @Time: 2025/11/26 16:21
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
import shlex
import time
from flow_manager import FlowManager
from function import find_and_click, input_text, move_and_click, wait, read_excel_first_column, run_python, simulate_key

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

        # 保存流程按钮放在最左边
        self.save_flow_button = ttk.Button(self.flow_frame, text="保存流程", command=self.save_steps)
        self.save_flow_button.pack(side='left', padx=5)

        self.select_flow_button = ttk.Button(self.flow_frame, text="读取流程", command=self.select_existing_flow)
        self.select_flow_button.pack(side='left', padx=5)

        self.current_flow_label = ttk.Label(self.flow_frame, text="当前流程: 未设置")
        self.current_flow_label.pack(side='left', padx=10)

        ttk.Label(self.flow_frame, text="流程名称:").pack(side='left')
        self.flow_name_var = tk.StringVar()
        self.flow_name_entry = ttk.Entry(self.flow_frame, textvariable=self.flow_name_var, width=25)
        self.flow_name_entry.pack(side='left', padx=5)

        self.add_flow_button = ttk.Button(self.flow_frame, text="添加流程", command=self.create_flow)
        self.add_flow_button.pack(side='left', padx=5)

        # 运行控制框架（位于流程设置第二行）
        self.loop_count_var = tk.StringVar(value="1")
        self.run_control_frame = ttk.Frame(self.frame)
        self.run_control_frame.pack(pady=(4, 0), padx=10, fill='x')

        self.run_button = tk.Button(
            self.run_control_frame,
            text="运行",
            command=self.run_steps,
            width=10,
            bg='#28a745',
            fg='white',
            activebackground='#218838',
            activeforeground='white',
            disabledforeground='gray',
            relief=tk.RAISED
        )
        self.run_button.pack(side='left', padx=5)

        ttk.Label(self.run_control_frame, text="循环次数:").pack(side='left', padx=(15, 5))
        self.loop_count_entry = ttk.Entry(self.run_control_frame, textvariable=self.loop_count_var, width=6)
        self.loop_count_entry.pack(side='left')

        self.stop_button = tk.Button(
            self.run_control_frame,
            text="中止运行",
            command=self.stop_running,
            state=tk.DISABLED,
            width=10,
            bg='#FFB6C1',
            activebackground='#c82333',
            activeforeground='white',
            relief=tk.RAISED
        )
        self.stop_button.pack(side='left', padx=5)

        # 吊死恢复流程区域
        self.hang_timeout_var = tk.StringVar(value="60")
        self.recovery_mode_var = tk.StringVar(value="continue_from_interrupt")
        self.recovery_section = ttk.LabelFrame(self.frame, text="吊死后运行的副流程")
        self.recovery_section.pack(fill='x', padx=10, pady=(12, 0))
        
        # 副流程折叠/展开按钮
        recovery_header_frame = ttk.Frame(self.recovery_section)
        recovery_header_frame.pack(fill='x', padx=5, pady=(4, 0))
        self.recovery_toggle_button = ttk.Button(
            recovery_header_frame,
            text="隐藏副流程",
            command=self._toggle_recovery_visibility,
            width=12
        )
        self.recovery_toggle_button.pack(side='right')
        self._recovery_visible = True  # 副流程默认可见

        # 副流程可折叠内容容器
        self.recovery_content_frame = ttk.Frame(self.recovery_section)
        self.recovery_content_frame.pack(fill='x', padx=5, pady=(0, 6))

        # 模式选择框架（放在最上面）
        recovery_mode_frame = ttk.Frame(self.recovery_content_frame)
        recovery_mode_frame.pack(fill='x', pady=(6, 4))

        ttk.Label(recovery_mode_frame, text="恢复模式:").pack(side='left', padx=(0, 8))
        
        mode1_radio = ttk.Radiobutton(
            recovery_mode_frame,
            text="从中断位置继续",
            variable=self.recovery_mode_var,
            value="continue_from_interrupt",
            command=self._on_recovery_mode_changed
        )
        mode1_radio.pack(side='left', padx=(0, 12))
        
        mode2_radio = ttk.Radiobutton(
            recovery_mode_frame,
            text="从选定步骤继续",
            variable=self.recovery_mode_var,
            value="continue_from_selected",
            command=self._on_recovery_mode_changed
        )
        mode2_radio.pack(side='left', padx=(0, 8))
        
        # 模式2的步骤选择下拉框
        ttk.Label(recovery_mode_frame, text="选择步骤:").pack(side='left', padx=(0, 4))
        self.recovery_step_combobox = ttk.Combobox(
            recovery_mode_frame,
            state="readonly",
            width=15
        )
        self.recovery_step_combobox.pack(side='left')
        # 注意：_update_recovery_step_options() 需要在 self.steps 初始化后调用

        recovery_top = ttk.Frame(self.recovery_content_frame)
        recovery_top.pack(fill='x', pady=(6, 4))

        ttk.Label(recovery_top, text="吊死超时阈值(秒):").pack(side='left')
        self.hang_timeout_entry = ttk.Entry(recovery_top, textvariable=self.hang_timeout_var, width=8)
        self.hang_timeout_entry.pack(side='left', padx=(4, 12))

        recovery_hint = ttk.Label(
            recovery_top,
            text="当主流程无响应超过该秒数后，会先运行一次副流程，然后根据恢复模式继续执行。",
            foreground="#555555"
        )
        recovery_hint.pack(side='left', expand=True, anchor='w')

        recovery_buttons = ttk.Frame(self.recovery_content_frame)
        recovery_buttons.pack(fill='x', pady=(0, 4))

        self.recovery_add_button = ttk.Button(recovery_buttons, text="添加副流程步骤", command=self.add_recovery_step)
        self.recovery_add_button.pack(side='left', padx=(0, 6))

        self.recovery_clear_button = ttk.Button(recovery_buttons, text="清空副流程", command=self.delete_all_recovery_steps)
        self.recovery_clear_button.pack(side='left')

        # 副流程步骤容器（带滚动条）
        self.recovery_steps_container = ttk.Frame(self.recovery_content_frame)
        self.recovery_steps_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 6))
        
        self.recovery_canvas = tk.Canvas(self.recovery_steps_container, bg='#f0f0f0')
        self.recovery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.recovery_scrollbar = ttk.Scrollbar(self.recovery_steps_container, orient="vertical", command=self.recovery_canvas.yview)
        self.recovery_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.recovery_canvas.configure(yscrollcommand=self.recovery_scrollbar.set)
        self.recovery_canvas.bind('<Configure>', lambda e: self.recovery_canvas.configure(scrollregion=self.recovery_canvas.bbox("all")))
        
        self.recovery_steps_frame = ttk.Frame(self.recovery_canvas)
        self.recovery_canvas.create_window((0, 0), window=self.recovery_steps_frame, anchor="nw")

        # 用横线与主流程区域隔开
        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', padx=10, pady=8)

        # 主流程区域
        self.main_flow_section = ttk.LabelFrame(self.frame, text="主流程")
        self.main_flow_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=(12, 0))
        
        # 主流程折叠/展开按钮
        main_flow_header_frame = ttk.Frame(self.main_flow_section)
        main_flow_header_frame.pack(fill='x', padx=5, pady=(4, 0))
        self.main_flow_toggle_button = ttk.Button(
            main_flow_header_frame,
            text="隐藏主流程",
            command=self._toggle_main_flow_visibility,
            width=12
        )
        self.main_flow_toggle_button.pack(side='right')
        self._main_flow_visible = True  # 主流程默认可见

        # 主流程可折叠内容容器
        self.main_flow_content_frame = ttk.Frame(self.main_flow_section)
        self.main_flow_content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 6))

        # 按钮框架
        self.buttons_frame = ttk.Frame(self.main_flow_content_frame)
        self.buttons_frame.pack(pady=10, padx=10, fill='x')

        button_config = {
            '添加': self.add_step,
            '全部删除': self.delete_all_steps
        }

        for text, command in button_config.items():
            btn = ttk.Button(self.buttons_frame, text=text, command=command)
            btn.pack(side='left', padx=5)
        self.image_dir = None
        self._is_running = False
        self._stop_event = threading.Event()

        # 步骤容器
        self.steps_container = ttk.Frame(self.main_flow_content_frame)
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
        self.recovery_steps = []
        self._recovery_requested = threading.Event()
        self._watchdog_stop_event = threading.Event()
        self._watchdog_thread = None
        self._pending_hang_timeout = 0.0
        self._last_progress_time = time.time()
        self._user_stop_requested = False
        
        # 初始化恢复步骤选择下拉框（需要在 self.steps 初始化后）
        self._update_recovery_step_options()
        self._on_recovery_mode_changed()  # 初始化显示状态

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
        for step_list in (self.steps, self.recovery_steps):
            for step in step_list:
                widget = step.get('params_widgets', {}).get('image_path')
                if widget:
                    current_value = widget.get()
                    widget['values'] = image_files
                    if current_value and current_value not in image_files:
                        widget.set('')

    def _parse_hang_timeout_input(self):
        value = (self.hang_timeout_var.get() or "").strip()
        if not value:
            return 0.0
        try:
            seconds = float(value)
        except ValueError as exc:
            raise ValueError("吊死超时阈值必须是数字") from exc
        return max(seconds, 0.0)

    def _get_hang_timeout_value(self):
        try:
            return self._parse_hang_timeout_input()
        except ValueError:
            return 0.0

    def _on_recovery_mode_changed(self):
        """当恢复模式改变时，更新步骤选择下拉框的显示状态"""
        mode = self.recovery_mode_var.get()
        if mode == "continue_from_selected":
            # 模式2：显示步骤选择下拉框
            self.recovery_step_combobox.config(state="readonly")
            # 确保选项已更新
            self._update_recovery_step_options()
        else:
            # 模式1：禁用下拉框（但保持可见，只是不可选）
            self.recovery_step_combobox.config(state="disabled")

    def _update_recovery_step_options(self):
        """更新恢复步骤选择下拉框的选项"""
        options = [f"步骤 {i + 1}" for i in range(len(self.steps))]
        self.recovery_step_combobox['values'] = options
        if options and self.recovery_step_combobox.get() == "":
            # 如果当前没有选择，默认选择第一个步骤
            self.recovery_step_combobox.current(0)

    def _toggle_recovery_visibility(self):
        """切换副流程的显示/隐藏状态"""
        if self._recovery_visible:
            self.recovery_content_frame.pack_forget()
            self.recovery_toggle_button.config(text="显示副流程")
            self._recovery_visible = False
        else:
            self.recovery_content_frame.pack(fill='x', padx=5, pady=(0, 6))
            self.recovery_toggle_button.config(text="隐藏副流程")
            self._recovery_visible = True

    def _toggle_main_flow_visibility(self):
        """切换主流程的显示/隐藏状态"""
        if self._main_flow_visible:
            self.main_flow_content_frame.pack_forget()
            self.main_flow_toggle_button.config(text="显示主流程")
            self._main_flow_visible = False
        else:
            self.main_flow_content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 6))
            self.main_flow_toggle_button.config(text="隐藏主流程")
            self._main_flow_visible = True

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
            values=["find_and_click", "input_text", "move_and_click", "wait", "input_from_excel", "run_python", "simulate_key"],
            state="readonly",
            width=15
        )
        step_combobox.grid(row=row, column=1, padx=5, pady=5)
        step_combobox.current(0)

        params_frame = ttk.Frame(self.steps_frame, width=200)
        params_frame.grid(row=row, column=2, padx=5, pady=5, sticky="w")

        control_frame = ttk.Frame(self.steps_frame)
        control_frame.grid(row=row, column=3, padx=5, pady=5, sticky="e")

        # 左侧：删除/添加 两个竖排按钮
        button_column = ttk.Frame(control_frame)
        button_column.pack(side="left", padx=(0, 6))

        delete_button = ttk.Button(button_column, text="删除", width=6)
        delete_button.pack(fill="x")

        add_button = ttk.Button(button_column, text="添加", width=6)
        add_button.pack(fill="x", pady=(4, 0))

        # 右侧：上移/下移 两个竖排按钮
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
            'add_button': add_button,
            'move_up_button': move_up_button,
            'move_down_button': move_down_button,
            'params': {},
            'params_widgets': {}
        }

        step_combobox.bind('<<ComboboxSelected>>', lambda e, entry=step_data: self._on_action_changed(entry))
        delete_button.config(command=lambda entry=step_data: self._delete_step_by_ref(entry))
        add_button.config(command=lambda entry=step_data: self._insert_step_after(entry))
        move_up_button.config(command=lambda entry=step_data: self._move_step(entry, -1))
        move_down_button.config(command=lambda entry=step_data: self._move_step(entry, 1))

        self.steps.append(step_data)

        self.update_step_params(len(self.steps) - 1)

        self._refresh_step_layout()
        self._update_recovery_step_options()  # 更新恢复步骤选择下拉框

    def add_recovery_step(self):
        # 如果框架被隐藏了（清空后），重新显示它
        # 检查是否是第一个步骤（从空到有）
        if len(self.recovery_steps) == 0:
            # 检查容器是否已经被 pack（通过检查是否在父容器中可见）
            try:
                pack_info = self.recovery_steps_container.pack_info()
                # 如果 pack_info 存在，说明已经 pack 了，不需要重新 pack
            except tk.TclError:
                # 容器被 pack_forget 了，重新 pack
                self.recovery_steps_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 6))
        
        row = len(self.recovery_steps)
        step_label = ttk.Label(self.recovery_steps_frame, text=f"步骤 {row + 1}:")
        step_label.grid(row=row, column=0, padx=5, pady=4, sticky="w")

        step_combobox = ttk.Combobox(
            self.recovery_steps_frame,
            values=["find_and_click", "input_text", "move_and_click", "wait", "input_from_excel", "run_python", "simulate_key"],
            state="readonly",
            width=18
        )
        step_combobox.grid(row=row, column=1, padx=5, pady=4, sticky="w")
        step_combobox.current(0)

        params_frame = ttk.Frame(self.recovery_steps_frame)
        params_frame.grid(row=row, column=2, padx=5, pady=4, sticky="w")

        control_frame = ttk.Frame(self.recovery_steps_frame)
        control_frame.grid(row=row, column=3, padx=5, pady=4, sticky="e")

        # 左侧：删除/添加 两个竖排按钮
        button_column = ttk.Frame(control_frame)
        button_column.pack(side="left", padx=(0, 6))

        delete_button = ttk.Button(button_column, text="删除", width=6)
        delete_button.pack(fill="x")

        add_button = ttk.Button(button_column, text="添加", width=6)
        add_button.pack(fill="x", pady=(4, 0))

        # 右侧：上移/下移 两个竖排按钮
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
            'add_button': add_button,
            'move_up_button': move_up_button,
            'move_down_button': move_down_button,
            'params': {},
            'params_widgets': {}
        }

        step_combobox.bind(
            '<<ComboboxSelected>>',
            lambda e, entry=step_data: self._on_action_changed_generic(entry, self.recovery_steps)
        )
        delete_button.config(command=lambda entry=step_data: self._delete_recovery_step_by_ref(entry))
        add_button.config(command=lambda entry=step_data: self._insert_recovery_step_after(entry))
        move_up_button.config(command=lambda entry=step_data: self._move_recovery_step(entry, -1))
        move_down_button.config(command=lambda entry=step_data: self._move_recovery_step(entry, 1))

        self.recovery_steps.append(step_data)
        self.update_step_params(len(self.recovery_steps) - 1, steps_list=self.recovery_steps)
        self._refresh_recovery_layout()

    def _on_action_changed(self, step_entry):
        self._on_action_changed_generic(step_entry, self.steps)

    def _on_action_changed_generic(self, step_entry, steps_list):
        index = self._get_step_index(step_entry, steps_list)
        if index is None:
            return
        self.update_step_params(index, steps_list=steps_list)

    def _delete_step_by_ref(self, step_entry):
        index = self._get_step_index(step_entry)
        if index is None:
            return
        self.delete_step(index)

    def _insert_step_after(self, step_entry):
        """在当前步骤下方插入一个新步骤。"""
        index = self._get_step_index(step_entry)
        if index is None:
            return
        # 先在末尾创建一个新步骤
        self.add_step()
        # 取出刚创建的步骤并插入到目标位置之后
        new_step = self.steps.pop()
        insert_pos = index + 1
        self.steps.insert(insert_pos, new_step)
        # 重新布局行号和标题
        self._refresh_step_layout()

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

    def _get_step_index(self, step_entry, steps_list=None):
        target_list = steps_list if steps_list is not None else self.steps
        try:
            return target_list.index(step_entry)
        except ValueError:
            return None

    def _delete_recovery_step_by_ref(self, step_entry):
        index = self._get_step_index(step_entry, self.recovery_steps)
        if index is None:
            return
        self._delete_recovery_step(index)

    def _delete_recovery_step(self, index):
        entry = self.recovery_steps[index]
        entry['label'].destroy()
        entry['combobox'].destroy()
        entry['params_frame'].destroy()
        entry['control_frame'].destroy()
        del self.recovery_steps[index]
        self._refresh_recovery_layout()
        # 如果删除后没有步骤了，隐藏容器
        if len(self.recovery_steps) == 0:
            self.recovery_steps_container.pack_forget()
            self.recovery_section.update_idletasks()
            self.frame.update_idletasks()

    def _refresh_recovery_layout(self):
        for i, step in enumerate(self.recovery_steps):
            step['label'].config(text=f"步骤 {i + 1}:")
            step['label'].grid_configure(row=i)
            step['combobox'].grid_configure(row=i)
            step['params_frame'].grid_configure(row=i)
            step['control_frame'].grid_configure(row=i)
            
            # 更新按钮状态
            up_state = tk.DISABLED if i == 0 else tk.NORMAL
            down_state = tk.DISABLED if i == len(self.recovery_steps) - 1 else tk.NORMAL
            step['move_up_button'].config(state=up_state)
            step['move_down_button'].config(state=down_state)
        
        # 更新滚动区域
        self.recovery_canvas.update_idletasks()
        self.recovery_canvas.config(scrollregion=self.recovery_canvas.bbox("all"))

    def _insert_recovery_step_after(self, step_entry):
        """在当前副流程步骤下方插入一个新步骤。"""
        index = self._get_step_index(step_entry, self.recovery_steps)
        if index is None:
            return
        # 先在末尾创建一个新步骤
        self.add_recovery_step()
        # 取出刚创建的步骤并插入到目标位置之后
        new_step = self.recovery_steps.pop()
        insert_pos = index + 1
        self.recovery_steps.insert(insert_pos, new_step)
        # 重新布局行号和标题
        self._refresh_recovery_layout()

    def _move_recovery_step(self, step_entry, direction: int):
        """移动副流程步骤位置"""
        index = self._get_step_index(step_entry, self.recovery_steps)
        if index is None:
            return
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.recovery_steps):
            return
        self.recovery_steps[index], self.recovery_steps[new_index] = self.recovery_steps[new_index], self.recovery_steps[index]
        self._refresh_recovery_layout()

    def delete_all_recovery_steps(self):
        for step in self.recovery_steps:
            step['label'].destroy()
            step['combobox'].destroy()
            step['params_frame'].destroy()
            step['control_frame'].destroy()
        self.recovery_steps.clear()
        # 完全隐藏 recovery_steps_container，让空白区域收缩
        self.recovery_steps_container.pack_forget()
        # 强制更新布局
        self.recovery_section.update_idletasks()
        self.frame.update_idletasks()

    def update_step_params(self, index, steps_list=None):
        target_list = steps_list if steps_list is not None else self.steps
        # 清除之前的参数输入区和控件引用
        for widget in target_list[index]['params_frame'].winfo_children():
            widget.destroy()
        target_list[index]['params_widgets'] = {}  # 重置参数控件引用

        action = target_list[index]['combobox'].get()

        image_files = self.get_available_images()

        # 创建参数控件并记录到params_widgets
        if action == 'find_and_click':
            # 图片路径
            combo_image = ttk.Combobox(
                target_list[index]['params_frame'],
                values=image_files,
                width=7
            )

            combo_image.grid(row=0, column=1, columnspan=2,sticky="w")
            target_list[index]['params_widgets']['image_path'] = combo_image

            # X/Y偏移
            entry_dx = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_dx.insert(0, '0')
            entry_dx.grid(row=1, column=1, sticky="w")
            target_list[index]['params_widgets']['d_x'] = entry_dx

            entry_dy = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_dy.insert(0, '0')
            entry_dy.grid(row=1, column=3, sticky="w")
            target_list[index]['params_widgets']['d_y'] = entry_dy

            # 点击次数
            entry_clicks_1 = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_clicks_1.insert(0, '1')
            entry_clicks_1.grid(row=1, column=5)
            target_list[index]['params_widgets']['click_times'] = entry_clicks_1

            # 在图片路径同行加入“超时跳过”控件：复选框 + 秒数输入

            timeout_var = tk.IntVar(value=0)
            timeout_check = ttk.Checkbutton(
                target_list[index]['params_frame'],
                variable=timeout_var
            )
            timeout_check.grid(row=0, column=3, sticky="e")
            entry_timeout = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_timeout.insert(0, '5')
            entry_timeout.grid(row=0, column=5, sticky="w")
            # 初始根据复选框设置秒数输入框状态（复选框未选中时禁用）
            try:
                entry_timeout.config(state='normal' if timeout_var.get() else 'disabled')
            except Exception:
                pass

            # 当复选框状态变化时，启用或禁用秒数输入框
            def _on_timeout_toggle(var=timeout_var, entry=entry_timeout):
                try:
                    entry.config(state='normal' if var.get() else 'disabled')
                except Exception:
                    pass

            # 兼容不同 tkinter 版本的监听方法
            try:
                timeout_var.trace_add('write', lambda *args: _on_timeout_toggle())
            except AttributeError:
                timeout_var.trace('w', lambda *args: _on_timeout_toggle())

            target_list[index]['params_widgets']['timeout_enabled'] = timeout_var
            target_list[index]['params_widgets']['timeout_seconds'] = entry_timeout

            # 添加标签
            ttk.Label(target_list[index]['params_frame'], text="图片路径:").grid(row=0, column=0, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="超时跳过:").grid(row=0, column=4, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="X偏移:").grid(row=1, column=0, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="Y偏移:").grid(row=1, column=2, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="点击次数:").grid(row=1, column=4, sticky="w")


        elif action == 'input_text':
            entry_text = ttk.Entry(target_list[index]['params_frame'], width=30)
            entry_text.grid(row=0, column=1)
            target_list[index]['params_widgets']['text'] = entry_text
            ttk.Label(target_list[index]['params_frame'], text="输入文本:").grid(row=0, column=0, sticky="w")

        elif action == 'move_and_click':
            # 坐标参数
            entry_x = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_x.insert(0, '0')
            entry_x.grid(row=0, column=1)
            target_list[index]['params_widgets']['X'] = entry_x

            entry_y = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_y.insert(0, '0')
            entry_y.grid(row=0, column=3)
            target_list[index]['params_widgets']['Y'] = entry_y

            # 滚动参数
            entry_scroll_times = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_scroll_times.insert(0, '0')
            entry_scroll_times.grid(row=1, column=1)
            target_list[index]['params_widgets']['scroll_times'] = entry_scroll_times

            entry_scroll_dist = ttk.Entry(target_list[index]['params_frame'], width=5)
            entry_scroll_dist.insert(0, '0')
            entry_scroll_dist.grid(row=1, column=3)
            target_list[index]['params_widgets']['scroll_distance'] = entry_scroll_dist

            # 点击次数
            entry_clicks_2 = ttk.Entry(target_list[index]['params_frame'], width=6)
            entry_clicks_2.insert(0, '1')
            entry_clicks_2.grid(row=1, column=5)
            target_list[index]['params_widgets']['click_times'] = entry_clicks_2

            combo_image = ttk.Combobox(
                target_list[index]['params_frame'],
                values=image_files,
                width=3
            )
            combo_image.grid(row=0, column=5, columnspan=2, padx=(5, 0))
            target_list[index]['params_widgets']['image_path'] = combo_image

            # 添加标签
            ttk.Label(target_list[index]['params_frame'], text="X移动:").grid(row=0, column=0, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="Y移动:").grid(row=0, column=2, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="滚动次数:").grid(row=1, column=0, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="滚动距离:").grid(row=1, column=2, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="点击:").grid(row=1, column=4, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="图片:").grid(row=0, column=4, sticky="w")

        elif action == 'wait':
            entry_seconds = ttk.Entry(target_list[index]['params_frame'], width=8)
            entry_seconds.insert(0, '1')
            entry_seconds.grid(row=0, column=1)
            target_list[index]['params_widgets']['seconds'] = entry_seconds
            ttk.Label(target_list[index]['params_frame'], text="等待秒数:").grid(row=0, column=0, sticky="w")

        elif action == 'input_from_excel':
            entry_excel = ttk.Entry(target_list[index]['params_frame'], width=20)
            entry_excel.grid(row=0, column=1, padx=(0, 5))
            target_list[index]['params_widgets']['excel_path'] = entry_excel

            def browse_file(entry_ref=entry_excel):
                file_path = filedialog.askopenfilename(
                    title="选择 Excel 文件",
                    filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
                )
                if file_path:
                    entry_ref.delete(0, tk.END)
                    entry_ref.insert(0, file_path)

            browse_button = ttk.Button(target_list[index]['params_frame'], text="浏览", command=browse_file, width=6)
            browse_button.grid(row=0, column=2)
            ttk.Label(target_list[index]['params_frame'], text="Excel 路径:").grid(row=0, column=0, sticky="w")

        elif action == 'run_python':
            env_entry = ttk.Entry(target_list[index]['params_frame'], width=19)
            env_entry.grid(row=0, column=1, padx=(0, 5), sticky="we")
            target_list[index]['params_widgets']['environment_path'] = env_entry

            def browse_env(entry_ref=env_entry):
                interpreter_path = filedialog.askopenfilename(
                    title="选择 Python 解释器",
                    filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
                )
                if interpreter_path:
                    entry_ref.delete(0, tk.END)
                    entry_ref.insert(0, interpreter_path)

            env_button = ttk.Button(target_list[index]['params_frame'], text="选择", command=browse_env, width=6)
            env_button.grid(row=0, column=2, padx=(0, 5))

            prog_entry = ttk.Entry(target_list[index]['params_frame'], width=19)
            prog_entry.grid(row=1, column=1, padx=(0, 6), sticky="we")
            target_list[index]['params_widgets']['program_path'] = prog_entry

            def browse_prog(entry_ref=prog_entry):
                file_path = filedialog.askopenfilename(
                    title="选择 Python 脚本",
                    filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")]
                )
                if file_path:
                    entry_ref.delete(0, tk.END)
                    entry_ref.insert(0, file_path)

            prog_button = ttk.Button(target_list[index]['params_frame'], text="浏览", command=browse_prog, width=6)
            prog_button.grid(row=1, column=2, padx=(0, 5))

            args_entry = ttk.Entry(target_list[index]['params_frame'], width=19)
            args_entry.grid(row=2, column=1, padx=(0, 5), sticky="we")
            target_list[index]['params_widgets']['args'] = args_entry

            ttk.Label(target_list[index]['params_frame'], text="Python路径:").grid(row=0, column=0, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="脚本路径:").grid(row=1, column=0, sticky="w")
            ttk.Label(target_list[index]['params_frame'], text="脚本参数:").grid(row=2, column=0, sticky="w")

        elif action == 'simulate_key':
            ttk.Label(target_list[index]['params_frame'], text="按键操作:").grid(row=0, column=0, sticky="w")
            entry_keys = ttk.Entry(target_list[index]['params_frame'], width=30)
            entry_keys.grid(row=0, column=1, sticky="ew")
            target_list[index]['params_widgets']['keys'] = entry_keys
            # 添加提示标签
            hint_label = ttk.Label(
                target_list[index]['params_frame'],
                text="示例:A B或ctrl+A(顺序操作：空格分隔)",
                font=('TkDefaultFont', 8),
                foreground='gray'
            )
            hint_label.grid(row=1, column=1)

        if target_list is self.steps:
            self.canvas.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _serialize_steps(self, step_list):
        serialized = []
        for step in step_list:
            action = step['combobox'].get()
            params = {}
            for param_key, widget in step.get('params_widgets', {}).items():
                # 支持不同控件类型返回值（IntVar 等有 get()，Entry/Combobox 返回字符串）
                try:
                    value = widget.get()
                except Exception:
                    # 直接取变量（如 IntVar）或其他可调用对象
                    try:
                        value = widget.get()
                    except Exception:
                        value = widget

                # 数值类型转换
                if param_key in ['d_x', 'd_y', 'X', 'Y', 'click_times', 'scroll_times', 'scroll_distance', 'timeout_enabled']:
                    try:
                        value = int(value) if value else 0
                    except Exception:
                        value = 0
                elif param_key in ['seconds', 'timeout_seconds']:
                    try:
                        value = float(value) if value else 0.0
                    except Exception:
                        value = 0.0
                elif param_key == 'args':
                    raw_args = (value or "").strip()
                    value = shlex.split(raw_args) if raw_args else []

                params[param_key] = value
            serialized.append({
                "action": action,
                "params": params
            })
        return serialized

    def save_steps(self):
        if not self.flow_manager.has_flow():
            messagebox.showwarning("提示", "请先创建并选择流程，再保存步骤。")
            return

        try:
            hang_timeout = self._parse_hang_timeout_input()
        except ValueError as exc:
            messagebox.showwarning("提示", str(exc))
            return

        loop_value = (self.loop_count_var.get() or "").strip()
        if not loop_value:
            loop_count = 1
            self.loop_count_var.set("1")
        else:
            try:
                loop_count = int(loop_value)
            except ValueError:
                messagebox.showwarning("提示", "循环次数必须是整数。")
                return
            if loop_count <= 0:
                messagebox.showwarning("提示", "循环次数必须大于 0。")
                return

        # 获取选定的步骤索引（如果是模式2）
        selected_step_index = None
        if self.recovery_mode_var.get() == "continue_from_selected":
            selected_step_str = self.recovery_step_combobox.get()
            if selected_step_str and selected_step_str.startswith("步骤 "):
                try:
                    selected_step_index = int(selected_step_str.replace("步骤 ", "")) - 1
                    if not (0 <= selected_step_index < len(self.steps)):
                        selected_step_index = None
                except ValueError:
                    selected_step_index = None

        steps_data = {
            "hang_timeout": hang_timeout,
            "recovery_mode": self.recovery_mode_var.get(),
            "recovery_selected_step": selected_step_index,
            "loop_count": loop_count,
            "steps": self._serialize_steps(self.steps),
            "recovery_steps": self._serialize_steps(self.recovery_steps)
        }

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

    def _populate_step_from_data(self, step_entry, steps_list, action, params):
        step_entry['combobox'].set(action)
        index = self._get_step_index(step_entry, steps_list)
        if index is None:
            return
        self.update_step_params(index, steps_list=steps_list)

        for param_key, param_value in params.items():
            widget = step_entry['params_widgets'].get(param_key)
            if not widget:
                continue

            if isinstance(widget, ttk.Combobox):
                widget.set(str(param_value))
            elif isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
                if param_key == 'args' and isinstance(param_value, (list, tuple)):
                    widget.insert(0, " ".join(str(arg) for arg in param_value))
                else:
                    widget.insert(0, str(param_value))
            else:
                # 处理变量类型（如 IntVar/BooleanVar）
                try:
                    # tk.Variable（IntVar/BooleanVar/StringVar 等）拥有 set 方法
                    widget.set(param_value)
                    # 如果是 timeout_enabled（IntVar），同步秒数输入框的可用状态
                    try:
                        if param_key == 'timeout_enabled':
                            timeout_entry = step_entry['params_widgets'].get('timeout_seconds')
                            if timeout_entry is not None:
                                try:
                                    state = 'normal' if int(param_value) else 'disabled'
                                except Exception:
                                    state = 'normal' if param_value else 'disabled'
                                try:
                                    timeout_entry.config(state=state)
                                except Exception:
                                    pass
                    except Exception:
                        pass
                except Exception:
                    # 忽略无法设置的控件类型
                    pass

    def _load_steps_from_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                steps_data = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")
            return False

        # 清除现有步骤
        self.delete_all_steps()
        self.delete_all_recovery_steps()

        for step_data in steps_data.get('steps', []):
            self.add_step()
            self._populate_step_from_data(
                self.steps[-1],
                self.steps,
                step_data.get('action', ''),
                step_data.get('params', {})
            )

        for step_data in steps_data.get('recovery_steps', []):
            self.add_recovery_step()
            self._populate_step_from_data(
                self.recovery_steps[-1],
                self.recovery_steps,
                step_data.get('action', ''),
                step_data.get('params', {})
            )

        hang_timeout = steps_data.get('hang_timeout')
        if hang_timeout is not None:
            # 将数值转换为字符串，如果小数部分为0则显示为整数
            if isinstance(hang_timeout, float) and hang_timeout.is_integer():
                self.hang_timeout_var.set(str(int(hang_timeout)))
            else:
                self.hang_timeout_var.set(str(hang_timeout))
        else:
            # 如果没有保存的值，使用默认值 60
            self.hang_timeout_var.set("60")

        loop_count = steps_data.get('loop_count')
        if loop_count is not None:
            self.loop_count_var.set(str(loop_count))
        else:
            self.loop_count_var.set("1")

        # 恢复恢复模式和选定的步骤
        recovery_mode = steps_data.get('recovery_mode', 'continue_from_interrupt')
        self.recovery_mode_var.set(recovery_mode)
        self._update_recovery_step_options()  # 先更新选项
        self._on_recovery_mode_changed()  # 更新显示状态
        
        recovery_selected_step = steps_data.get('recovery_selected_step')
        if recovery_selected_step is not None and 0 <= recovery_selected_step < len(self.steps):
            self.recovery_step_combobox.current(recovery_selected_step)

        return True

    def delete_step(self, index):
        self.steps[index]['label'].destroy()
        self.steps[index]['combobox'].destroy()
        self.steps[index]['params_frame'].destroy()
        self.steps[index]['control_frame'].destroy()
        del self.steps[index]

        self._refresh_step_layout()
        self._update_recovery_step_options()  # 更新恢复步骤选择下拉框

    def delete_all_steps(self):
        for step in self.steps:
            step['label'].destroy()
            step['combobox'].destroy()
            step['params_frame'].destroy()
            step['control_frame'].destroy()
        self.steps.clear()

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self._update_recovery_step_options()  # 更新恢复步骤选择下拉框

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

        try:
            hang_timeout = self._parse_hang_timeout_input()
        except ValueError as exc:
            messagebox.showwarning("提示", str(exc))
            return

        self._is_running = True
        self._stop_event.clear()
        self._recovery_requested.clear()
        self._set_run_button_state(disabled=True)
        self._set_stop_button_state(disabled=False)
        self._pending_hang_timeout = hang_timeout
        self._user_stop_requested = False

        worker = threading.Thread(
            target=self._run_steps_worker,
            args=(screenshot_dir, loop_times),
            daemon=True
        )
        worker.start()

    def stop_running(self):
        if not self._is_running:
            return
        self._user_stop_requested = True
        self._recovery_requested.clear()
        self._stop_event.set()
        if self._watchdog_stop_event:
            self._watchdog_stop_event.set()
        self._set_stop_button_state(disabled=True)
        print("\n收到停止指令，正在尝试中止运行...")

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

    def _execute_action(self, action, params_widgets, screenshot_dir, loop_index, excel_inputs, excel_step_index, stop_event):
        if action == 'find_and_click':
            image_path_widget = params_widgets.get('image_path')
            if not image_path_widget:
                print("步骤缺少图片路径参数")
                return True

            image_filename = image_path_widget.get().strip()
            if not image_filename:
                print("步骤图片路径为空")
                return True

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
            # 超时参数（可选）
            timeout_enabled_var = params_widgets.get('timeout_enabled')
            timeout_seconds_widget = params_widgets.get('timeout_seconds')
            timeout_val = None
            try:
                enabled = int(timeout_enabled_var.get()) if timeout_enabled_var is not None else 0
            except Exception:
                enabled = 0
            if enabled:
                try:
                    timeout_val = float(timeout_seconds_widget.get() or 0.0) if timeout_seconds_widget else None
                    if timeout_val is not None and timeout_val <= 0:
                        timeout_val = None
                except Exception:
                    timeout_val = None

            find_and_click(
                image_path=full_image_path,
                d_x=d_x,
                d_y=d_y,
                click_times=click_times,
                stop_event=stop_event,
                timeout=timeout_val
            )
            return True

        if action == 'input_text':
            text_widget = params_widgets.get('text')
            if not text_widget:
                print("步骤缺少文本参数")
                return True

            text = text_widget.get().strip()
            if not text:
                print("步骤输入文本为空")
                return True

            input_text(text=text)
            return True

        if action == 'input_from_excel':
            excel_values = None
            if excel_inputs is not None:
                excel_values = excel_inputs.get(excel_step_index)

            if excel_values:
                text = excel_values[loop_index]
                print(f"Excel 输入 -> {text}")
                input_text(text=text)
                return True

            path_widget = params_widgets.get('excel_path')
            if not path_widget:
                print("步骤缺少 Excel 路径参数")
                return True
            excel_path = path_widget.get().strip()
            if not excel_path:
                print("Excel 路径为空")
                return True
            try:
                values = read_excel_first_column(excel_path)
            except Exception as exc:
                print(f"Excel 读取失败: {exc}")
                return False
            if not values:
                print("Excel 文件没有可用数据")
                return False
            input_text(text=values[0])
            return True

        if action == 'move_and_click':
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

            image_path_widget = params_widgets.get('image_path')
            image_path_value = image_path_widget.get().strip() if image_path_widget else ""
            if image_path_value:
                if screenshot_dir and os.path.exists(screenshot_dir):
                    move_image_path = os.path.join(screenshot_dir, image_path_value)
                else:
                    move_image_path = image_path_value
            else:
                move_image_path = None

            move_and_click(
                X=X,
                Y=Y,
                scroll_times=scroll_times,
                scroll_distance=scroll_distance,
                click_times=click_times,
                image_path=move_image_path,
                stop_event=stop_event
            )
            return True

        if action == 'wait':
            seconds_widget = params_widgets.get('seconds')
            if seconds_widget:
                try:
                    seconds = float(seconds_widget.get() or 0)
                except ValueError:
                    seconds = 0.0
            else:
                seconds = 0.0
            wait(seconds)
            return True

        if action == 'run_python':
            env_widget = params_widgets.get('environment_path')
            prog_widget = params_widgets.get('program_path')
            args_widget = params_widgets.get('args')
            program_path = prog_widget.get().strip() if prog_widget else ""
            if not program_path:
                print("步骤程序路径为空")
                return True
            environment_path = env_widget.get().strip() if env_widget else ""
            raw_args = args_widget.get().strip() if args_widget else ""
            if raw_args:
                try:
                    parsed_args = shlex.split(raw_args)
                except ValueError as exc:
                    print(f"脚本参数解析失败 -> {exc}")
                    return False
            else:
                parsed_args = []
            run_python(environment_path=environment_path, program_path=program_path, args=parsed_args)
            return True

        if action == 'simulate_key':
            keys_widget = params_widgets.get('keys')
            if not keys_widget:
                print("步骤缺少按键参数")
                return True

            keys = keys_widget.get().strip()
            if not keys:
                print("按键字符串为空")
                return True

            simulate_key(keys=keys)
            return True

        print(f"未知操作类型 '{action}'")
        return True

    def _start_watchdog(self, hang_timeout):
        if hang_timeout <= 0 or not self.recovery_steps:
            self._watchdog_stop_event = threading.Event()
            self._watchdog_thread = None
            return
        self._watchdog_stop_event = threading.Event()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            args=(hang_timeout,),
            daemon=True
        )
        self._watchdog_thread.start()

    def _stop_watchdog(self):
        if self._watchdog_stop_event:
            self._watchdog_stop_event.set()
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=1.0)
        self._watchdog_thread = None

    def _watchdog_loop(self, hang_timeout):
        while not self._watchdog_stop_event.wait(0.5):
            if not self._is_running or self._user_stop_requested:
                break
            if not self.recovery_steps:
                continue
            if time.time() - self._last_progress_time > hang_timeout:
                self._request_recovery()

    def _request_recovery(self):
        if self._recovery_requested.is_set() or not self.recovery_steps:
            return
        print("\n检测到主流程超时未响应，准备触发副流程...")
        self._recovery_requested.set()
        if not self._user_stop_requested:
            self._stop_event.set()

    def _run_recovery_flow(self, screenshot_dir):
        if not self.recovery_steps:
            return True
        print("\n开始执行吊死副流程...")
        for idx, step in enumerate(self.recovery_steps, 1):
            if self._user_stop_requested:
                print("用户已停止运行，副流程被终止。")
                return False
            action = step['combobox'].get()
            params_widgets = step.get('params_widgets', {})
            print(f"副流程步骤 {idx}: {action}")
            success = self._execute_action(
                action=action,
                params_widgets=params_widgets,
                screenshot_dir=screenshot_dir,
                loop_index=0,
                excel_inputs=None,
                excel_step_index=idx - 1,
                stop_event=self._stop_event
            )
            if not success:
                print(f"副流程步骤 {idx} 执行失败")
                return False
        print("副流程执行完成，返回主流程继续。")
        return True

    def _run_steps_worker(self, screenshot_dir, loop_times):
        stop_requested = False
        hang_timeout = max(self._pending_hang_timeout or 0.0, 0.0)
        self._recovery_requested.clear()
        self._last_progress_time = time.time()
        self._start_watchdog(hang_timeout)
        try:
            excel_inputs = self._prepare_excel_inputs(loop_times)
            for loop_index in range(loop_times):
                if self._stop_event.is_set() and self._user_stop_requested:
                    stop_requested = True
                    break
                print(f"\n开始执行第 {loop_index + 1}/{loop_times} 轮流程")
                step_index = 0
                while step_index < len(self.steps):
                    if self._stop_event.is_set() and self._user_stop_requested:
                        stop_requested = True
                        break

                    if self._recovery_requested.is_set():
                        if self._user_stop_requested:
                            stop_requested = True
                            break
                        self._stop_event.clear()
                        recovered = self._run_recovery_flow(screenshot_dir)
                        self._recovery_requested.clear()
                        if not recovered:
                            stop_requested = True
                            break
                        self._last_progress_time = time.time()
                        # 根据恢复模式决定从哪个步骤继续
                        recovery_mode = self.recovery_mode_var.get()
                        if recovery_mode == "continue_from_selected":
                            # 模式2：从选定的步骤继续
                            selected_step_str = self.recovery_step_combobox.get()
                            if selected_step_str and selected_step_str.startswith("步骤 "):
                                try:
                                    selected_index = int(selected_step_str.replace("步骤 ", "")) - 1
                                    if 0 <= selected_index < len(self.steps):
                                        step_index = selected_index
                                        print(f"副流程执行完成，从选定的步骤 {selected_index + 1} 继续执行（第 {loop_index + 1} 轮循环，使用本次循环的数据）。")
                                    else:
                                        print(f"选定的步骤索引 {selected_index + 1} 无效，从中断位置继续。")
                                except ValueError:
                                    print(f"无法解析选定的步骤 '{selected_step_str}'，从中断位置继续。")
                            else:
                                print("未选择步骤，从中断位置继续。")
                        else:
                            # 模式1：从中断位置继续
                            print(f"副流程执行完成，从中断位置继续执行（第 {loop_index + 1} 轮循环，使用本次循环的数据）。")
                        # continue 会保持 loop_index 和 step_index 不变（或已更新），确保使用本次循环的数据
                        continue

                    step = self.steps[step_index]
                    action = step['combobox'].get()
                    params_widgets = step.get('params_widgets', {})

                    print(f"\n执行步骤 {step_index + 1}: {action}")

                    success = self._execute_action(
                        action=action,
                        params_widgets=params_widgets,
                        screenshot_dir=screenshot_dir,
                        loop_index=loop_index,
                        excel_inputs=excel_inputs,
                        excel_step_index=step_index,
                        stop_event=self._stop_event
                    )

                    if not success:
                        print(f"步骤 {step_index + 1} 执行失败或被中止")

                    if self._stop_event.is_set():
                        if self._user_stop_requested:
                            stop_requested = True
                            break
                        if self._recovery_requested.is_set():
                            continue
                        self._stop_event.clear()

                    self._last_progress_time = time.time()
                    step_index += 1

                if stop_requested:
                    break
        except Exception as exc:
            self._notify_async_error(exc)
            print(f"执行错误: {exc}")
        finally:
            self._stop_watchdog()
            if stop_requested:
                print("\n执行已被用户中止。")
            else:
                print("\n所有轮次执行完成！")
            self.frame.after(0, self._on_run_finished)

    def _notify_async_error(self, exc: Exception):
        self.frame.after(0, lambda: messagebox.showerror("错误", f"执行步骤时发生错误: {str(exc)}"))

    def _on_run_finished(self):
        self._is_running = False
        self._stop_event.clear()
        self._user_stop_requested = False
        self._set_run_button_state(disabled=False)
        self._set_stop_button_state(disabled=True)

    def _set_run_button_state(self, disabled: bool):
        if self.run_button:
            state = tk.DISABLED if disabled else tk.NORMAL
            self.run_button.config(state=state)

    def _set_stop_button_state(self, disabled: bool):
        if self.stop_button:
            state = tk.DISABLED if disabled else tk.NORMAL
            self.stop_button.config(state=state)

if __name__ == "__main__":
    from flow_manager import FlowManager

    root = tk.Tk()
    flow_manager = FlowManager()
    app = Process(root, flow_manager)
    root.geometry("1000x600")
    root.mainloop()

