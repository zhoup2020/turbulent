# host_api.py
class HostAPI:
    def __init__(self, app):
        # 直接引用主程序实例或选定属性
        self._app = app

    @property
    def files(self):
        """示例属性，插件可读写"""
        return self._app.selected_files      # 来自主程序:contentReference[oaicite:3]{index=3}

    def data(self):
        return self._app.plot_data
