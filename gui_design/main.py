import tkinter as tk
import logging
from class_gui import TurbulentAnalysisApp

# 设置日志文件
LOG_FILENAME = "app.log"
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[
        logging.FileHandler(LOG_FILENAME, encoding='utf-8'),
        logging.StreamHandler()  # optional: also print to console
    ]
)

root = tk.Tk()
app = TurbulentAnalysisApp(root)
root.mainloop()