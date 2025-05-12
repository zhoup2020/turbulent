
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

class CalculatorPlugin(BasePlugin):
    plugin_name = "计算器插件"
    version = "2.0"

    def setup(self):
        # 创建计算器面板
        self.frame = ttk.LabelFrame(
            self.app.main_frame,
            text="迷你计算器"
        )
        self.frame.pack(padx=10, pady=10, fill=tk.X)

        # 输入组件
        self.num1 = ttk.Entry(self.frame)
        self.num2 = ttk.Entry(self.frame)
        self.result = ttk.Label(self.frame, text="结果: ")

        # 按钮
        ttk.Button(
            self.frame,
            text="相加",
            command=lambda: self.calculate("+")
        ).grid(row=2, column=0)

        # 布局
        self.num1.grid(row=0, column=0, padx=5)
        self.num2.grid(row=0, column=1, padx=5)
        self.result.grid(row=1, columnspan=2)

    def calculate(self, operator):
        try:
            n1 = float(self.num1.get())
            n2 = float(self.num2.get())
            res = n1 + n2  # 示例只实现加法
            self.result.config(text=f"结果: {res}")
        except ValueError:
            self.result.config(text="输入无效数字")

    def teardown(self):
        self.frame.destroy()