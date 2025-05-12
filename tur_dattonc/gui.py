"""
This python file is a visualization page for converting DAT files to NC files
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re  # 新增正则表达式模块
from tur_dattonc.dat_to_nc import dat_nc
class DataMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DAT文件合并工具")
        self.root.geometry("800x600")

        # 初始化变量
        self.selected_files = []
        self.var_name = tk.StringVar()
        self.var_height = tk.StringVar()  # 新增高度变量
        self.var_start_time = tk.StringVar()  # 新增起始时间变量
        self.var_timestep = tk.StringVar()  # 新增时间步长变量
        # 创建界面组件
        self.create_widgets()

    def create_widgets(self):
        # 文件选择部分
        file_frame = ttk.LabelFrame(self.root, text="1. 选择后缀名为.dat的文件（按照高度从低到高进行选择）")
        file_frame.pack(pady=10, padx=10, fill="x", expand=True)

        # 按钮组
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(side="top", fill="x", padx=5, pady=2)

        ttk.Button(btn_frame, text="添加文件", command=self.select_files).pack(side="left")
        ttk.Button(btn_frame, text="删除选中", command=self.remove_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_files).pack(side="left")
        ttk.Button(btn_frame, text="上移↑", command=lambda: self.move_file(-1)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="下移↓", command=lambda: self.move_file(1)).pack(side="left")

        # 带滚动条的可操作文件列表
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(pady=5, padx=5, fill="both", expand=True)

        self.file_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,  # 允许多选
            height=6
        )
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.file_listbox.xview)
        self.file_listbox.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        # 变量输入部分
        var_frame = ttk.LabelFrame(self.root, text="2. 设置统一变量名（请用','进行隔离，例如u,v,w）")
        var_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(var_frame, text="变量名：").pack(side="left", padx=5)
        ttk.Entry(var_frame, textvariable=self.var_name, width=30).pack(side="left")

        # 处理参数部分（新增部分）
        param_frame = ttk.LabelFrame(self.root, text="3. 设置处理参数")
        param_frame.pack(pady=10, padx=10, fill="x")

        # 高度输入
        ttk.Label(param_frame, text="高度（m）：").grid(row=0, column=0, padx=5, sticky="e")
        ttk.Entry(param_frame, textvariable=self.var_height, width=15).grid(row=0, column=1, padx=5, sticky="w")

        # 起始时间输入
        ttk.Label(param_frame, text="起始时间（YY-MM-DD HH:MM:SS）：").grid(row=0, column=2, padx=5, sticky="e")
        ttk.Entry(param_frame, textvariable=self.var_start_time, width=15).grid(row=0, column=3, padx=5, sticky="w")

        # 频率输入
        ttk.Label(param_frame, text="时间步长（s）：").grid(row=0, column=4, padx=5, sticky="e")
        ttk.Entry(param_frame, textvariable=self.var_timestep, width=15).grid(row=0, column=5, padx=5, sticky="w")

        # 保存路径部分
        save_frame = ttk.LabelFrame(self.root, text="4. 选择保存路径")
        save_frame.pack(pady=10, padx=10, fill="x")

        ttk.Button(save_frame, text="选择文件夹", command=self.select_save_path).pack(side="left", padx=5)
        self.save_path = tk.StringVar()
        ttk.Entry(save_frame, textvariable=self.save_path, width=50).pack(pady=5, padx=5, fill="x")

        # 处理按钮
        ttk.Button(self.root, text="开始处理", command=self.process_files).pack(pady=10)

    # 文件选择
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="选择DAT文件（可跨文件夹多选）",
            filetypes=(("DAT文件", "*.dat"), ("所有文件", "*.*"))
        )
        if files:
            self.selected_files += list(files)
            self.update_file_list()

    def update_file_list(self):
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)
        for idx, file in enumerate(self.selected_files, 1):
            self.file_listbox.insert(tk.END, f"{idx}. {os.path.basename(file)} ({os.path.dirname(file)})")

    def remove_selected(self):
        """删除选中的文件"""
        selected = self.file_listbox.curselection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的文件！")
            return

        # 倒序删除避免索引错位
        for index in reversed(sorted(selected)):
            del self.selected_files[index]
        self.update_file_list()

    def clear_files(self):
        """清空所有文件"""
        self.selected_files.clear()
        self.update_file_list()

    def move_file(self, direction):
        """移动文件位置（direction: -1上移，1下移）"""
        selected = self.file_listbox.curselection()
        if not selected or len(selected) > 1:
            messagebox.showwarning("提示", "请选择单个文件进行调整！")
            return

        index = selected[0]
        new_index = index + direction

        # 检查边界
        if new_index < 0 or new_index >= len(self.selected_files):
            return

        # 交换位置
        self.selected_files[index], self.selected_files[new_index] = \
            self.selected_files[new_index], self.selected_files[index]
        self.update_file_list()
        self.file_listbox.selection_set(new_index)

    def select_save_path(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path.set(path)

    def validate_parameters(self):
        """验证新增参数输入的合法性"""
        heights = self.var_height.get().strip()
        if not heights:
            messagebox.showerror("错误", "请设置高度层（与所选文件个数一致）！")
            return False

        try:
            # 分割并转换为浮点数列表
            height_list = [float(h.strip()) for h in heights.split(',')]
        except ValueError:
            messagebox.showerror("错误", "高度值必须为有效数字！")
            return False

        # 检查高度数量与文件数量是否一致
        if len(height_list) != len(self.selected_files):
            messagebox.showerror("错误",
                                 f"高度层数量（{len(height_list)}）与文件数量（{len(self.selected_files)}）不一致！")
            return False

        # 验证时间格式
        time_pattern = r"^\d{4}-\d{2}-\d{2} ([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$"
        if not re.match(time_pattern, self.var_start_time.get()):
            messagebox.showerror("错误", "时间格式不正确，请使用HH:MM:SS格式！")
            return False

        # 验证时间步长
        try:
            float(self.var_timestep.get())
        except ValueError:
            messagebox.showerror("错误", "频率必须为有效数字！")
            return False

        return True

    def process_files(self):
        # 基础验证
        if not self.selected_files:
            messagebox.showerror("错误", "请先选择DAT文件！")
            return
        if not self.var_name.get():
            messagebox.showerror("错误", "必须指定变量名！")
            return
        if not self.var_height.get():
            messagebox.showerror("错误", "请设置高度层！")
            return
        if not self.save_path.get():
            messagebox.showerror("错误", "请选择保存路径！")
            return

        # 新增参数验证
        if not self.validate_parameters():
            return
        heights = self.var_height.get().strip()
        try:
            # 分割并转换为浮点数列表
            height_list = [float(h.strip()) for h in heights.split(',')]
        except ValueError:
            messagebox.showerror("错误", "高度值必须为有效数字！")
            return False
        # 转换输入的变量成为列表
        variables = self.var_name.get().strip()
        try:
            # 分割并转换为浮点数列表
            var_list = [str(var.strip()) for var in variables.split(',')]
        except ValueError:
            messagebox.showerror("错误", "变量名必须是字符串（形如u,v,w,t,q,c）！")
            return False

        try:
            # 获取所有参数值
            params = {
                "files": self.selected_files,
                "variable": var_list,
                "height": height_list,
                "start_time": self.var_start_time.get(),
                "timestep": float(self.var_timestep.get()),
                "save_path": self.save_path.get()
            }

            # 这里添加实际处理逻辑，示例打印参数
            print("\n处理参数：")
            print(f"选择的文件：{params['files']}")
            print(f"变量名：{params['variable']}")
            print(f"高度：{params['height']} 米")
            print(f"起始时间：{params['start_time']}")
            print(f"采样时间间隔：{params['timestep']} s")
            print(f"保存路径：{params['save_path']}")
            dat_nc(params['files'], params['start_time'][:10], params['timestep'], params['variable'], height_list,
                   params['save_path'])
            messagebox.showinfo("完成", f"成功处理{len(self.selected_files)}个文件！\n参数已生效")
        except Exception as e:
            messagebox.showerror("错误", f"处理过程中发生错误：\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DataMergerApp(root)
    root.mainloop()
