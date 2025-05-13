# 查看文件结构
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import netCDF4
import os

class EnhancedFileViewer:
    def __init__(self, parent=None, embed=False, show_menu=True, default_file=None, window_size="1000x700"):
        self.parent = parent or tk.Tk()
        self.embed = embed
        self.window_size = window_size
        self._configure_styles()
        if embed:
            if isinstance(self.parent, tk.Tk) and show_menu:
                self._create_menu(self.parent)
            self._create_widgets(self.parent)
        if default_file:
            self.load_file(default_file)

    def _configure_styles(self):
        style = ttk.Style()
        style.configure("Enhanced.Treeview", font=("Segoe UI", 10), rowheight=25,
                        background="#FFFFFF", fieldbackground="#FFFFFF", bordercolor="#CCCCCC")
        style.configure("Enhanced.Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#F0F0F0", relief="flat")
        style.map("Enhanced.Treeview.Heading", background=[("active", "#E0E0E0")])
        style.configure("Enhanced.TNotebook", background="#FFFFFF")
        style.configure("Enhanced.TNotebook.Tab", font=("Segoe UI", 9), padding=[10, 4])

    def _create_menu(self, win):
        menubar = tk.Menu(win)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=win.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        win.config(menu=menubar)

    def _create_widgets(self, win):
        self.notebook = ttk.Notebook(win, style="Enhanced.TNotebook")
        self.notebook.pack(fill="both", expand=True)
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(win, textvariable=self.status_var,
                              relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def open_file(self):
        file_types = [("Data Files", "*.csv;*.xlsx;*.dat;*.nc"),
                      ("Text Files", "*.txt"),
                      ("All Files", "*.*")]
        path = filedialog.askopenfilename(filetypes=file_types)
        if path:
            self.load_file(path)

    def load_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if self.embed:
            notebook = self.notebook
        else:
            win = tk.Toplevel(self.parent)
            win.title(f"Viewer - {os.path.basename(file_path)}")
            win.geometry(self.window_size)
            notebook = ttk.Notebook(win, style="Enhanced.TNotebook")
            notebook.pack(fill="both", expand=True)
            var = tk.StringVar()
            ttk.Label(win, textvariable=var, relief="sunken", anchor="w").pack(side="bottom", fill="x")
            self.status_var = var
        if ext in ('.csv', '.dat', '.xlsx'):
            self._show_tabular_data(notebook, file_path)
        elif ext == '.nc':
            self._show_netcdf_metadata(notebook, file_path)
        else:
            self._show_text_content(notebook, file_path)

    def _show_tabular_data(self, notebook, file_path):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=os.path.basename(file_path))
        tree = ttk.Treeview(frame, show="headings", selectmode="extended", style="Enhanced.Treeview")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        df = pd.read_csv(file_path) if file_path.endswith(('.csv','.dat')) else pd.read_excel(file_path)
        self._populate_table(tree, df)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def _show_netcdf_metadata(self, notebook, file_path):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=os.path.basename(file_path))
        tree = ttk.Treeview(frame, style="Enhanced.Treeview")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        with netCDF4.Dataset(file_path) as ds:
            root = tree.insert('', 'end', text=os.path.basename(file_path), open=True)
            dim_node = tree.insert(root, 'end', text="Dimensions", open=True)
            for n, dim in ds.dimensions.items():
                tree.insert(dim_node, 'end', text=f"{n}: {len(dim)}", tags=('dim',))
            var_node = tree.insert(root, 'end', text="Variables", open=True)
            for v, var in ds.variables.items():
                vid = tree.insert(var_node, 'end', text=f"{v} ({var.dtype})")
                tree.insert(vid, 'end', text=f"Dims: {var.dimensions}")
                tree.insert(vid, 'end', text=f"Shape: {var.shape}")
            attr_node = tree.insert(root, 'end', text="Global Attributes", open=True)
            for a in ds.ncattrs():
                tree.insert(attr_node, 'end', text=f"{a}={repr(getattr(ds,a))}")
        tree.tag_configure('dim', foreground='blue')
        tree.tag_configure('var', foreground='green')
        tree.tag_configure('attr', foreground='purple')

    def _show_text_content(self, notebook, file_path):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=os.path.basename(file_path))
        text = tk.Text(frame, wrap='none')
        vsb = ttk.Scrollbar(frame, orient='vertical', command=text.yview)
        hsb = ttk.Scrollbar(frame, orient='horizontal', command=text.xview)
        text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        text.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        with open(file_path, 'r', encoding='utf-8') as f:
            text.insert('1.0', f.read())
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def _populate_table(self, tree, df):
        tree.delete(*tree.get_children())
        tree['columns'] = list(df.columns)
        for c in df.columns:
            tree.heading(c, text=c, anchor='w')
            tree.column(c, width=max(100, len(c)*10), anchor='w')
        for i, row in enumerate(df.itertuples(index=False)):
            tree.insert('', 'end', values=row,
                        tags=('odd' if i%2 else 'even',))
        tree.tag_configure('odd', background='#F8F8F8')
        tree.tag_configure('even', background='#FFFFFF')

    def _table_context_menu(self, event, tree):
        menu = tk.Menu(tree.master, tearoff=0)
        menu.add_command(label='Copy', command=lambda: self._copy(tree))
        menu.add_command(label='Export CSV', command=lambda: self._export(tree))
        menu.post(event.x_root, event.y_root)

    def _copy(self, tree):
        sel = tree.selection()
        txt = '\n'.join('\t'.join(map(str, tree.item(i)['values'])) for i in sel)
        self.parent.clipboard_clear()
        self.parent.clipboard_append(txt)

    def _export(self, tree):
        df = pd.DataFrame([tree.item(i)['values'] for i in tree.get_children()],
                          columns=tree['columns'])
        p = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if p:
            df.to_csv(p, index=False)
            messagebox.showinfo('Export', f'Saved: {p}')
