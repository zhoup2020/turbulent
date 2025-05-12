import tkinter as tk
from tkinter import ttk
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)


    def show_tip(self, event=None):
        """显示提示"""
        if self.tip_window:
            return
        # 获取鼠标位置
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # 创建顶层窗口
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")

        # 提示内容
        label = ttk.Label(self.tip_window, text=self.text, background="#ffffe0",
                          relief="solid", borderwidth=1, padding=(5, 2))
        label.pack()

    def hide_tip(self, event=None):
        """隐藏提示"""
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None