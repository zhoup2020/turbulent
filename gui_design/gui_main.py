import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from Tooltip import Tooltip
import os


def create_gui():
    root = tk.Tk()
    root.title("Turbulent analysis tool 1.0.0")
    root.geometry("1200x800")

    # ==================== 菜单栏 ====================
    menubar = tk.Menu(root)

    # 定义菜单命令函数
    #     def new_project():
    #         os.makedirs(folder_path, exist_ok=True)
    def new_file():
        messagebox.showinfo("Info", "New file created")

    def open_file():
        global selected_files
        selected_files = []
        files = filedialog.askopenfilenames(
            title="Select .dat files", filetypes=((".dat", "*.dat"), (".csv", "*.csv"), ("All files", "*.*")))
        if files:
            selected_files += list(files)  # 改为追加
            update_status(f"Opened {files}")
        for file in selected_files:
            file_listbox.insert(tk.END, f"• {os.path.basename(file)} ({os.path.dirname(file)})\n")

    def save_file():
        file_path = filedialog.asksaveasfilename()
        if file_path:
            with open(file_path, 'w') as f:
                print(1)
            update_status(f"Saved: {file_path}")

    def on_exit():
        print("Cleaning up before exit...")
        root.destroy()

    def show_metrics():
        messagebox.showinfo("Metrics", "Success rate: 98%")

    def update_status(message):
        status_bar.config(text=message)
        root.after(5000, lambda: status_bar.config(text=f"Ready:{message}"))

    # 完整的菜单结构
    menu_items = [
        ("File", [
            ("New", new_file),
            ("Open", open_file),
            ("Save", save_file),
            ("Exit", on_exit)
        ]),
        ("Edit", [
            ("Cut", lambda: root.focus_get().event_generate("<<Cut>>")),
            ("Copy", lambda: root.focus_get().event_generate("<<Copy>>")),
            ("Paste", lambda: root.focus_get().event_generate("<<Paste>>"))
        ]),
        ("View", [
            ("Zoom In", lambda: messagebox.showinfo("Zoom", "Zooming in")),
            ("Zoom Out", lambda: messagebox.showinfo("Zoom", "Zooming out"))
        ]),
        ("Source", [
            ("Show Source", lambda: messagebox.showinfo("Source", "Source code"))
        ]),
        ("Show Sequence", [
            ("Sequence 1", lambda: messagebox.showinfo("Sequence", "Sequence 1 activated")),
            ("Sequence 2", lambda: messagebox.showinfo("Sequence", "Sequence 2 activated"))
        ]),
        ("Tools", [
            ("Options", lambda: messagebox.showinfo("Options", "Settings panel")),
            ("Converter", lambda: messagebox.showinfo("Converter", "Format converter"))
        ]),
        ("Explore", [
            ("Discover", lambda: messagebox.showinfo("Explore", "Discovery mode"))
        ]),
        ("Success", [
            ("Metrics", show_metrics),
            ("Statistics", lambda: messagebox.showinfo("Stats", "Detailed statistics"))
        ]),
        ("Help", [
            ("Documentation", lambda: messagebox.showinfo("Help", "User manual")),
            ("About", lambda: messagebox.showinfo("About", "Project 1.0\nVersion 2024"))
        ])
    ]

    # 创建菜单
    for menu_label, items in menu_items:
        menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=menu_label, menu=menu)
        for item_label, command in items:
            menu.add_command(label=item_label, command=command)
    root.config(menu=menubar)

    # ==================== 侧边栏 ====================
    sidebar = ttk.Frame(root, width=40, relief="sunken")
    sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=1, pady=1)
    sidebar.pack_propagate(False)

    # 侧边栏控件
    img = ImageTk.PhotoImage(Image.open("../icons/sider.png").resize((20, 20)))
    btntitle = ttk.Label(sidebar, image=img)
    btntitle.image = img
    btntitle.pack(pady=1)
    tools = [
        ("New File", new_file),
        ("Open", open_file),
        ("Save", save_file),
        ("Metrics", show_metrics)
    ]
    icons = {
        "New File": ImageTk.PhotoImage(Image.open("../icons/new.png").resize((20, 20))),
        "Open": ImageTk.PhotoImage(Image.open("../icons/open.png").resize((20, 20))),
        "Save": ImageTk.PhotoImage(Image.open("../icons/save.png").resize((20, 20))),
        "Metrics": ImageTk.PhotoImage(Image.open("../icons/metrics.png").resize((20, 20)))
    }

    tooltips = {
        "New File": "新建分析文件 (Ctrl+N)",
        "Open": "打开现有文件 (Ctrl+O)",
        "Save": "保存当前分析 (Ctrl+S)",
        "Metrics": "查看运行指标统计"
    }

    # 紧凑型按钮布局
    for text, cmd in tools:
        btn = ttk.Button(
            sidebar,
            image=icons[text],
            command=cmd,
            width=20,  # 2. 限制按钮宽度
            padding=(0, 2),  # 3. 减少内边距
            compound=tk.CENTER)  # 图标在上方
        btn.pack(fill=tk.X, pady=1)  # 最小化垂直间距
        btn.image = icons[text]
        Tooltip(btn, tooltips[text])
        # ==================== 主内容区 ====================
    # 使用PanedWindow实现可调整分区
    # 外层垂直布局
    outer_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    outer_paned.pack(fill=tk.BOTH, expand=True)

    # 区域一（上半部分）
    frame1 = tk.Frame(outer_paned, bg="lightcoral", width=100, height=300)
    frame1.pack_propagate(False)  # 禁止自动调整大小

    label1 = tk.Label(frame1, text="区域一", bg="lightcoral", fg="white", font=("Arial", 16))
    label1.pack(side=tk.TOP)

    # 文件路径区域容器
    listbox_frame = tk.Frame(frame1)
    listbox_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

    file_listbox = tk.Listbox(listbox_frame, bg="white", fg="black", font=("Arial", 12), height=24, width=30)
    file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, expand=True)
    scrollbar = tk.Scrollbar(listbox_frame, command=file_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    file_listbox.config(yscrollcommand=scrollbar.set)

    # 添加 frame 到主容器
    outer_paned.add(frame1, weight=1)

    # 内层水平布局（包含区域二和三）
    inner_horizontal = ttk.PanedWindow(outer_paned, orient=tk.VERTICAL)
    outer_paned.add(inner_horizontal, weight=3)

    # 区域二（左下，内层垂直上半部分）
    frame2 = tk.Frame(inner_horizontal, bg="lightblue", height=350)
    frame2.pack_propagate(False)
    label2 = tk.Label(frame2, text="区域二", bg="lightblue", font=("Arial", 14))
    label2.pack(expand=True)

    # 区域三（右下，内层垂直下半部分）
    frame3 = tk.Frame(inner_horizontal, bg="lightgreen", height=50)
    frame3.pack_propagate(False)
    label3 = tk.Label(frame3, text="区域三", bg="lightgreen", font=("Arial", 14))
    label3.pack(expand=True)

    inner_horizontal.add(frame2, weight=2)
    inner_horizontal.add(frame3, weight=1)

    # 状态栏
    status_bar = ttk.Label(root, text="Ready", relief="sunken", anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    return root


if __name__ == "__main__":
    window = create_gui()
    window.mainloop()