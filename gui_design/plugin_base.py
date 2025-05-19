# plugin_base.py
from abc import ABC, abstractmethod

class PluginBase(ABC):
    @abstractmethod
    def activate(self):
        """激活插件功能，通常这里调用 open_page()"""
        pass

    @abstractmethod
    def deactivate(self):
        """停用插件功能，通常这里调用 close_page()"""
        pass

    @abstractmethod
    def open_page(self, parent):
        """
        在 parent 上打开插件主面板（可以是 Frame、Notebook 插页或 Toplevel）。
        parent: 父容器（如 ttk.Notebook 或某个 Frame）。
        """
        pass

    @abstractmethod
    def close_page(self):
        """
        关闭或销毁插件创建的主面板（Frame 或 Toplevel）。
        """
        pass

    @abstractmethod
    def new_page(self, container, title: str):
        """
        在给定的容器（通常是 ttk.Notebook）内新建一个子页面，并返回它。
        container: ttk.Notebook 实例
        title: 新页面的标题
        """
        pass
