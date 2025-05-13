# 创建文件树结构
import os
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import shutil


class EnhancedFileTree(ttk.Frame):
    def __init__(self, master, open_callback=None, select_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.current_path = os.getcwd()
        self.history = []
        self.future = []
        self.open_callback = open_callback  # 回调以在外部调用文件打开
        self.select_callback = select_callback  # 回调以在外部选择数据文件
        self._create_ui()
        self._load_icons()
        self._create_context_menu()
        self.update_tree()

        self.tree.bind("<Double-Button-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def _create_ui(self):
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, pady=5)

        self.back_btn = ttk.Button(nav_frame, text="←", width=3, command=self.navigate_back)
        self.forward_btn = ttk.Button(nav_frame, text="→", width=3, command=self.navigate_forward)
        self.up_btn = ttk.Button(nav_frame, text="↑", width=3, command=self.navigate_up)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(nav_frame, textvariable=self.path_var)
        self.browse_btn = ttk.Button(nav_frame, text="浏览...", command=self.browse_folder)

        self.back_btn.pack(side=tk.LEFT, padx=2)
        self.forward_btn.pack(side=tk.LEFT, padx=2)
        self.up_btn.pack(side=tk.LEFT, padx=2)
        self.path_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.browse_btn.pack(side=tk.LEFT)

        self.tree = ttk.Treeview(self, columns=('fullpath', 'type'), show='tree headings')
        self._configure_tree()

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind('<<TreeviewOpen>>', self.on_folder_expand)
        self.path_entry.bind('<Return>', self.on_path_entered)

    def _configure_tree(self):
        self.tree.heading('#0', text='名称')
        self.tree.column('#0', width=300)
        self.tree.heading('type', text='类型')
        self.tree.column('type', width=100)
        style = ttk.Style()
        style.configure('Treeview', rowheight=25)
        style.map('Treeview', background=[('selected', '#0078d4')], foreground=[('selected', 'white')])

    def _load_icons(self):
        self.folder_icon = tk.PhotoImage(file='../icons/folder.png').subsample(12, 12)
        self.file_icon = tk.PhotoImage(file='../icons/file.png').subsample(12, 12)

    def update_tree(self, new_path=None):
        """更新目录树显示"""
        new_path = new_path or self.current_path
        if not os.path.exists(new_path):
            messagebox.showerror("错误", "路径不存在")
            return

        # 更新历史记录
        if self.current_path != new_path:
            self.history.append(self.current_path)
            self.future = []

        self.current_path = new_path
        self.path_var.set(new_path)
        self._update_nav_buttons()

        # 清除旧数据
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 加载新目录
        self._insert_root()

    def _insert_root(self):
        """插入当前路径根节点"""
        root_name = os.path.basename(self.current_path)
        root = self.tree.insert('', 'end',
                                text=root_name,
                                values=(self.current_path, '文件夹'),
                                image=self.folder_icon,
                                open=True)
        self._populate_children(root)

    def _create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="打开", command=self.open_selected)
        self.context_menu.add_command(label="在资源管理器中显示", command=self.reveal_in_explorer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="选择数据文件", command=self._select_data_files)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="新建文件夹", command=self.create_new_folder)
        self.context_menu.add_command(label="新建文件", command=self.create_new_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="重命名", command=self.rename_item)
        self.context_menu.add_command(label="删除", command=self.delete_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="在EnhancedViewer中打开", command=self._open_with_viewer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="刷新", command=self.refresh_tree)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            path = self.tree.item(item, "values")[0]
            if os.path.isdir(path):
                self.open_selected()
            else:
                self.open_file(path)

    def _select_data_files(self):
        """调用外部回调，选择并保存数据文件路径"""
        if self.select_callback:
            self.select_callback()
        else:
            messagebox.showwarning("未设置回调", "无法选择数据文件，请配置 select_callback")

    def _open_with_viewer(self):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.tree.item(selected[0], 'values')[0]
        if self.open_callback:
            self.open_callback(path)
        else:
            from enhanced_viewer import EnhancedFileViewer
            EnhancedFileViewer(self.master, embed=False).load_file(path)

    def open_selected(self):
        for item in self.tree.selection():
            path = self.tree.item(item, "values")[0]
            if os.path.isdir(path):
                self.update_tree(path)
            else:
                self.open_file(path)

    def open_file(self, path):
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开文件: {str(e)}")

    def reveal_in_explorer(self):
        """在文件资源管理器中显示"""
        for item in self.tree.selection():
            path = self.tree.item(item, "values")[0]
            try:
                if platform.system() == "Windows":
                    subprocess.run(f'explorer /select,"{path}"')
                elif platform.system() == "Darwin":
                    subprocess.run(["open", "-R", path])
                else:
                    subprocess.run(["xdg-open", os.path.dirname(path)])
            except Exception as e:
                messagebox.showerror("错误", f"无法打开资源管理器: {str(e)}")

    def create_new_folder(self):
        """创建新文件夹"""
        parent_item = self.tree.selection()[0]
        parent_path = self.tree.item(parent_item, "values")[0]

        new_name = simpledialog.askstring("新建文件夹", "输入文件夹名称:")
        if new_name:
            try:
                new_path = os.path.join(parent_path, new_name)
                os.makedirs(new_path, exist_ok=False)
                self.refresh_tree(parent_item)
            except Exception as e:
                messagebox.showerror("错误", f"创建失败: {str(e)}")

    def create_new_file(self):
        """创建新文件"""
        parent_item = self.tree.selection()[0]
        parent_path = self.tree.item(parent_item, "values")[0]

        new_name = simpledialog.askstring("新建文件", "输入文件名:")
        if new_name:
            try:
                new_path = os.path.join(parent_path, new_name)
                Path(new_path).touch()
                self.refresh_tree(parent_item)
            except Exception as e:
                messagebox.showerror("错误", f"创建失败: {str(e)}")

    def rename_item(self):
        """重命名文件/文件夹"""
        item = self.tree.selection()[0]
        old_path = self.tree.item(item, "values")[0]

        new_name = simpledialog.askstring("重命名", "输入新名称:",
                                          initialvalue=os.path.basename(old_path))
        if new_name:
            try:
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                self.refresh_tree(self.tree.parent(item))
            except Exception as e:
                messagebox.showerror("错误", f"重命名失败: {str(e)}")

    def delete_item(self):
        """删除文件/文件夹"""
        item = self.tree.selection()[0]
        path = self.tree.item(item, "values")[0]

        if messagebox.askyesno("确认删除", f"确定要永久删除 {os.path.basename(path)} 吗？"):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.refresh_tree(self.tree.parent(item))
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")

    def create_zip(self):
        """创建ZIP压缩文件"""
        # 需要实现具体压缩逻辑
        messagebox.showinfo("信息", "创建ZIP功能待实现")

    def add_to_path(self):
        """添加到系统路径"""
        # 需要实现系统路径管理逻辑
        messagebox.showinfo("信息", "添加到路径功能待实现")

    def refresh_tree(self, item=None):
        """刷新目录树"""
        if not item:
            item = self.tree.parent(self.tree.selection()[0]) if self.tree.selection() else ""
        if item:
            self._populate_children(item)
        else:
            self.update_tree(self.current_path)

    def on_folder_expand(self, event):
        """处理文件夹展开事件"""
        item = self.tree.focus()
        if self.tree.item(item, 'values')[1] == '文件夹':
            children = self.tree.get_children(item)
            if children and self.tree.item(children[0])['text'] == '加载中...':
                self.tree.delete(children[0])
                self._populate_children(item)

    def browse_folder(self):
        """打开文件夹选择对话框"""
        path = filedialog.askdirectory(initialdir=self.current_path)
        if path:
            self.update_tree(path)

    def on_path_entered(self, event):
        """处理路径输入事件"""
        path = self.path_var.get().strip()
        if os.path.isdir(path):
            self.update_tree(path)
        else:
            messagebox.showerror("错误", "无效的目录路径")

    def navigate_back(self):
        """导航到上一个目录"""
        if len(self.history) > 0:
            self.future.append(self.current_path)
            self.update_tree(self.history.pop())

    def navigate_forward(self):
        """导航到下一个目录"""
        if len(self.future) > 0:
            self.history.append(self.current_path)
            self.update_tree(self.future.pop())

    def navigate_up(self):
        """返回上级目录"""
        parent = os.path.dirname(self.current_path)
        if os.path.exists(parent):
            self.update_tree(parent)

    def _update_nav_buttons(self):
        """更新导航按钮状态"""
        self.back_btn.state(['!disabled' if len(self.history) > 0 else 'disabled'])
        self.forward_btn.state(['!disabled' if len(self.future) > 0 else 'disabled'])
        self.up_btn.state(['!disabled' if os.path.dirname(self.current_path) else 'disabled'])

    # 修改原_populate_children方法以支持刷新
    def _populate_children(self, parent):
        parent_path = self.tree.item(parent, 'values')[0]
        # 先删除所有子节点
        for child in self.tree.get_children(parent):
            self.tree.delete(child)

        # 重新填充子节点（同原逻辑）
        try:
            entries = sorted(os.scandir(parent_path),
                             key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.name.startswith('.'):
                    continue

                icon = self.folder_icon if entry.is_dir() else self.file_icon
                file_type = '文件夹' if entry.is_dir() else '文件'
                node = self.tree.insert(
                    parent, 'end',
                    text=entry.name,
                    values=(entry.path, file_type),
                    image=icon
                )
                if entry.is_dir():
                    # 添加虚拟子节点用于展开
                    self.tree.insert(node, 'end', text='加载中...')
        except PermissionError:
            messagebox.showwarning("权限不足", f"无法访问: {parent_path}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
