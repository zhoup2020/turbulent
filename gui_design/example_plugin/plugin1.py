# plugins/sample_plugin.py
import tkinter as tk
from plugin_base import PluginBase

class SamplePlugin(PluginBase):
    name = "示例插件"

    def __init__(self):
        self.host = None
        self.frame = None

    def activate(self, host_api):
        self.host = host_api
        # 这里可以预先注册事件、启动线程等
        print("[SamplePlugin] Activated; files:", self.host.files)

    def deactivate(self):
        # 清理 UI 或后台任务
        self.close_page()
        self.host = None

    def open_page(self, parent, host_api):
        # 弹窗示例：如果想要 Toplevel
        # win = tk.Toplevel(parent)
        # 或者在 parent Frame 中展示
        self.close_page()
        self.frame = tk.Frame(parent, bd=1, relief="solid")
        tk.Label(self.frame, text="主程序 files 列表：").pack(anchor="w", padx=5, pady=2)
        for f in host_api.files:
            tk.Label(self.frame, text=f"- {f}").pack(anchor="w", padx=15)
        btn = tk.Button(self.frame, text="打印加载文件", command=lambda : self.print_info(self.host.files))
        btn.pack(pady=5)
        return self.frame

    def print_info(self,info):
        print(info)

    def close_page(self):
        if self.frame:
            self.frame.destroy()
            self.frame = None