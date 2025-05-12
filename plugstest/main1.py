import tkinter as tk
from tkinter import ttk
import importlib
import os
import inspect
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Type


# 插件基础接口 ==============================================
class BasePlugin:
    plugin_name = "未命名插件"
    version = "1.0"

    def __init__(self, app):
        self.app = app

    def setup(self):
        raise NotImplementedError

    def teardown(self):
        pass


# 主程序框架 ================================================
class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("插件化应用")
        self.geometry("800x600")
        self.plugin_manager = PluginManager(self)
        self._init_ui()

    def _init_ui(self):
        self.menu_bar = tk.Menu(self)
        self.configure(menu=self.menu_bar)
        self.plugin_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="插件", menu=self.plugin_menu)
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.status_bar = ttk.Label(self, text="就绪", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def run(self):
        self.plugin_manager.load_plugins()
        self.mainloop()


# 修复后的插件管理器 =========================================
class PluginManager:
    def __init__(self, app):
        self.app = app
        self.plugins = {}

        # 安全获取基础路径
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
        elif '__file__' in globals():
            base_path = Path(__file__).parent
        else:
            base_path = Path(os.getcwd())

        self.plugin_dir = base_path / "plugins"
        self.plugin_dir.mkdir(exist_ok=True)  # 自动创建目录

    def load_plugins(self):
        for file in self.plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{file.stem}", file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj != BasePlugin:
                        plugin = obj(self.app)
                        plugin.setup()
                        self.plugins[file.stem] = plugin
                        self._add_plugin_menu(plugin)
            except Exception as e:
                self.app.status_bar.config(text=f"加载插件失败: {str(e)}")

    # 其他方法保持不变...
    def _add_plugin_menu(self, plugin: BasePlugin):
        """为插件添加管理菜单"""
        menu = tk.Menu(self.app.plugin_menu, tearoff=0)
        menu.add_command(
            label=f"关于{plugin.plugin_name}",
            command=lambda: self._show_plugin_info(plugin)
        )
        menu.add_separator()
        menu.add_command(
            label="卸载",
            command=lambda: self.unload_plugin(plugin)
        )

        self.app.plugin_menu.add_cascade(
            label=plugin.plugin_name,
            menu=menu
        )

    def unload_plugin(self, plugin: BasePlugin):
        """卸载插件"""
        plugin.teardown()
        del self.plugins[plugin.__class__.__name__]
        self.app.status_bar.config(text=f"已卸载插件: {plugin.plugin_name}")

    def _show_plugin_info(self, plugin: BasePlugin):
        """显示插件信息"""
        info = f"名称: {plugin.plugin_name}\n版本: {plugin.version}"
        tk.messagebox.showinfo("插件信息", info)


# 示例插件实现 ==============================================
"""
文件结构：
main_app.py
plugins/
   ├── hello_plugin.py
   └── calculator_plugin.py
"""


if __name__ == "__main__":
    app = MainApplication()
    app.run()