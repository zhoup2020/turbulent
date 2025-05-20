# plugin_base.py
from abc import ABC, abstractmethod

class PluginBase(ABC):
    @abstractmethod
    def activate(self, host_api):
        """插件被加载时调用，host_api 暴露主程序接口"""
        pass

    @abstractmethod
    def deactivate(self):
        """插件被卸载或关闭时调用，用来清理资源"""
        pass

    @abstractmethod
    def open_page(self, parent, host_api):
        """
        当用户点击列表项时调用，parent 是主程序的展示容器（Frame）
        host_api 可以让插件访问主程序任意公开接口
        """
        pass

    @abstractmethod
    def close_page(self):
        """当需要关闭插件 UI 时调用"""
        pass

