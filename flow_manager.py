import os


class FlowManager:
    """
    管理当前流程名称及其关联的存储目录。
    """

    def __init__(self, base_dir="flows"):
        self.base_dir = os.path.abspath(base_dir)
        self.current_flow_name = None
        self._listeners = []
        os.makedirs(self.base_dir, exist_ok=True)

    def set_flow_name(self, name: str):
        flow_name = name.strip()
        if not flow_name:
            raise ValueError("流程名称不能为空")
        self.current_flow_name = flow_name
        os.makedirs(self.get_flow_dir(), exist_ok=True)
        os.makedirs(self.get_screenshot_dir(), exist_ok=True)
        self._notify_listeners("flow_changed")

    def set_flow_from_directory(self, directory: str):
        if not directory:
            raise ValueError("请选择有效的流程文件夹")
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            raise ValueError("选择的路径不是有效的文件夹")
        if directory == self.base_dir:
            raise ValueError("请选择具体的流程文件夹，而不是根目录")
        common_base = os.path.commonpath([directory, self.base_dir])
        if common_base != self.base_dir:
            raise ValueError(f"请选择位于 {self.base_dir} 内的流程文件夹")
        flow_name = os.path.basename(directory.rstrip(os.sep))
        self.current_flow_name = flow_name
        os.makedirs(self.get_screenshot_dir(), exist_ok=True)
        self._notify_listeners("flow_changed")

    def has_flow(self) -> bool:
        return bool(self.current_flow_name)

    def get_flow_name(self):
        return self.current_flow_name

    def get_flow_dir(self):
        if not self.current_flow_name:
            return None
        return os.path.join(self.base_dir, self.current_flow_name)

    def get_screenshot_dir(self):
        flow_dir = self.get_flow_dir()
        if not flow_dir:
            return None
        screenshots_dir = os.path.join(flow_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        return screenshots_dir

    def get_json_path(self):
        flow_dir = self.get_flow_dir()
        if not flow_dir:
            return None
        os.makedirs(flow_dir, exist_ok=True)
        return os.path.join(flow_dir, f"{self.current_flow_name}.json")

    def register_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def notify_screenshots_updated(self):
        self._notify_listeners("screenshots_updated")

    def _notify_listeners(self, event):
        for callback in self._listeners:
            callback(event)

