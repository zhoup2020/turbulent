# 工作区类
import tkinter as tk
from tkinter import ttk
import pandas as pd
from pandastable import Table

class WorkspaceViewer:
    """
    A Tkinter-based workspace viewer for pandas DataFrame variables.
    Displays a list of variables (name and shape) and lets user double-click to inspect contents in a table.

    Usage:
        viewer = WorkspaceViewer(root)
        viewer.update_workspace({'df1': df1, 'df2': df2})
        # Attach viewer.show to a button
    """
    def __init__(self, parent):
        self.parent = parent
        self.vars = {}

    def update_workspace(self, var_dict: dict):
        """Update internal variable dictionary and rebuild list"""
        self.vars = {k: v for k, v in var_dict.items() if isinstance(v, (pd.DataFrame, pd.Series))}

    def show(self):
        """Create and display the workspace window"""
        win = tk.Toplevel(self.parent)
        win.title("Workspace")
        win.geometry("400x300")

        # Treeview for variable list
        cols = ("名称", "形状")
        tree = ttk.Treeview(win, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center')
        tree.pack(fill='both', expand=True)

        # Populate
        for name, obj in self.vars.items():
            shape = obj.shape if hasattr(obj, 'shape') else ()
            tree.insert('', 'end', iid=name, values=(name, shape))

        # Double-click handler
        def on_double(event):
            item = tree.selection()[0]
            self._show_variable(self.vars[item])
        tree.bind('<Double-1>', on_double)

    def _show_variable(self, obj):
        """用 pandastable 显示 DataFrame/Series，带网格线"""
        win = tk.Toplevel(self.parent)
        title = getattr(obj, 'name', '') or 'Data'
        win.title(f"Inspect: {title}")
        win.geometry("800x600")

        frame = ttk.Frame(win)
        frame.pack(fill='both', expand=True)

        # 如果是 Series，先转成 DataFrame
        if isinstance(obj, pd.Series):
            df = obj.to_frame(name=obj.name or "值")
        else:
            df = obj.copy()

        table = Table(frame,
                      dataframe=df,
                      showtoolbar=True,
                      showstatusbar=True)
        table.show()  # 这行会绘制带网格的表格