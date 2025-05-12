# hello_plugin.py 示例 -------------------------------
import tkinter as tk
from tkinter import ttk
class BasePlugin:
    plugin_name = "未命名插件"
    version = "1.0"

    def __init__(self, app):
        self.app = app

    def setup(self):
        raise NotImplementedError

    def teardown(self):
        pass

class HelloPlugin(BasePlugin):
    plugin_name = "问候插件"
    version = "1.0"

    def setup(self):
        # 添加菜单项
        self.menu = tk.Menu(self.app.menu_bar)
        self.app.menu_bar.add_cascade(label="问候", menu=self.menu)
        self.menu.add_command(label="打招呼", command=self.say_hello)

        # 添加工具栏按钮
        self.btn = ttk.Button(
            self.app.main_frame,
            text="点击问候",
            command=self.say_hello
        )
        self.btn.pack()

    def say_hello(self):
        tk.messagebox.showinfo("问候", "你好，这是一个插件示例！")

    def teardown(self):
        self.btn.destroy()
        self.app.menu_bar.delete("问候")
