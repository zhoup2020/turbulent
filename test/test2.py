from tur_dattonc import DataMergerApp
import tur_dattonc
import tkinter as tk

print(tur_dattonc.__version__)
print(tur_dattonc.__author__)
root = tk.Tk()
DataMergerApp(root)
root.mainloop()