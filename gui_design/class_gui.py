import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog,simpledialog
from tkinter.colorchooser import askcolor
from PIL import Image, ImageTk
import os
import platform
import subprocess
import webbrowser
import logging
import numpy as np
import pandas as pd
import string
import re
import xarray as xr
from tkcalendar import DateEntry
from scipy.interpolate import interp1d
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.font_manager as fm
import matplotlib.colors as mpl_colors
from Tooltip import Tooltip
from Firetree import EnhancedFileTree
from Fileviwer import EnhancedFileViewer
from Workspace import WorkspaceViewer
from tur_dattonc import read_single_nc, read_and_merge_ncs, read_single_csv_or_dat, read_and_merge_csvs_or_dats, wavelet_calculate,dat_nc, save_to_nc,calculate_corr,read_datfiles,high_low_freq

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

class TurbulentAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Turbulent analysis tool 1.0.0")
        self.root.geometry("1200x800")

        # 初始化全局状态
        self.selected_files = []
        self.file_listbox = None
        self.form_params = {'datnc': {}, 'corr': {}, 'deltaS': {},
                            'quan': {}, 'imfs': {}, 'wavelet': {},
                            'fit': {}}
        self.params = {'datnc': {}, 'corr': {}, 'deltaS': {},
                       'quan': {}, 'imfs': {}, 'wavelet': {},
                       'fit': {}}
        self.plot_data = {'corr': {}, 'deltaS': {},
                          'quan': {}, 'imfs': {}, 'wavelet': {},
                          'fit': {}}

        # 初始化界面组件
        self._create_menu()
        self._create_sidebar()
        self._create_main_area()
        self._create_status_bar()

    def _create_menu(self):
        """创建菜单系统"""
        menubar = tk.Menu(self.root)

        style = ttk.Style()
        style.configure("TMenu", font=("Arial", 14))

        # 菜单项配置
        menu_config = [
            ("File", [
                ("New", self.new_file),
                ("Open", self.open_file),
                ("Save", self.save_file),
                ("Load", self.load_file),
                ("Exit", self.on_exit)
            ]),
            ("Edit", [
                ("Cut", lambda: self.root.focus_get().event_generate("<<Cut>>")),
                ("Copy", lambda: self.root.focus_get().event_generate("<<Copy>>")),
                ("Paste", lambda: self.root.focus_get().event_generate("<<Paste>>"))
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
            ("Log", [
                ("Open_logs", self.open_log),
                ("Clear_logs", self.clean_logs)
            ]),
            ("Help", [
                ("Documentation", self.open_documentation),
                ("About", lambda: webbrowser.open("https://github.com/zhoup2020/turbulent"))
            ])
        ]

        # 动态创建菜单
        for label, items in menu_config:
            menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label=label, menu=menu)
            for item_label, command in items:
                menu.add_command(label=item_label, command=command)

        self.root.config(menu=menubar)

    def open_otherfile(self, file_path):
        """使用系统默认程序打开文件"""
        try:
            system = platform.system()
            if system == 'Windows':
                os.startfile(file_path)
            elif system == 'Darwin':
                subprocess.call(['open', file_path])
            else:
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            logging.error(f"文件打开失败: {e}")
            messagebox.showerror("错误", f"文件打开失败，详情请查看日志")

    def open_documentation(self):
        """打开用户手册（自动检测PDF或DOCX）"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.getcwd()

        base_name = "基于python的湍流分析工具说明"
        extensions = [".pdf", ".docx"]

        for ext in extensions:
            file_path = os.path.join(base_dir, base_name + ext)
            print("Looking for:", file_path)  # debug
            if os.path.exists(file_path):
                self.open_otherfile(file_path)
                return

        messagebox.showerror("错误", f"未找到用户手册文件\n{base_dir}")

    def clean_logs(self):
        """清空日志文件内容并记录此次操作"""
        try:
            # Truncate the log file
            with open(LOG_FILENAME, 'w', encoding='utf-8'):
                pass
            logging.info("日志已清空")  # this goes to console handler only
            messagebox.showinfo("清空日志", "日志文件已清空。")
        except Exception as e:
            logging.error(f"清空日志失败: {e}")
            messagebox.showerror("错误", "清空日志失败，详情请查看日志。")

    def open_log(self):
        """打开日志文件"""
        log_path = os.path.join(os.getcwd(), LOG_FILENAME)
        if os.path.exists(log_path):
            self.open_otherfile(log_path)
        else:
            logging.error("日志文件不存在，无法打开")
            messagebox.showerror("错误", "未找到日志文件，请先生成日志后再打开。")

    def _create_sidebar(self):
        """创建侧边栏组件"""
        self.sidebar = ttk.Frame(self.root, width=40, relief="sunken")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=1, pady=1)
        self.sidebar.pack_propagate(False)

        # 加载图标资源
        self._load_icons()

        # 创建侧边栏按钮
        self._create_sidebar_buttons()

    def _load_icons(self):
        """加载所有图标资源"""
        try:
            self.icons = {
                "header": self._load_image("../icons/sider.png"),
                "New File": self._load_image("../icons/new.png"),
                "Load": self._load_image("../icons/load.png"),
                "Open": self._load_image("../icons/open.png"),
                "dat_nc": self._load_image("../icons/save.png"),
                "Corr": self._load_image("../icons/metrics.png"),
                "deltaS": self._load_image("../icons/deltaS.png"),
                "quan": self._load_image("../icons/quan.png"),
                "EMD": self._load_image("../icons/EMD.png"),
                "Wavelet": self._load_image("../icons/wavelet.png"),
                "Fit": self._load_image("../icons/fit.png"),
            }
        except Exception as e:
            messagebox.showerror("图标加载错误", f"无法加载图标文件: {str(e)}")
            self.root.destroy()

        # 标题区域
        title_label = ttk.Label(self.sidebar, image=self.icons["header"])
        title_label.image = self.icons["header"]
        title_label.pack(pady=1)

    def _load_image(self, path):
        """加载并缩放图像"""
        return ImageTk.PhotoImage(Image.open(path).resize((20, 20)))

    def _create_sidebar_buttons(self):
        """创建侧边栏功能按钮"""
        button_config = [
            ("New File", self.new_file, "新建分析文件 (Ctrl+N)"),
            ("Load", self.load_file, "加载文件 (Ctrl+O)"),
            ("Open", self.open_file, "打开文件"),
            ("dat_nc", self._create_parameter_form_datnc, "文件转换dat_nc (Ctrl+S)"),
            ("Corr", self._create_parameter_form_corr, "计算相关系数"),
            ("deltaS", self._create_parameter_form_deltaS, r"计算ΔS"),
            ("quan", self._create_parameter_form_quan, "象限分析"),
            ("EMD", self._create_parameter_form_imfs, "EMD分解"),
            ("Wavelet", self._create_parameter_form_wavelet, "小波分析"),
            ("Fit", self._create_parameter_form_fit, "MOST分析")
        ]

        for text, command, tip in button_config:
            self._create_button(
                parent=self.sidebar,
                text=text,
                command=command,
                icon=self.icons[text],
                tooltip=tip
            )

    def _create_button(self, parent, text, command, icon, tooltip):
        """创建带图标的按钮"""
        btn = ttk.Button(
            parent,
            image=icon,
            command=command,
            width=20,
            padding=(0, 2),
            compound=tk.CENTER
        )
        btn.pack(fill=tk.X, pady=1)
        btn.image = icon  # 保持图片引用
        Tooltip(btn, tooltip)

    def _create_main_area(self):
        """创建主工作区"""
        # 使用PanedWindow实现可调整分区
        self.outer_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.outer_paned.pack(fill=tk.BOTH, expand=True)

        # 左侧文件列表区域
        self._create_file_panel()

        # 右侧分析区域
        self._create_analysis_panel()

    def _create_file_panel(self):
        """创建分屏文件列表面板（上方文件列表，下方参数输入）"""
        # 主容器框架
        file_frame = ttk.Frame(self.outer_paned, width=100)
        file_frame.pack_propagate(False)

        # 使用垂直分割容器
        file_paned = ttk.PanedWindow(file_frame, orient=tk.VERTICAL)
        file_paned.pack(fill=tk.BOTH, expand=True)

        # ===== 上部文件列表区域 =====
        self.file_tree = EnhancedFileTree(self.root,
                                          open_callback=lambda path: EnhancedFileViewer(self.root).load_file(path),
                                          select_callback=self.open_file  # 将主类的 open_file 传入
                                          )

        file_paned.add(self.file_tree, weight=3)  # 分配3/4空间

        # ===== 下部参数输入区域 =====
        param_frame = ttk.Frame(file_paned, relief="solid", borderwidth=2)
        param_frame.pack(padx=5, pady=5, fill=tk.X)
        file_paned.add(param_frame, weight=1)  # 分配1/4空间

        # 参数输入标题
        ttk.Label(param_frame, text="初始化参数", font=("Segoe UI Variable", 12)).pack(pady=5, anchor=tk.CENTER)
        self.param_frame = param_frame
        # 参数输入表单
        self.outer_paned.add(file_frame, weight=1)

    def _create_parameter_form_datnc(self):
        """创建datnc参数输入表单"""

        self.clear_form()
        # 使用网格布局对齐控件
        form_frame = ttk.Frame(self.param_frame)
        form_frame.pack(fill=tk.BOTH, padx=10, pady=5)

        # 参数配置
        parameters = [
            ("vars", "Variable names:", "u,v,w,t,q,c"),
            ("d_start", "Start date (YY-MM-DD):", ""),
            ("d_end", "End_date (YY-MM-DD):", ""),
            ("t_start", "Start time (HH:mm:SS):", ""),
            ("t_end", "End time (HH:mm:SS):", ""),
            ("h", "Height (m):", ""),
            ("t_step", "Time step (s):", 0.1),
            ("out_path", "Save file Path:", "")
        ]
        start_row = len(parameters)
        current_params = {}
        for i, (key, label, default) in enumerate(parameters):
            row = start_row + i
            ttk.Label(form_frame, text=label).grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value=default)
            ttk.Entry(form_frame, textvariable=var, width=15).grid(
                row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            if key == 'out_path':
                btn = ttk.Button(
                    form_frame,
                    text="Browse…",
                    command=lambda v=var: self._browse_directory(v)
                )
                btn.grid(row=row, column=2, padx=5, pady=2)
            current_params[key] = var
        self.form_params["datnc"] = current_params
        # 文件保存设置
        option_row = start_row + len(parameters)
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=start_row + len(parameters) + 1, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="合并dat文件保存为nc文件", command=self._create_collect_datncparameter).pack(
            side=tk.LEFT, padx=5)

    def _create_collect_datncparameter(self):
        """应用datnc参数到类变量"""
        time0 = time.time()
        try:
            params_collect = self.form_params['datnc']
            params = {}
            messagebox.showinfo("成功", "参数已保存！")
            params.update({"vars": params_collect["vars"].get().split(','),
                           "d_start": params_collect["d_start"].get(),
                           "d_end": params_collect["d_end"].get(),
                           "t_start": params_collect["t_start"].get(),
                           "t_end": params_collect["t_end"].get(),
                           "h": [float(h.strip()) for h in params_collect["h"].get().split(',')],
                           "t_step": float(params_collect["t_step"].get()),
                           "out_path": params_collect["out_path"].get()
                           })
            print("参数为：", params)
            self.params['datnc'] = params

            dat_nc(self.selected_files, params["d_start"],
                   params['t_step'], params["vars"],
                   params["h"], params["out_path"])
            time1 = time.time()
            self.run_analysis('dat_nc', time0, time1)

        except ValueError as e:
            messagebox.showerror("输入错误", f"数值转换失败: {e}")
            time1 = time.time()
            self.run_analysis('dat_nc', time0, time1, e)
        except Exception as e:
            messagebox.showerror("错误", f"保存参数失败: {e}")
            time1 = time.time()
            self.run_analysis('dat_nc', time0, time1, e)

    def _create_parameter_form_corr(self):
        """创建计算相关系数参数输入表单"""
        self.clear_form()
        form_frame = ttk.Frame(self.param_frame)
        form_frame.pack(fill=tk.BOTH, padx=10, pady=5)

        parameters = [("tur1", "Turbulent variable1", ""),
                      ("tur2", "Turbulent variable2", ""),
                      ("time_seg", "Time_segment(eg xxmin):", "")]

        # 将表单从第 len(parameters)+1 行开始生成
        self._build_form(form_frame, parameters, 'corr', start_row=len(parameters) + 1,
                         command1=self._create_collect_corrparameter,
                         command2=lambda: self.on_save('corr'), command3=lambda: self.show_plot_corr_settings('corr'))

    def _create_collect_corrparameter(self):
        """应用相关系数变量到类变量"""
        time0 = time.time()
        try:
            params_collect = self.form_params['corr']
            params = {}
            messagebox.showinfo("成功", "参数已保存！")
            params.update({"tur1": params_collect["tur1"].get(),
                           "tur2": params_collect["tur2"].get(),
                           "time_seg": params_collect["time_seg"].get()
                           })
            print("参数为：", params)
            self.params['corr'] = params
        except AttributeError as e:
            pass

        try:
            if self.selected_files:
                if len(self.selected_files) == 1:
                    file = self.selected_files[0]
                    if file.endswith('.nc'):
                        # 单个 netCDF 文件，直接读取
                        data1, data2, uf = read_single_nc(file, params['tur1'], params['tur2'])
                        print(data1)
                    elif file.endswith('.csv') or file.endswith('.dat'):
                        # 单个 CSV 或 DAT 文件，直接读取
                        data = read_single_csv_or_dat(file)
                    else:
                        raise ValueError("不支持的文件格式")
                else:
                    if all(f.endswith('.nc') for f in self.selected_files):
                        # 多个 nc 文件，合并后读取
                        data = read_and_merge_ncs(self.selected_files)
                    elif all(f.endswith('.csv') or f.endswith('.dat') for f in self.selected_files):
                        # 多个 CSV 或 DAT 文件，合并后读取
                        data = read_and_merge_csvs_or_dats(self.selected_files)
                    else:
                        raise ValueError("不支持混合格式文件")
                corr = calculate_corr(data1, data2, params["time_seg"])
                self.plot_data['corr'] = {'corr': corr, 'uf': uf}
                time1 = time.time()
                self.run_analysis('calculate_corr', time0, time1)
        except ValueError as e:
            messagebox.showerror("输入错误", f"数值转换失败: {e}")
            time1 = time.time()
            self.run_analysis('calculate_corr', time0, time1, e)
        except Exception as e:
            messagebox.showerror("错误", f"设置参数失败: {e}")
            time1 = time.time()
            self.run_analysis('calculate_corr', time0, time1, e)

    def _create_save_corrfile(self, out_path, fmt):
        df = self.plot_data['corr']['corr']
        try:
            if fmt == '.csv':
                df.to_csv(out_path, index=False)
            elif fmt in (".xls", ".xlsx"):
                df.to_excel(out_path, index=False, engine="openpyxl")
            elif fmt == '.nc':  # nc
                da = xr.DataArray(
                    data=df.values,
                    dims=("time", "height"),
                    coords={"time": df.index, "height": df.columns},
                    name='corr'
                )
                da.to_netcdf(out_path)
            else:
                messagebox.showwarning("未知格式", f"不支持的文件后缀：{fmt}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return

    def _create_parameter_form_deltaS(self):
        """创建deltaS参数输入表单"""
        self.clear_form()
        form_frame = self._make_scrollable_frame(self.param_frame)
        parameters = [("path", "Path:", ""),
                      ("hole", "Holesize:", ""),
                      ("d_start", "Start date (YY-MM-DD):", ""),
                      ("d_end", "End_date (YY-MM-DD):", ""),
                      ("t_start", "Start time (HH:mm:SS):", ""),
                      ("t_end", "End time (HH:mm:SS):", ""),
                      ("timestep", "Timestep (s):", ""),
                      ("d_exclude", "Exclude date:", ""),
                      ("vars", "Variabel name:", ""), ("height", "Height (m):", "")]
        self._build_form(form_frame, parameters, 'deltaS', start_row=0, command1=self._create_collect_deltaSparameter,
                         command2=lambda: self.on_save("deltaS"), command3=lambda: self.show_plot_ds_settings("deltaS"))

    def _create_collect_deltaSparameter(self):
        time0 = time.time()
        try:
            params_collect = self.form_params['deltaS']
            params = {}
            messagebox.showinfo("成功", "参数已保存！")
            for key in ["path", "d_start", "d_end", "t_start", "t_end"]:
                params.update({key: params_collect[key].get()})
            params.update({"hole": float(params_collect["hole"].get()),
                           "timestep": float(params_collect["timestep"].get()),
                           "d_exclude": params_collect["d_exclude"].get().split(','),
                           "vars": params_collect["vars"].get().split(','),
                           "height": [float(h) for h in params_collect["height"].get().split(',')]})
            self.params['deltaS'] = params
        except AttributeError as e:
            time1 = time.time()
            self.run_analysis('calculate_ΔS', time0, time1, e)
            pass

        try:
            ds, cem, icem = read_datfiles(params["path"], params["hole"], params['d_start'], params['d_end'],
                                          params['t_start'], params['t_end'],
                                          params['d_exclude'], params['vars'], params['height'])
            self.plot_data['deltaS'] = {'deltaS': ds, 'CEM': cem, 'ICEM': icem}
            time1 = time.time()
            self.run_analysis('calculate_ΔS', time0, time1)
        except Exception as e:
            time1 = time.time()
            self.run_analysis('calculate_ΔS', time0, time1, e)

    def _create_save_deltaSfile(self, out_path, fmt):
        try:
            data = self.plot_data['deltaS']
            dict_df = {}
            for key in data.keys():
                dict_df.update({key: data[key]})
            df = pd.concat(dict_df, axis=1)
            if fmt == ".csv":
                df.to_csv(out_path, index=False)
            elif fmt in (".xls", ".xlsx"):
                df.to_excel(out_path, index=False, engine="openpyxl")
            elif fmt == '.nc':  # nc
                dict_ds = {}
                for key in data.keys():
                    dict_ds.update({key: xr.DataArray(
                        data=dict_df[key].values,
                        dims=("time", "height"),
                        coords={"time": dict_df[key].index, "height": dict_df[key].columns},
                        name=key
                    )})
                ds = xr.Dataset(dict_ds)
                ds.to_netcdf(out_path)
            else:
                messagebox.showwarning("未知格式", f"不支持的文件后缀：{fmt}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return

    def on_save(self, task_name):
        time0 = time.time()
        file_path = filedialog.asksaveasfilename(
            title="保存文件",
            initialdir=".",
            initialfile="output",
            defaultextension="",  # 让用户自己选扩展名
            filetypes=[
                ("NetCDF 文件", "*.nc"),
                ("CSV 文件", "*.csv"),
                ("Excel 文件", "*.xlsx"),
                ("所有文件", "*.*"),
            ]
        )
        if not file_path:
            return  # 用户取消

        base, ext = os.path.splitext(file_path)
        ext = ext.lower()

        try:
            if task_name == "corr":
                self._create_save_corrfile(file_path, ext)
                tk.messagebox.showinfo("保存成功", f"已成功{task_name}保存任务")

            elif task_name == "deltaS":
                self._create_save_deltaSfile(file_path, ext)
                tk.messagebox.showinfo("保存成功", f"已成功{task_name}保存任务")

            elif task_name == "quan":
                self._create_save_quanfile(file_path, ext)
                tk.messagebox.showinfo("保存成功", f"已成功{task_name}保存任务")

            elif task_name == "imfs":
                self._create_save_imfsfile(file_path, ext)
                tk.messagebox.showinfo("保存成功", f"已成功{task_name}保存任务")

            elif task_name == "wavelet":
                self._create_save_waveletfile(file_path, ext)
                tk.messagebox.showinfo("保存成功", f"已成功{task_name}保存任务")

            elif task_name == "fit":
                self._create_save_fitfile(file_path, ext)
                tk.messagebox.showinfo("保存成功", f"已成功{task_name}保存任务")

            else:
                pass

            time1 = time.time()
            self.run_analysis('save_' + task_name, time0, time1)
        except Exception as e:
            time1 = time.time()
            tk.messagebox.showerror("保存失败", str(e))
            self.run_analysis('save_' + task_name, time0, time1, e)

    def _create_parameter_form_quan(self):
        """创建deltaS参数输入表单"""
        self.clear_form()
        form_frame = self._make_scrollable_frame(self.param_frame)

        parameters = [("vars", "Variable names:", ""), ("time_seg", "Time segment (min):", ""),
                      ("hole", "Holesize:", ""),
                      ("start_time", "Start datetime(YY-MM-DD HH:mm:SS):", ""),
                      ("end_time", "End datetime(YY-MM-DD HH:mm:SS):", ""),
                      ("timestep", "Timestep:", "")]
        self._build_form(form_frame, parameters, 'quan', start_row=len(parameters) + 1,
                         command1=self._create_collect_quanparameter,
                         command2=lambda: self.on_save('quan'), command3=lambda: self.show_plot_quan_settings('quan'))

    def _create_collect_quanparameter(self):
        time0 = time.time()
        try:
            params_collect = self.form_params['quan']
            params = {}
            messagebox.showinfo("成功", "参数已保存！")
            for key in ["time_seg", "timestep", "start_time", "end_time"]:
                params.update({key: params_collect[key].get()})
            params.update({"hole": int(params_collect["hole"].get())})
            params.update({"vars": params_collect["vars"].get().split(',')})
            print("参数为：", params)
            print("收集参数为：", params_collect)
            self.params['quan'] = params
        except AttributeError as e:
            time1 = time.time()
            self.run_analysis('calculate_quan', time0, time1, e)
            pass

        try:
            if len(self.selected_files) == 0:
                messagebox.showerror("未加载文件")
            elif len(self.selected_files) == 1:
                print(1)
                df = pd.read_csv(self.selected_files[0], header=None, names=params["vars"])
            else:
                df_all = [pd.read_csv(selected_file, header=None, names=params["vars"]) for selected_file in
                          self.selected_files]
                df = pd.concat(df_all, axis=1)
            df.index = pd.date_range(start=params["start_time"], periods=len(df.index), freq=params["timestep"])
            df.replace(-9999.0, np.nan, inplace=True)
            df2 = df.copy()
            print(2)
            for col in df.columns:
                mask = df[col].notna()
                f = interp1d(df.index[mask].astype(np.int64), df[col][mask], kind='linear', fill_value='extrapolate')
                df2[col] = f(df.index.astype(np.int64))
            #             df2.interpolate(method='linear')
            #             df2 = df2.ffill()
            #             df2 = df2.bfill()
            df1 = df2.dropna()
            print(df1)
            df_tur = df1 - df1.groupby(pd.Grouper(freq=params["time_seg"])).transform('mean')
            print(3)
            self.plot_data['quan'] = {column: df_tur[column] for column in df_tur.columns}
            self.plot_data['quan'].update({column + "_std": df_tur[column].groupby(
                pd.Grouper(freq=params["time_seg"])).transform(lambda x: x.std(ddof=0)) for column in df_tur.columns})
            time1 = time.time()
            self.run_analysis('calculate_quan', time0, time1)
        except Exception as e:
            time1 = time.time()
            self.run_analysis('calculate_quan', time0, time1, e)

    def _create_save_quanfile(self, out_path, fmt):
        time0 = time.time()
        try:
            data = self.plot_data['quan']
            dict_df = {}
            for key in data.keys():
                dict_df.update({key: data[key]})
            df = pd.concat(dict_df, axis=1)
            if fmt == ".csv":
                df.to_csv(out_path, index=False)
            elif fmt in (".xls", ".xlsx"):
                df.to_excel(out_path, index=False, engine="openpyxl")
            elif fmt == '.nc':  # nc
                dict_ds = {}
                for key in data.keys():
                    dict_ds.update({key: xr.DataArray(
                        data=dict_df[key].values,
                        dims=["time"],
                        coords={"time": dict_df[key].index},
                        name=key)})
                ds = xr.Dataset(dict_ds)
                ds.to_netcdf(out_path)
            else:
                messagebox.showwarning("未知格式", f"不支持的文件后缀：{fmt}")
        except Exception as e:
            time1 = time.time()
            messagebox.showerror("保存失败", str(e))
            self.run_analysis('save_quan', time0, time1, e)
            return

    def _create_parameter_form_imfs(self):
        """创建EMD分解参数输入表单"""
        self.clear_form()
        form_frame = self._make_scrollable_frame(self.param_frame)

        parameters = [("path", "Path:", ""),
                      ("d_start", "Start date (YY-MM-DD):", ""),
                      ("d_end", "End_date (YY-MM-DD):", ""),
                      ("t_start", "Start time (HH:mm:SS):", ""),
                      ("t_end", "End time (HH:mm:SS):", ""),
                      ("timestep", "Timestep (s):", ""),
                      ("timeseg", "Timesegment (xxmin:)", ""),
                      ("d_exclude", "Exclude date:", ""),
                      ("threshold", "Freq threshold:", ""),
                      ("vars", "Variabel name:", ""), ("height", "Height (m):", "")]
        self._build_form(form_frame, parameters, 'imfs', start_row=len(parameters) + 1,
                         command1=self._create_collect_imfsparameter,
                         command2=lambda: self.on_save('imfs'), command3=lambda: self.show_plot_emd_settings('imfs'))

    def _create_collect_imfsparameter(self):
        time0 = time.time()
        try:
            params_collect = self.form_params['imfs']
            params = {}
            messagebox.showinfo("成功", "参数已保存！")
            for key in ["timestep", "timeseg", "d_start", "d_end", "t_start", "t_end", "path"]:
                params.update({key: params_collect[key].get()})
            params.update({"threshold": float(params_collect["threshold"].get())})
            params.update({"d_exclude": params_collect["d_exclude"].get().split(',')})
            params.update({"vars": params_collect["vars"].get().split(',')})
            params.update({"height": [float(h) for h in params_collect["height"].get().split(',')]})
            print("参数为：", params)
            print("收集参数为：", params_collect)
            self.params['imfs'] = params
        except AttributeError as e:
            time1 = time.time()
            self.run_analysis('calculate_imfs', time0, time1, e)
            pass

        try:
            w_large, w_small, t_large, t_small, uf_df = high_low_freq(params['path'], params['d_start'],
                                                                      params['d_end'], params['t_start'],
                                                                      params['t_end'],
                                                                      params['d_exclude'], params['vars'],
                                                                      params['height'], params['threshold'])
            self.plot_data['imfs'].update({'w_high': w_small, 'w_low': w_large, 't_high': t_small, 't_low': t_large})
            time1 = time.time()
            self.run_analysis('calculate_imfs', time0, time1)
        except Exception as e:
            time1 = time.time()
            self.run_analysis('calculate_imfs', time0, time1, e)

    def _create_save_imfsfile(self, out_path, fmt):
        try:
            data = self.plot_data['imfs']
            dict_df = {}
            for key in data.keys():
                dict_df.update({key: data[key]})
            df = pd.concat(dict_df, axis=1)
            if fmt == ".csv":
                df.to_csv(out_path, index=False)
            elif fmt in (".xls", ".xlsx"):
                df.to_excel(out_path, index=False, engine="openpyxl")
            elif fmt == '.nc':  # nc
                dict_ds = {}
                for key in data.keys():
                    dict_ds.update({key: xr.DataArray(
                        data=dict_df[key].values,
                        dims=("time", "height"),
                        coords={"time": data[key].index, "height": data[key].columns},
                        name=key)})
                ds = xr.Dataset(dict_ds)
                ds.to_netcdf(out_path)
            else:
                messagebox.showwarning("未知格式", f"不支持的文件后缀：{fmt}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return

    def _create_parameter_form_wavelet(self):
        """创建小波分析参数输入表单"""
        self.clear_form()
        form_frame = self._make_scrollable_frame(self.param_frame)

        parameters = [("dt_start", "Start datetime(YY:MM:DD HH:mm:ss):", ""), ("vars", "Variable names:", ""),
                      ("height", "Height:", ""), ("timeseg", "Time segment:", ""), ("timestep", "Timestep:", ""),
                      ("waveletvar", 'Wavelet Variable:', ""), ('index1', 'Starting Index:', ""),
                      ('index2', 'Ending Index:', ""),
                      ("scale_res", "Scale resolution:", ""), ("n_scales", "Scales number:", "")]
        self._build_form(form_frame, parameters, 'wavelet', start_row=len(parameters) + 1,
                         command1=self._create_collect_waveletparameter,
                         command2=lambda: self.on_save("wavelet"),
                         command3=lambda: self.show_plot_wavelet_settings('wavelet'))

    def _create_collect_waveletparameter(self):
        time0 = time.time()
        try:
            params_collect = self.form_params['wavelet']
            params = {}
            messagebox.showinfo("成功", "参数已保存！")
            for key in ["timestep", "timeseg", "dt_start", "waveletvar", "index1", "index2"]:
                params.update({key: params_collect[key].get()})
            params.update({"vars": params_collect["vars"].get().split(',')})
            params.update({"scale_res": float(params_collect["scale_res"].get())})
            params.update({"n_scales": int(params_collect["n_scales"].get())})
            params.update({"height": [float(h) for h in params_collect["height"].get().split(',')]})
            self.params['wavelet'] = params
        except AttributeError as e:
            time1 = time.time()
            self.run_analysis('calculate_wavelet', time0, time1, e)
            pass

        def extract_floats(s):
            return [float(num) for num in re.findall(r"[-+]?\d*\.\d+|\d+", s)]

        timestep = extract_floats(params['timestep'])
        try:
            data = None
            if len(self.selected_files) == 0:
                messagebox.showerror('请加载文件')
            elif len(self.selected_files) == 1:
                file = self.selected_files[0]
                if file.endswith('.csv') or file.endswith('.dat'):
                    data = pd.read_csv(self.selected_files[0], header=None, names=params['vars'])
                elif file.endswith('.xlsx'):
                    data = pd.read_excel(self.selected_files[0], names=params['vars'])
                else:
                    messagebox.showwarning("未知格式", "不支持的文件后缀")
                data.replace(-9999.0, np.nan, inplace=True)  # 将数据中的缺测值-9999.0设置为NAN，方便插值
                data.interpolate(method='linear')
                data = data.ffill()
                data = data.bfill()
                data = data.dropna()
                data.index = pd.date_range(start=params['dt_start'], periods=len(data.index), freq=params['timestep'])
                data_tur = data - data.groupby(pd.Grouper(freq=params['timeseg'])).transform('mean')
                print(1)
                print(params['waveletvar'], params['index1'], params['index2'], timestep, params['scale_res'],
                      params['n_scales'])
                period, power, sig95, coi, _ = wavelet_calculate(
                    data_tur[params['waveletvar']].loc[params['index1']:params['index2']], timestep[0],
                    params['scale_res'], params['n_scales'])
                print(2)
                df_power, df_sig95, df_coi = pd.DataFrame(power.T, columns=period), pd.DataFrame(sig95.T,
                                                                                                 columns=period), pd.DataFrame(
                    coi)
                print(3)
                wavelet_result = pd.concat({'power': df_power, 'sig95': df_sig95, 'coi': df_coi}, axis=1)
            else:
                if all(f.endswith('.csv') or f.endswith('.dat') for f in self.selected_files):
                    data_list = [pd.read_csv(f, header=None, names=params['vars']) for f in self.selected_files]
                    datas = []
                    for data1, h in zip(data_list, params['height']):
                        data1.columns = pd.MultiIndex.from_product([[h], data1.columns])
                        datas.append(data1)
                    data = pd.concat(datas, axis=1)
                    data.columns = data.columns.swaplevel(0, 1)
                else:
                    messagebox.showwarning("未知格式", "不支持的文件后缀")
                data.replace(-9999.0, np.nan, inplace=True)  # 将数据中的缺测值-9999.0设置为NAN，方便插值
                data.interpolate(method='linear')
                data = data.ffill()
                data = data.bfill()
                data = data.dropna()
                data.index = pd.date_range(start=params['dt_start'], periods=len(data.index), freq=params['timestep'])
                data_tur = data - data.groupby(pd.Grouper(freq=params['timeseg'])).transform('mean')
                wavelet_results = {}
                for height in params['height']:
                    period, power, sig95, coi, _ = wavelet_calculate(
                        data_tur[params['waveletvar']].loc[params['index1']:params['index2']], timestep[0],
                        params['scale_res'], params['n_scales'])
                    df_power, df_sig95, df_coi = pd.DataFrame(power.T, columns=period), pd.DataFrame(sig95.T,
                                                                                                     columns=period), pd.DataFrame(
                        coi)
                    wavelet_result = pd.concat({'power': df_power, 'sig95': df_sig95, 'coi': df_coi}, axis=1)
                    wavelet_results.update({height: wavelet_result})
                wavelet_result = pd.concat(wavelet_results, axis=0)

            self.plot_data['wavelet'].update({'wavelet_result': wavelet_result})
            time1 = time.time()
            self.run_analysis('calculate_wavelet', time0, time1)
        except Exception as e:
            time1 = time.time()
            self.run_analysis('calculate_wavelet', time0, time1, e)

    def _create_save_waveletfile(self, out_path, fmt):
        try:
            data = self.plot_data['wavelet']
            dict_df = {}
            for key in data.keys():
                dict_df.update({key: data[key]})
            df = pd.concat(dict_df, axis=1)
            if fmt == ".csv":
                df.to_csv(out_path, index=False)
            elif fmt in (".xls", ".xlsx"):
                df.to_excel(out_path, index=False, engine="openpyxl")
            else:
                messagebox.showwarning("未知格式", f"不支持的文件后缀：{fmt}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return

    def _create_parameter_form_fit(self):
        """创建MOST拟合参数输入表单"""
        self.clear_form()
        messagebox.showwarning("暂时不支持该功能，待开发")

    # 设置可滚动的属性输入区域
    def _make_scrollable_frame(self, parent, padding=(10, 5, 10, 5)):
        """创建一个可滚动容器，返回内部的 scrollable_frame."""
        left_pad, top_pad, right_pad, bottom_pad = padding

        # 外层容器
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True,
                       padx=(left_pad, right_pad),
                       pady=(top_pad, bottom_pad))

        # Canvas + Scrollbar
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient="vertical",
                            command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 真正放控件的 Frame
        scrollable_frame = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0),
                                         window=scrollable_frame,
                                         anchor="nw")

        # 1) 内部 frame 大小改变时更新 scrollregion
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", _on_frame_configure)

        # 2) Canvas 大小改变时，让 window 宽度同步，避免横向滚动
        def _on_canvas_resize(event):
            canvas.itemconfigure(window_id, width=event.width)

        canvas.bind("<Configure>", _on_canvas_resize)

        # 3) 绑定鼠标滚轮（跨平台）
        def _on_mousewheel(event):
            if event.delta:  # Windows / MacOS
                canvas.yview_scroll(-1 * (event.delta // 120), "unit")
            elif event.num in (4, 5):  # Linux
                canvas.yview_scroll(-1 if event.num == 4 else 1, "unit")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

        return scrollable_frame

    def _build_form(self, form_frame, parameters, form_key, start_row=0, command1=None, command2=None, command3=None):
        current_params = {}
        for i, (key, label, default) in enumerate(parameters):
            row = start_row + i
            ttk.Label(form_frame, text=label).grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value=default)
            ttk.Entry(form_frame, textvariable=var, width=15).grid(
                row=row, column=1, sticky=tk.EW, padx=5, pady=2)
            if key == 'out_path' or key == 'path':
                btn = ttk.Button(
                    form_frame,
                    text="Browse…",
                    command=lambda v=var: self._browse_directory(v)
                )
                btn.grid(row=row, column=2, padx=5, pady=2)
            current_params[key] = var
        self.form_params[form_key] = current_params

        # 按钮区也放在 start_row + len(parameters)
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=start_row + len(parameters) + 1, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="计算", command=command1).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存文件", command=command2).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="绘图", command=command3).pack(side=tk.LEFT)

    # 文件夹选择
    def _browse_directory(self, target_var: tk.StringVar):
        """弹出文件夹选择框，并把选中的路径写入 target_var"""
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            target_var.set(folder)

    def clear_form(self):
        # 清除表格原先的内容
        for widget in self.param_frame.winfo_children():
            widget.destroy()

    def _create_analysis_panel(self):
        """创建分析显示面板"""
        analysis_paned = ttk.PanedWindow(self.outer_paned, orient=tk.VERTICAL)

        # 可视化分析区
        # ===== 可视化分析区 =====
        self.viz_frame = ttk.Frame(analysis_paned)

        # 创建Matplotlib画布
        self.fig = Figure(figsize=(6, 4), dpi=100)

        # 嵌入Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加工具栏
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.viz_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        analysis_paned.add(self.viz_frame, weight=4)  # 占80%高度
        # 统计信息区
        stats_frame = ttk.Frame(analysis_paned, borderwidth=2, relief='sunken')
        stats_frame.pack_propagate(False)
        analysis_paned.add(stats_frame, weight=1)
        self.outer_paned.add(analysis_paned, weight=3)

        # 区块标题
        title = ttk.Label(stats_frame, text="任务日志", anchor='center', font=("Segoe UI Variable", 12))
        title.pack(fill=tk.X, padx=5, pady=(5, 0))

        # 日志文本 + 滚动条
        self.stats_text = tk.Text(
            stats_frame,
            height=8,
            state=tk.DISABLED,
            wrap=tk.NONE,
            bg='lightgray',
            font=('Consolas', 12)
        )
        self.stats_text.tag_configure('green', foreground='green')
        self.stats_text.tag_configure('red', foreground='red')
        vsb = ttk.Scrollbar(
            stats_frame,
            orient=tk.VERTICAL,
            command=self.stats_text.yview
        )
        self.stats_text.configure(yscrollcommand=vsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

    def log(self, message: str, color: str = "green"):
        """向统计信息区追加一条带时间戳的日志"""
        now = datetime.now().strftime('%H:%M:%S')
        entry = f"[{now} turbulent analysis] {message}\n"
        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.insert(tk.END, entry, color)
        self.stats_text.configure(state=tk.DISABLED)
        self.stats_text.see(tk.END)

    # 示例：分析任务启动与结束时调用
    def run_analysis(self, task_info, t0: float, t1: float, e=None):
        self.log(f"任务 {task_info} 开始")
        elapsed = t1 - t0
        if e is None:
            self.log(f"任务 {task_info} 完成，耗时 {elapsed / 60:.2f} min", "green")
        else:
            self.log(f"任务 {task_info} 未完成，Error:{e}， 耗时 {elapsed / 60:.2f} min", "red")

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief="sunken",
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message=""):
        """更新状态栏信息"""
        self.status_bar.config(text=message)
        self.root.after(500, lambda: self.status_bar.config(text=f"Accomplish:{message}"))
        self.root.after(1000, lambda: self.status_bar.config(text="Ready"))

    def new_file(self):
        """新建分析项目"""
        parent_path = filedialog.askdirectory(title="Select a parent folder")
        new_name = simpledialog.askstring("新建文件夹", "输入文件夹名称:")
        if new_name:
            try:
                new_path = os.path.join(parent_path, new_name)
                os.makedirs(new_path, exist_ok=False)
            except Exception as e:
                messagebox.showerror("错误", f"创建失败: {str(e)}")
        self.update_status("新建分析项目已就绪")

    def load_file(self):
        """打开数据文件并显示可编辑的文件列表窗口"""
        files = filedialog.askopenfilenames(
            title="选择数据文件",
            filetypes=(
                (".dat", "*.dat"),
                (".csv", "*.csv"),
                (".xlsx", "*.xlsx"),
                (".nc", "*.nc"),
                ("All types", "*.*")
            )
        )
        if not files:
            return

        # 更新内部列表
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)

        # 创建/激活窗口
        if not hasattr(self, 'file_window') or not self.file_window.winfo_exists():
            self._build_file_window()

        # 刷新列表框
        self._refresh_listbox()
        self.update_status(f"已加载 {len(self.selected_files)} 个数据文件")

    def _build_file_window(self):
        self.file_window = tk.Toplevel(self.root)
        self.file_window.title("已加载的数据文件")
        self.file_window.geometry("500x350")

        # 列表区
        frame = ttk.Frame(self.file_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox = tk.Listbox(
            frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=vsb.set
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.config(command=self.file_listbox.yview)

        # 控制按钮区
        ctrl = ttk.Frame(self.file_window)
        ctrl.pack(fill=tk.X, pady=5)

        up_btn = ttk.Button(ctrl, text="↑ 上移", width=8, command=self._move_up)
        down_btn = ttk.Button(ctrl, text="↓ 下移", width=8, command=self._move_down)
        del_btn = ttk.Button(ctrl, text="删除选中", width=10, command=self._delete_selected)
        clear_btn = ttk.Button(ctrl, text="清空列表", width=8, command=self._clear_file_list)

        up_btn.pack(side=tk.LEFT, padx=2)
        down_btn.pack(side=tk.LEFT, padx=2)
        del_btn.pack(side=tk.LEFT, padx=2)
        clear_btn.pack(side=tk.RIGHT, padx=2)

    def _refresh_listbox(self):
        """根据 self.selected_files 刷新列表框内容"""
        self.file_listbox.delete(0, tk.END)
        for f in self.selected_files:
            display = f"• {os.path.basename(f)} ({os.path.dirname(f)})"
            self.file_listbox.insert(tk.END, display)

    def _clear_file_list(self):
        """清空所有选中文件"""
        self.selected_files.clear()
        if hasattr(self, 'file_listbox'):
            self.file_listbox.delete(0, tk.END)
        self.update_status("已清空数据文件列表")

    def _delete_selected(self):
        """删除列表中当前选中的文件"""
        sel = list(self.file_listbox.curselection())
        if not sel:
            return
        # 从最后一个索引开始删除，避免索引错乱
        for idx in reversed(sel):
            del self.selected_files[idx]
        self._refresh_listbox()
        self.update_status(f"删除 {len(sel)} 个文件")
        print('删除', self.selected_files)

    def _move_up(self):
        """将选中的文件上移"""
        sel = list(self.file_listbox.curselection())
        if not sel or sel[0] == 0:
            return
        for idx in sel:
            self.selected_files[idx - 1], self.selected_files[idx] = (
                self.selected_files[idx],
                self.selected_files[idx - 1]
            )
        self._refresh_listbox()
        # 重新选中移动后的项目
        for idx in [i - 1 for i in sel]:
            self.file_listbox.selection_set(idx)
        print('上移', self.selected_files)

    def _move_down(self):
        """将选中的文件下移"""
        sel = list(self.file_listbox.curselection())
        n = len(self.selected_files)
        if not sel or sel[-1] == n - 1:
            return
        for idx in reversed(sel):
            self.selected_files[idx], self.selected_files[idx + 1] = (
                self.selected_files[idx + 1],
                self.selected_files[idx]
            )
        self._refresh_listbox()
        # 重新选中移动后的项目
        for idx in [i + 1 for i in sel]:
            self.file_listbox.selection_set(idx)
        print('下移', self.selected_files)

    def open_file(self):
        EnhancedFileViewer(self.root, embed=False).open_file()

    def save_file(self):
        """保存分析结果"""
        path = filedialog.askdirectory()
        if path:
            self.params['Save file path:'] = path

    def show_metrics(self):
        """显示分析指标"""
        metrics_window = tk.Toplevel(self.root)
        metrics_window.title("分析指标")
        ttk.Label(metrics_window, text="实时分析指标监控", font=('Arial', 14)).pack(pady=10)
        # 添加具体指标显示逻辑

    def on_exit(self):
        """退出程序"""
        if messagebox.askokcancel("退出", "确认要退出程序吗？"):
            self.root.destroy()

    # 新增的corr绘图设置方法
    def show_plot_corr_settings(self, task_name):
        """显示绘图属性设置窗口"""
        # 创建设置窗口
        settings_win = tk.Toplevel(self.root)
        settings_win.title("绘图属性设置")

        # 存储设置的变量
        self.plot_settings = {
            'var_x': tk.StringVar(value='请选择'),
            'var_y': tk.StringVar(value='请选择'),
            'drawing_style': tk.StringVar(value='default'),
            'fonts': tk.StringVar(value='Times New Roman'),
            'fontsize': tk.IntVar(value=12),
            'dpi': tk.IntVar(value=100),
            'color': tk.StringVar(value='#FF0000'),
            'marker_size': tk.IntVar(value=8),
            'nrows': tk.IntVar(value=1),
            'ncols': tk.IntVar(value=1),
            'plot_type': tk.StringVar(value='scatter')
        }

        # 获取数据中的变量列表（假设self.df是已加载的DataFrame）

        variables = ['请选择'] + list(self.plot_data[task_name].keys()) if hasattr(self, 'plot_data') else [
            '请选择']  # ["corr","u*","|z/L|"]

        # 创建表单控件
        ttk.Label(settings_win, text="X轴变量:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var_x'],
                               values=variables,
                               state='readonly')
        x_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(settings_win, text="Y轴变量:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        y_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var_y'],
                               values=variables,
                               state='readonly')
        y_combo.grid(row=0, column=3, padx=5, pady=5)

        # 颜色选择
        def choose_color():
            color = askcolor()[1]
            if color:
                self.plot_settings['color'].set(color)

        ttk.Label(settings_win, text="颜色:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(settings_win, textvariable=self.plot_settings['color'], width=7).grid(row=1, column=1, sticky='w')
        ttk.Button(settings_win, text="选择颜色", command=choose_color).grid(row=1, column=2, padx=20)

        # 设置绘图风格
        draw_styles = ['default'] + plt.style.available
        ttk.Label(settings_win, text="绘图风格:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['drawing_style'],
                               values=draw_styles,
                               state='readonly')
        x_combo.grid(row=2, column=1, padx=5, pady=5)

        # 点大小
        ttk.Label(settings_win, text="点大小:").grid(row=2, column=2, padx=5, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=20,
                    textvariable=self.plot_settings['marker_size'],
                    width=5).grid(row=2, column=3, sticky='w')
        # 图形行数
        ttk.Label(settings_win, text="图行数:").grid(row=3, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['nrows'],
                    width=5).grid(row=3, column=1, sticky='w')

        # 图形列数
        ttk.Label(settings_win, text="图列数:").grid(row=3, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['ncols'],
                    width=5).grid(row=3, column=3, sticky='w')

        # 字体类型
        def list_available_fonts():
            """返回Matplotlib可用的所有字体家族名称（去重）"""
            fonts = set()
            for font in fm.fontManager.ttflist:
                fonts.add(font.name)  # 提取字体家族名称
            return sorted(list(fonts))

        fonts = list_available_fonts()
        ttk.Label(settings_win, text="字体类型:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['fonts'],
                               values=fonts,
                               state='readonly')
        x_combo.grid(row=4, column=1, padx=5, pady=5)
        # 字体大小
        ttk.Label(settings_win, text="字体大小:").grid(row=4, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=32,
                    textvariable=self.plot_settings['fontsize'],
                    width=5).grid(row=4, column=3, sticky='w')
        # 清晰度
        ttk.Label(settings_win, text="清晰度:").grid(row=5, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=50, to=1000, increment=50,
                    textvariable=self.plot_settings['dpi'],
                    width=5).grid(row=5, column=1, sticky='w')
        # 绘图类型
        ttk.Label(settings_win, text="绘图类型:").grid(row=6, column=0, padx=5, pady=5, sticky='e')
        plot_types = [('散点图', 'scatter'), ('折线图', 'line'), ('柱状图', 'bar')]
        for i, (text, value) in enumerate(plot_types):
            ttk.Radiobutton(settings_win,
                            text=text,
                            variable=self.plot_settings['plot_type'],
                            value=value).grid(row=6 + i, column=1, sticky='w')

        # 开始绘图按钮
        ttk.Button(settings_win,
                   text="开始绘图",
                   command=lambda: [self._execute_corrplot(task_name), settings_win.destroy()]
                   ).grid(row=9, column=1, pady=10)

    def _execute_corrplot(self, task_name):
        """执行实际绘图操作"""
        # 获取设置参数
        time0 = time.time()
        print(self.plot_settings.items())
        settings = {k: v.get() for k, v in self.plot_settings.items()}

        # 验证参数
        if settings['var_x'] == '请选择' or settings['var_y'] == '请选择':
            messagebox.showerror("错误", "请先选择X轴和Y轴变量")
            return

        # 清除旧图形
        self.fig.clf()
        plt.style.use(settings['drawing_style'])
        plt.rcParams['figure.dpi'] = settings['dpi']
        plt.rcParams['font.family'] = settings['fonts']
        plt.rcParams['font.size'] = settings['fontsize']
        plt.rcParams['mathtext.fontset'] = 'stix'
        self.axes = self.fig.subplots(nrows=settings['nrows'], ncols=settings['ncols'])

        try:
            # 在第一个子图绘制
            self._plot_to_axis_corr(self.axes, settings)

            # 调整布局并刷新
            self.fig.tight_layout()
            self.canvas.draw()
            time1 = time.time()
            self.run_analysis(''.join(['draw_', task_name]), time0, time1)

        except Exception as e:
            messagebox.showerror("绘图错误", f"发生错误: {str(e)}")
            time1 = time.time()
            self.run_analysis('draw_corr', time0, time1, e)

    def _plot_to_axis_corr(self, axes, settings):
        """通用绘图方法"""
        if settings['plot_type'] == 'scatter':
            self.corr_plot(axes, self.plot_data['corr']['uf'], self.plot_data['corr']['corr'], settings['color'])
        else:
            messagebox.showerror("暂不支持使用该功能")

    def corr_plot(self, axes, x, y, color1):
        """绘制两变量之间的相关系数"""
        bins = np.arange(0, 1.5, 0.1)  # 分箱边界: [0.0, 0.2, 0.4, ..., 1.4]
        bin_centers = (bins[:-1] + bins[1:]) / 2  # 中点: [0.1, 0.3, ..., 1.3]

        # 绘制新图形
        for ax, column, i in zip(axes.flat, x.columns, range(6)):
            data1 = pd.DataFrame({'x': x[column], 'y': y[column]})
            data1['bin'] = pd.cut(data1['x'], bins=bins, labels=bin_centers)
            ax.scatter(data1['x'], data1['y'], color=color1, alpha=0.6, s=20)
            bin_stats = data1.groupby('bin', observed=False).agg(
                mean_y=('y', 'mean'),
                std_y=('y', 'std')).reset_index()

            ax.errorbar(x=bin_stats['bin'],
                        y=bin_stats['mean_y'],
                        yerr=bin_stats['std_y'],
                        fmt='s', color='royalblue',
                        ecolor='black', capsize=4)

            #             设置坐标轴范围
            ax.set_xlim(0, 1.4)  # 覆盖全部分箱
            ax.set_ylim(0, 1)
            ax.set_xticks(np.arange(0, 1.5, 0.2))
            ax.set_xticks(bin_centers)
            ax.set_xticklabels([f"{bin1:.1f}" for bin1 in bin_centers], rotation=0)
            ax.annotate(f'({string.ascii_lowercase[i]}){column} m', xy=(0.5, 1.02), ha='center',
                        xycoords='axes fraction', fontsize=12)
        # 统一设置坐标轴标签
        for ax in axes[1, :]:
            ax.set_xlabel(r'$u_{\ast}$ (m/s)')
        for ax in axes[:, 0]:
            ax.set_ylabel('$R_{wT}$')

        # 自动调整布局
        self.fig.tight_layout()

        # 强制刷新画布显示新图形
        self.canvas.draw()

    # 新增的deltaS绘图设置方法
    def show_plot_ds_settings(self, task_name):
        """显示绘图属性设置窗口"""
        # 创建设置窗口
        settings_win = tk.Toplevel(self.root)
        settings_win.title("绘图属性设置")

        # 存储设置的变量
        self.plot_settings = {
            'var1': tk.StringVar(value='请选择'),
            'var2': tk.StringVar(value='请选择'),
            'var3': tk.StringVar(value='请选择'),
            'vary': tk.StringVar(value='请选择'),
            'drawing_style': tk.StringVar(value='default'),
            'fonts': tk.StringVar(value='Times New Roman'),
            'fontsize': tk.IntVar(value=12),
            'dpi': tk.IntVar(value=100),
            'color1': tk.StringVar(value='#FF1F5B'),
            'color2': tk.StringVar(value='#009ADE'),
            'color3': tk.StringVar(value='#AF58BA'),
            'marker_size': tk.IntVar(value=8),
            'nrows': tk.IntVar(value=1),
            'ncols': tk.IntVar(value=1),
            'plot_type': tk.StringVar(value='line')
        }

        # 获取数据中的变量列表（假设self.df是已加载的DataFrame）

        variables = ['请选择'] + list(self.plot_data[task_name].keys()) if hasattr(self, 'plot_data') else [
            '请选择']  # ["corr","u*","|z/L|"]

        # 创建表单控件
        ttk.Label(settings_win, text="变量1:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var1'],
                               values=variables,
                               state='readonly')
        x_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(settings_win, text="变量2:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        y_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var2'],
                               values=variables,
                               state='readonly')
        y_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(settings_win, text="变量3:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        y_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var3'],
                               values=variables,
                               state='readonly')
        y_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(settings_win, text="y变量:").grid(row=1, column=2, padx=5, pady=5, sticky='e')
        y_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['vary'],
                               values=variables,
                               state='readonly')
        y_combo.grid(row=1, column=3, padx=5, pady=5)

        # 颜色选择
        def choose_color():
            color = askcolor()[1]
            if color:
                self.plot_settings['color'].set(color)

        ttk.Label(settings_win, text="line1颜色:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(settings_win, textvariable=self.plot_settings['color1'], width=7).grid(row=2, column=1, sticky='w')
        ttk.Button(settings_win, text="选择颜色", command=choose_color).grid(row=2, column=2, padx=20)

        ttk.Label(settings_win, text="line2颜色:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(settings_win, textvariable=self.plot_settings['color2'], width=7).grid(row=3, column=1, sticky='w')
        ttk.Button(settings_win, text="选择颜色", command=choose_color).grid(row=3, column=2, padx=20)

        ttk.Label(settings_win, text="line3颜色:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(settings_win, textvariable=self.plot_settings['color3'], width=7).grid(row=4, column=1, sticky='w')
        ttk.Button(settings_win, text="选择颜色", command=choose_color).grid(row=4, column=2, padx=20)

        # 设置绘图风格
        draw_styles = ['default'] + plt.style.available
        ttk.Label(settings_win, text="绘图风格:").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['drawing_style'],
                               values=draw_styles,
                               state='readonly')
        x_combo.grid(row=5, column=1, padx=5, pady=5)

        # 点大小
        ttk.Label(settings_win, text="点大小:").grid(row=5, column=2, padx=5, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=20,
                    textvariable=self.plot_settings['marker_size'],
                    width=5).grid(row=5, column=3, sticky='w')
        # 图形行数
        ttk.Label(settings_win, text="图行数:").grid(row=6, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['nrows'],
                    width=5).grid(row=6, column=1, sticky='w')

        # 图形列数
        ttk.Label(settings_win, text="图列数:").grid(row=6, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['ncols'],
                    width=5).grid(row=6, column=3, sticky='w')

        # 字体类型
        def list_available_fonts():
            """返回Matplotlib可用的所有字体家族名称（去重）"""
            fonts = set()
            for font in fm.fontManager.ttflist:
                fonts.add(font.name)  # 提取字体家族名称
            return sorted(list(fonts))

        fonts = list_available_fonts()
        ttk.Label(settings_win, text="字体类型:").grid(row=7, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['fonts'],
                               values=fonts,
                               state='readonly')
        x_combo.grid(row=7, column=1, padx=5, pady=5)
        # 字体大小
        ttk.Label(settings_win, text="字体大小:").grid(row=7, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=32,
                    textvariable=self.plot_settings['fontsize'],
                    width=5).grid(row=7, column=3, sticky='w')
        # 清晰度
        ttk.Label(settings_win, text="清晰度:").grid(row=8, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=50, to=1000, increment=50,
                    textvariable=self.plot_settings['dpi'],
                    width=5).grid(row=8, column=1, sticky='w')
        # 绘图类型
        ttk.Label(settings_win, text="绘图类型:").grid(row=9, column=0, padx=5, pady=5, sticky='e')
        plot_types = [('折线图', 'line'), ('散点图', 'scatter'), ('柱状图', 'bar')]
        for i, (text, value) in enumerate(plot_types):
            ttk.Radiobutton(settings_win,
                            text=text,
                            variable=self.plot_settings['plot_type'],
                            value=value).grid(row=9 + i, column=1, sticky='w')
        # 工作区按钮
        tk.Button(settings_win, text="打开工作区", command=lambda: self.on_click_workspace(task_name)).grid(row=12,
                                                                                                            column=0,
                                                                                                            pady=10)

        # 开始绘图按钮
        ttk.Button(settings_win,
                   text="开始绘图",
                   command=lambda: [self._execute_dsplot(task_name), settings_win.destroy()]
                   ).grid(row=12, column=2, pady=10)

    def _execute_dsplot(self, task_name):
        """执行实际绘图操作"""
        # 获取设置参数
        time0 = time.time()
        print(self.plot_settings.items())
        settings = {k: v.get() for k, v in self.plot_settings.items()}

        # 验证参数
        if settings['var1'] == '请选择' or settings['var2'] == '请选择' or settings['var3'] == '请选择' or settings[
            'vary'] == '请选择':
            messagebox.showerror("错误", "请先选择X轴和Y轴变量")
            return

        # 清除旧图形
        self.fig.clf()
        plt.style.use(settings['drawing_style'])
        plt.rcParams['figure.dpi'] = settings['dpi']
        plt.rcParams['font.family'] = settings['fonts']
        plt.rcParams['font.size'] = settings['fontsize']
        plt.rcParams['mathtext.fontset'] = 'stix'
        self.axes = self.fig.subplots(nrows=settings['nrows'], ncols=settings['ncols'])

        try:
            # 在第一个子图绘制
            self._plot_to_axis_ds(self.axes, settings)
            # 调整布局并刷新
            self.fig.tight_layout()
            self.canvas.draw()
            time1 = time.time()
            self.run_analysis(''.join(['draw_', task_name]), time0, time1)

        except Exception as e:
            messagebox.showerror("绘图错误", f"发生错误: {str(e)}")
            time1 = time.time()
            self.run_analysis('draw_corr', time0, time1, e)

    def _plot_to_axis_ds(self, axes, settings):
        """通用绘图方法"""
        if settings['plot_type'] == 'line':
            self.deltaS_plot(axes, self.plot_data['deltaS'][settings['var1']],
                             self.plot_data['deltaS'][settings['var2']], self.plot_data['deltaS'][settings['var3']],
                             settings['color1'], settings['color2'], settings['color3'])
        else:
            messagebox.showerror("暂不支持使用该功能")

    def deltaS_plot(self, axes, var1, var2, var3, color1, color2, color3):
        for ax, S, CEM, ICEM in zip(axes.flat, var1.values, var2.values, var3.values):
            ax.plot(S, var1.columns, linestyle='--', color=color1, marker="o", markersize=5, markeredgecolor='#FF1F5B',
                    markerfacecolor='none', zorder=0, label=r'$\Delta$S')
            ax.plot(CEM, var2.columns, linestyle='-', color=color2, zorder=2, label='CEM')
            ax.plot(ICEM, var3.columns, linestyle='-', color=color3, zorder=3, label='ICEM')
        for ax in axes[1, :]:
            ax.set_xlabel(R'$\Delta$S$_{0}$', fontsize=12, labelpad=6)
        for ax in axes[:, 0]:
            ax.set_ylabel(r'z (m)', fontsize=12, labelpad=6)
        axes[0, 0].legend(loc="center", bbox_to_anchor=(0.5, 0.85), edgecolor='none', fontsize=8)
        # 自动调整布局
        self.fig.tight_layout()
        # 强制刷新画布显示新图形
        self.canvas.draw()

    # 新增的quan绘图设置方法
    def show_plot_quan_settings(self, task_name):
        """显示绘图属性设置窗口"""
        # 创建设置窗口
        settings_win = tk.Toplevel(self.root)
        settings_win.title("绘图属性设置")

        # 存储设置的变量
        self.plot_settings = {
            'var1': tk.StringVar(value='请选择'),
            'var2': tk.StringVar(value='请选择'),
            'drawing_style': tk.StringVar(value='default'),
            'fonts': tk.StringVar(value='Times New Roman'),
            'fontsize': tk.IntVar(value=12),
            'dpi': tk.IntVar(value=100),
            'color': tk.StringVar(value='#000000'),
            'marker_size': tk.IntVar(value=8),
            'timeidx': tk.IntVar(value=0),
            'nrows': tk.IntVar(value=1),
            'ncols': tk.IntVar(value=1),
            'plot_type': tk.StringVar(value='distribution')
        }

        # 获取数据中的变量列表（假设self.df是已加载的DataFrame）

        variables = ['请选择'] + list(self.plot_data[task_name].keys()) if hasattr(self, 'plot_data') else [
            '请选择']  # ["corr","u*","|z/L|"]

        # 创建表单控件
        ttk.Label(settings_win, text="变量1:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var1'],
                               values=variables,
                               state='readonly')
        x_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(settings_win, text="变量2:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        y_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var2'],
                               values=variables,
                               state='readonly')
        y_combo.grid(row=0, column=3, padx=5, pady=5)

        # 颜色选择
        def choose_color():
            color = askcolor()[1]
            if color:
                self.plot_settings['color'].set(color)

        ttk.Label(settings_win, text="颜色:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(settings_win, textvariable=self.plot_settings['color'], width=7).grid(row=1, column=1, sticky='w')
        ttk.Button(settings_win, text="选择颜色", command=choose_color).grid(row=1, column=2, padx=20)

        # 设置绘图风格
        draw_styles = ['default'] + plt.style.available
        ttk.Label(settings_win, text="绘图风格:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['drawing_style'],
                               values=draw_styles,
                               state='readonly')
        x_combo.grid(row=2, column=1, padx=5, pady=5)

        # 点大小
        ttk.Label(settings_win, text="点大小:").grid(row=2, column=2, padx=5, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=20,
                    textvariable=self.plot_settings['marker_size'],
                    width=5).grid(row=2, column=3, sticky='w')
        # 图形行数
        ttk.Label(settings_win, text="图行数:").grid(row=3, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['nrows'],
                    width=5).grid(row=3, column=1, sticky='w')

        # 图形列数
        ttk.Label(settings_win, text="图列数:").grid(row=3, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['ncols'],
                    width=5).grid(row=3, column=3, sticky='w')

        # 字体类型
        def list_available_fonts():
            """返回Matplotlib可用的所有字体家族名称（去重）"""
            fonts = set()
            for font in fm.fontManager.ttflist:
                fonts.add(font.name)  # 提取字体家族名称
            return sorted(list(fonts))

        fonts = list_available_fonts()
        ttk.Label(settings_win, text="字体类型:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['fonts'],
                               values=fonts,
                               state='readonly')
        x_combo.grid(row=4, column=1, padx=5, pady=5)
        # 字体大小
        ttk.Label(settings_win, text="字体大小:").grid(row=4, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=32,
                    textvariable=self.plot_settings['fontsize'],
                    width=5).grid(row=4, column=3, sticky='w')
        # 清晰度
        ttk.Label(settings_win, text="清晰度:").grid(row=5, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=50, to=1000, increment=50,
                    textvariable=self.plot_settings['dpi'],
                    width=5).grid(row=5, column=1, sticky='w')
        # 绘图开始时刻的索引
        ttk.Label(settings_win, text="绘图时刻:").grid(row=5, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=0, to=48, increment=1,
                    textvariable=self.plot_settings['timeidx'],
                    width=5).grid(row=5, column=3, sticky='w')
        # 绘图类型
        ttk.Label(settings_win, text="绘图类型:").grid(row=6, column=0, padx=5, pady=5, sticky='e')
        plot_types = [('分布图', 'distribution'), ('散点图', 'scatter')]
        for i, (text, value) in enumerate(plot_types):
            ttk.Radiobutton(settings_win,
                            text=text,
                            variable=self.plot_settings['plot_type'],
                            value=value).grid(row=6 + i, column=1, sticky='w')
        # 工作区按钮
        tk.Button(settings_win, text="打开工作区", command=lambda: self.on_click_workspace(task_name)).grid(row=8,
                                                                                                            column=0,
                                                                                                            pady=10)

        # 开始绘图按钮
        ttk.Button(settings_win,
                   text="开始绘图",
                   command=lambda: [self._execute_quanplot(task_name), settings_win.destroy()]
                   ).grid(row=8, column=2, pady=10)

    def _execute_quanplot(self, task_name):
        """执行实际绘图操作"""
        # 获取设置参数
        time0 = time.time()
        print(self.plot_settings.items())
        settings = {k: v.get() for k, v in self.plot_settings.items()}
        print(settings)
        # 验证参数
        if settings['var1'] == '请选择' or settings['var2'] == '请选择':
            messagebox.showerror("错误", "请先选择X轴和Y轴变量")
            return

        # 清除旧图形
        self.fig.clf()
        plt.style.use(settings['drawing_style'])
        plt.rcParams['figure.dpi'] = settings['dpi']
        plt.rcParams['font.family'] = settings['fonts']
        plt.rcParams['font.size'] = settings['fontsize']
        plt.rcParams['mathtext.fontset'] = 'stix'
        self.axes = self.fig.subplots(nrows=settings['nrows'], ncols=settings['ncols'])

        try:
            # 在第一个子图绘制
            self._plot_to_axis_quan(self.axes, settings)
            # 调整布局并刷新
            self.fig.tight_layout()
            self.canvas.draw()
            time1 = time.time()
            self.run_analysis(''.join(['draw_', task_name]), time0, time1)

        except Exception as e:
            messagebox.showerror("绘图错误", f"发生错误: {str(e)}")
            time1 = time.time()
            self.run_analysis('draw_corr', time0, time1, e)

    def _plot_to_axis_quan(self, axes, settings):
        """通用绘图方法"""
        if settings['plot_type'] == 'distribution':
            self.quan_plot(axes, self.plot_data['quan'][settings['var1']], self.plot_data['quan'][settings['var2']],
                           self.plot_data['quan'][settings['var1'] + "_std"],
                           self.plot_data['quan'][settings['var2'] + "_std"], settings["timeidx"],
                           color=settings['color'])
        else:
            messagebox.showerror("暂不支持使用该功能")

    def quan_plot(self, axes, vars1, vars2, vars1_std, vars2_std, timeidx, color='black'):
        def PDF(ax, w, t, color):
            # --- 步骤1: 提取数据并标准化（可选）---
            w_normalized = w.values
            t_normalized = t.values

            data_points = np.vstack([w_normalized, t_normalized])  # 形状为(2, N)

            # --- 步骤2: 动态生成网格 ---
            def get_grid_range(data, buffer_ratio=0.05):
                min_val = np.min(data)
                max_val = np.max(data)
                delta = (max_val - min_val) * buffer_ratio
                return [min_val - delta, max_val + delta]

            x_range = get_grid_range(data_points[0])
            y_range = get_grid_range(data_points[1])

            # 生成网格点（分辨率可调）
            x = np.linspace(x_range[0], x_range[1], 100)
            y = np.linspace(y_range[0], y_range[1], 100)
            X, Y = np.meshgrid(x, y)
            grid_points = np.vstack([X.ravel(), Y.ravel()])

            # --- 步骤3: 计算KDE概率密度 ---
            kde = gaussian_kde(data_points)
            Z = kde(grid_points).reshape(X.shape)

            # 归一化概率密度（总积分为1）
            Z_normalized = Z / Z.sum()

            # --- 步骤4: 确定等高线层级（50%, 20%, 10%）---
            sorted_density = np.sort(Z_normalized.ravel())[::-1]
            cumulative = np.cumsum(sorted_density)
            levels = [sorted_density[np.where(cumulative >= p)[0][0]] for p in [0.5, 0.2, 0.1]]

            # --- 步骤5: 绘制等值线图 ---
            #     ax.contourf(X, Y, Z, levels=10, cmap=cmap)
            contour = ax.contour(X, Y, Z_normalized, levels=levels, colors=color, linewidths=1)
            #     ax.scatter(data_points[0], data_points[1], s=1, alpha=0.3, c='blue')  # 叠加数据点
            return ax

        for i, ax in enumerate(axes.flat):
            ax = PDF(ax, (vars1 / vars1_std).iloc[i * 18000:(i + 1) * 18000],
                     (vars2 / vars2_std).iloc[i * 18000:(i + 1) * 18000], color)
            ax.annotate(f'({string.ascii_lowercase[i]})', xy=(0.5, 1.05), ha='center', xycoords='axes fraction',
                        fontsize=12)
            ax.set_xlim([-2.5, 2.5])
            ax.set_ylim([-2.5, 2.5])
            ax.plot([-2.5, 2.5], [0, 0], color='black', linestyle='-', linewidth=0.5)
            ax.plot([0, 0], [-2.5, 2.5], color='black', linestyle='-', linewidth=0.5)
            #         ax.set_xlim(0.1,0.5)
        for ax in axes[1, :]:
            ax.set_xticks(np.arange(-2, 3, 1))
            ax.set_xlabel('w/$\sigma$$_{w}$')
        for ax in axes[:, 0]:
            ax.set_yticks(np.arange(-2, 3, 1))
            ax.set_ylabel('T/$\sigma$$_{T}$')
        # 自动调整布局
        self.fig.tight_layout()
        # 强制刷新画布显示新图形
        self.canvas.draw()

    # 新增的EMD绘图设置
    def show_plot_emd_settings(self, task_name):
        """显示绘图属性设置窗口"""
        # 创建设置窗口
        settings_win = tk.Toplevel(self.root)
        settings_win.title("绘图属性设置")

        # 存储设置的变量
        self.plot_settings = {
            'var1': tk.StringVar(value='请选择'),
            'var2': tk.StringVar(value='请选择'),
            'drawing_style': tk.StringVar(value='default'),
            'fonts': tk.StringVar(value='Times New Roman'),
            'fontsize': tk.IntVar(value=12),
            'dpi': tk.IntVar(value=100),
            'color1': tk.StringVar(value='#FF1F5B'),
            'color2': tk.StringVar(value='#00CD6C'),
            'marker_size': tk.IntVar(value=8),
            'start_date': tk.StringVar(),
            'end_date': tk.StringVar(),
            'start_time': tk.StringVar(value='12:00:00'),
            'end_time': tk.StringVar(value='12:29:59'),
            'start_layer': tk.IntVar(),
            'end_layer': tk.IntVar(),
            'nrows': tk.IntVar(value=1),
            'ncols': tk.IntVar(value=1),
            'plot_type': tk.StringVar(value='plot')
        }

        # 获取数据中的变量列表（假设self.df是已加载的DataFrame）

        variables = ['请选择'] + list(self.plot_data[task_name].keys()) if hasattr(self, 'plot_data') else [
            '请选择']  # ["corr","u*","|z/L|"]

        # 创建表单控件
        ttk.Label(settings_win, text="小涡变量:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var1'],
                               values=variables,
                               state='readonly')
        x_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(settings_win, text="大涡变量:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        y_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var2'],
                               values=variables,
                               state='readonly')
        y_combo.grid(row=0, column=3, padx=5, pady=5)

        # 颜色选择
        def choose_color():
            color = askcolor()[1]
            if color:
                self.plot_settings['color'].set(color)

        ttk.Label(settings_win, text="颜色1:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(settings_win, textvariable=self.plot_settings['color1'], width=7).grid(row=1, column=1, sticky='w')
        ttk.Button(settings_win, text="选择颜色", command=choose_color).grid(row=1, column=2, padx=20)

        ttk.Label(settings_win, text="颜色2:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        ttk.Entry(settings_win, textvariable=self.plot_settings['color2'], width=7).grid(row=2, column=1, sticky='w')
        ttk.Button(settings_win, text="选择颜色", command=choose_color).grid(row=2, column=2, padx=20)

        # 设置绘图风格
        draw_styles = ['default'] + plt.style.available
        ttk.Label(settings_win, text="绘图风格:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['drawing_style'],
                               values=draw_styles,
                               state='readonly')
        x_combo.grid(row=3, column=1, padx=5, pady=5)

        # 点大小
        ttk.Label(settings_win, text="点大小:").grid(row=3, column=2, padx=5, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=20,
                    textvariable=self.plot_settings['marker_size'],
                    width=5).grid(row=3, column=3, sticky='w')
        # 图形行数
        ttk.Label(settings_win, text="图行数:").grid(row=4, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['nrows'],
                    width=5).grid(row=4, column=1, sticky='w')

        # 图形列数
        ttk.Label(settings_win, text="图列数:").grid(row=4, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['ncols'],
                    width=5).grid(row=4, column=3, sticky='w')

        # 字体类型
        def list_available_fonts():
            """返回Matplotlib可用的所有字体家族名称（去重）"""
            fonts = set()
            for font in fm.fontManager.ttflist:
                fonts.add(font.name)  # 提取字体家族名称
            return sorted(list(fonts))

        fonts = list_available_fonts()
        ttk.Label(settings_win, text="字体类型:").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['fonts'],
                               values=fonts,
                               state='readonly')
        x_combo.grid(row=5, column=1, padx=5, pady=5)
        # 字体大小
        ttk.Label(settings_win, text="字体大小:").grid(row=5, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=32,
                    textvariable=self.plot_settings['fontsize'],
                    width=5).grid(row=5, column=3, sticky='w')
        # 清晰度
        ttk.Label(settings_win, text="清晰度:").grid(row=6, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=50, to=1000, increment=50,
                    textvariable=self.plot_settings['dpi'],
                    width=5).grid(row=6, column=1, sticky='w')
        # 起始日期
        ttk.Label(settings_win, text="绘图起始日期:") \
            .grid(row=7, column=0, padx=5, pady=5, sticky='e')
        DateEntry(settings_win,
                  textvariable=self.plot_settings['start_date'],
                  date_pattern='yyyy-MM-dd',  # 格式：年-月-日
                  year=2021, month=4, day=25,  # 默认值
                  width=12) \
            .grid(row=7, column=1, sticky='w')

        # 结束日期
        ttk.Label(settings_win, text="绘图结束日期:") \
            .grid(row=7, column=2, padx=5, pady=5, sticky='e')
        DateEntry(settings_win,
                  textvariable=self.plot_settings['end_date'],
                  date_pattern='yyyy-MM-dd',
                  year=2021, month=4, day=25,
                  width=12) \
            .grid(row=7, column=3, sticky='w')

        # 起始时间
        ttk.Label(settings_win, text="起始时间 (HH:mm:ss):") \
            .grid(row=8, column=0, sticky='e', padx=5, pady=5)
        ttk.Entry(settings_win,
                  textvariable=self.plot_settings['start_time'],
                  width=8) \
            .grid(row=8, column=1, sticky='w')

        # 结束时间
        ttk.Label(settings_win, text="结束时间 (HH:mm:ss):") \
            .grid(row=8, column=2, sticky='e', padx=5, pady=5)
        ttk.Entry(settings_win,
                  textvariable=self.plot_settings['end_time'],
                  width=8) \
            .grid(row=8, column=3, sticky='w')

        # 绘图的铁塔起始层
        ttk.Label(settings_win, text="起始层:").grid(row=9, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=0, to=100,
                    textvariable=self.plot_settings['start_layer'],
                    width=5).grid(row=9, column=1, sticky='w')

        # 绘图的铁塔终点层
        ttk.Label(settings_win, text="终点层:").grid(row=9, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=0, to=100,
                    textvariable=self.plot_settings['end_layer'],
                    width=5).grid(row=9, column=3, sticky='w')

        # 绘图类型
        ttk.Label(settings_win, text="绘图类型:").grid(row=10, column=0, padx=5, pady=5, sticky='e')
        plot_types = [('折线图 ', 'plot'), ('散点图', 'scatter')]
        for i, (text, value) in enumerate(plot_types):
            ttk.Radiobutton(settings_win,
                            text=text,
                            variable=self.plot_settings['plot_type'],
                            value=value).grid(row=10 + i, column=1, sticky='w')
        # 工作区按钮
        tk.Button(settings_win, text="打开工作区", command=lambda: self.on_click_workspace(task_name)).grid(row=12,
                                                                                                            column=0,
                                                                                                            pady=10)

        # 开始绘图按钮
        ttk.Button(settings_win,
                   text="开始绘图",
                   command=lambda: [self._execute_emdplot(task_name), settings_win.destroy()]
                   ).grid(row=12, column=2, pady=10)

    def _execute_emdplot(self, task_name):
        """执行实际绘图操作"""
        # 获取设置参数
        time0 = time.time()
        print(self.plot_settings.items())
        settings = {k: v.get() for k, v in self.plot_settings.items()}
        print(settings)
        # 验证参数
        if settings['var1'] == '请选择' or settings['var2'] == '请选择':
            messagebox.showerror("错误", "请先选择X轴和Y轴变量")
            return

        # 清除旧图形
        self.fig.clf()
        plt.style.use(settings['drawing_style'])
        plt.rcParams['figure.dpi'] = settings['dpi']
        plt.rcParams['font.family'] = settings['fonts']
        plt.rcParams['font.size'] = settings['fontsize']
        plt.rcParams['mathtext.fontset'] = 'stix'
        self.axes = self.fig.subplots(nrows=settings['nrows'], ncols=settings['ncols'])

        try:
            # 在第一个子图绘制
            self._plot_to_axis_emd(self.axes, settings)
            # 调整布局并刷新
            self.fig.tight_layout()
            self.canvas.draw()
            time1 = time.time()
            self.run_analysis(''.join(['draw_', task_name]), time0, time1)

        except Exception as e:
            messagebox.showerror("绘图错误", f"发生错误: {str(e)}")
            time1 = time.time()
            self.run_analysis('draw_corr', time0, time1, e)

    def _plot_to_axis_emd(self, axes, settings):
        """通用绘图方法"""
        if settings['plot_type'] == 'plot':
            self.emd_plot(axes, self.plot_data['imfs'][settings['var1']], self.plot_data['imfs'][settings['var2']],
                          settings['color1'],
                          settings['color2'], " ".join([settings['start_date'], settings['start_time']]),
                          " ".join([settings['end_date'],
                                    settings['end_time']]), settings['start_layer'], settings['end_layer'],
                          settings['nrows'])
        else:
            messagebox.showerror("暂不支持使用该功能")

    def emd_plot(self, axes, vars1, vars2, color1, color2, start, end, layer1, layer2, row):
        time = np.arange(0, 1800, 0.1)
        data1, data2 = vars1.loc[start:end].iloc[:, layer1:layer2], vars2.loc[start:end].iloc[:, layer1:layer2]
        axes = np.atleast_2d(axes)
        for ax, column1, column2 in zip(axes.flat, data1.columns, data2.columns):
            ax.plot(time, data1[column1], color=color1, label='Small eddy')
            ax.plot(time, data2[column2], color=color2, label='Large eddy')
            ax.set_xticks(np.arange(0, 1801, 300))
            ax.legend(loc='best')
        for ax in axes[row - 1, :]:
            ax.set_xlabel('Time')
        for ax in axes[:, 0]:
            ax.set_ylabel('signal')
        # 自动调整布局
        self.fig.tight_layout()
        # 强制刷新画布显示新图形
        self.canvas.draw()

    # 新增的wavelet绘图设置
    def show_plot_wavelet_settings(self, task_name):
        """显示绘图属性设置窗口"""
        # 创建设置窗口
        settings_win = tk.Toplevel(self.root)
        settings_win.title("绘图属性设置")

        # 存储设置的变量
        self.plot_settings = {
            'var': tk.StringVar(value='请选择'),
            'drawing_style': tk.StringVar(value='default'),
            'fonts': tk.StringVar(value='Times New Roman'),
            'fontsize': tk.IntVar(value=12),
            'dpi': tk.IntVar(value=100),
            'colorbar': tk.StringVar(value=''),
            'marker_size': tk.IntVar(value=8),
            'nrows': tk.IntVar(value=1),
            'ncols': tk.IntVar(value=1),
            'plot_type': tk.StringVar(value='contourf')
        }

        # 获取数据中的变量列表（假设self.df是已加载的DataFrame）

        variables = ['请选择'] + list(self.plot_data[task_name].keys()) if hasattr(self, 'plot_data') else [
            '请选择']  # ["corr","u*","|z/L|"]

        # 创建表单控件
        ttk.Label(settings_win, text="小波分析变量:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['var'],
                               values=variables,
                               state='readonly')
        x_combo.grid(row=0, column=1, padx=5, pady=5)

        # 颜色条选择
        ttk.Label(settings_win, text="选择颜色条:").grid(row=1, column=0, padx=5, pady=5, sticky='e')

        # 用于显示颜色调名称的输入框
        self.color_entry = ttk.Entry(settings_win, textvariable=self.plot_settings['colorbar'], width=20)
        self.color_entry.grid(row=1, column=1, padx=20)

        # 颜色选择按钮
        ttk.Button(settings_win, text="选择颜色调色板", command=self.show_color_palette).grid(row=1, column=2, padx=20)

        # 设置绘图风格
        draw_styles = ['default'] + plt.style.available
        ttk.Label(settings_win, text="绘图风格:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['drawing_style'],
                               values=draw_styles,
                               state='readonly')
        x_combo.grid(row=2, column=1, padx=5, pady=5)

        # 点大小
        ttk.Label(settings_win, text="点大小:").grid(row=2, column=2, padx=5, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=20,
                    textvariable=self.plot_settings['marker_size'],
                    width=5).grid(row=2, column=3, sticky='w')
        # 图形行数
        ttk.Label(settings_win, text="图行数:").grid(row=3, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['nrows'],
                    width=5).grid(row=3, column=1, sticky='w')

        # 图形列数
        ttk.Label(settings_win, text="图列数:").grid(row=3, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=4,
                    textvariable=self.plot_settings['ncols'],
                    width=5).grid(row=3, column=3, sticky='w')

        # 字体类型
        def list_available_fonts():
            """返回Matplotlib可用的所有字体家族名称（去重）"""
            fonts = set()
            for font in fm.fontManager.ttflist:
                fonts.add(font.name)  # 提取字体家族名称
            return sorted(list(fonts))

        fonts = list_available_fonts()
        ttk.Label(settings_win, text="字体类型:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        x_combo = ttk.Combobox(settings_win,
                               textvariable=self.plot_settings['fonts'],
                               values=fonts,
                               state='readonly')
        x_combo.grid(row=4, column=1, padx=5, pady=5)
        # 字体大小
        ttk.Label(settings_win, text="字体大小:").grid(row=4, column=2, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=1, to=32,
                    textvariable=self.plot_settings['fontsize'],
                    width=5).grid(row=4, column=3, sticky='w')
        # 清晰度
        ttk.Label(settings_win, text="清晰度:").grid(row=5, column=0, padx=0, pady=5, sticky='e')
        ttk.Spinbox(settings_win,
                    from_=50, to=1000, increment=50,
                    textvariable=self.plot_settings['dpi'],
                    width=5).grid(row=5, column=1, sticky='w')

        # 绘图类型
        ttk.Label(settings_win, text="绘图类型:").grid(row=9, column=0, padx=5, pady=5, sticky='e')
        plot_types = [('等值线图 ', 'contourf'), ('散点图', 'scatter')]
        for i, (text, value) in enumerate(plot_types):
            ttk.Radiobutton(settings_win,
                            text=text,
                            variable=self.plot_settings['plot_type'],
                            value=value).grid(row=9 + i, column=1, sticky='w')
        # 工作区按钮
        tk.Button(settings_win, text="打开工作区", command=lambda: self.on_click_workspace(task_name)).grid(row=11,
                                                                                                            column=0,
                                                                                                            pady=10)

        # 开始绘图按钮
        ttk.Button(settings_win,
                   text="开始绘图",
                   command=lambda: [self._execute_waveletplot(task_name), settings_win.destroy()]
                   ).grid(row=11, column=2, pady=10)

    def on_mouse_wheel(self, event):
        # 确保self.canvas存在且未销毁
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            # 滚动事件：滚动鼠标时，滚动canvas
            if event.delta > 0:
                self.canvas.yview_scroll(-1, "units")  # 向上滚动
            else:
                self.canvas.yview_scroll(1, "units")  # 向下滚动
        else:
            print("Canvas no longer exists or has been destroyed.")

    def show_color_palette(self):
        # 打开调色板窗口
        palette_win = tk.Toplevel()
        palette_win.title("选择颜色调色板")
        palette_win.geometry("800x600")  # 设置窗口初始尺寸

        # 创建Canvas和Scrollbar
        self.canvas1 = tk.Canvas(palette_win)  # 使用 self.canvas，避免 AttributeError
        scrollbar = tk.Scrollbar(palette_win, orient="vertical", command=self.canvas1.yview)
        scrollable_frame = ttk.Frame(self.canvas1)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas1.configure(scrollregion=self.canvas1.bbox("all"))
        )

        self.canvas1.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas1.config(yscrollcommand=scrollbar.set)

        # 配置布局权重
        palette_win.grid_rowconfigure(0, weight=1)
        palette_win.grid_columnconfigure(0, weight=1)

        # 放置滚动条和Canvas
        self.canvas1.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 获取matplotlib调色板列表
        cmap_names = plt.colormaps()

        # 每个调色板显示为颜色条+名称，三列布局
        num_columns = 3
        row, col = 0, 0

        for cmap_name in cmap_names:
            cmap = plt.get_cmap(cmap_name)
            color_band = np.linspace(0, 1, 256)

            # --- 颜色名称标签（放在颜色条上方）---
            name_label = tk.Label(
                scrollable_frame,
                text=cmap_name,
                anchor="center",
                width=25  # 增加宽度避免文字截断
            )
            name_label.grid(
                row=row, column=col,
                padx=5, pady=(5, 0),  # pady=(上间距, 下间距)
                sticky="ew"
            )

            # --- 颜色条Canvas ---
            color_bar = tk.Canvas(
                scrollable_frame,
                height=20,
                width=250  # 加宽颜色条
            )
            color_bar.grid(
                row=row + 1, column=col,  # 名称在row，颜色条在row+1
                padx=5, pady=(0, 10),  # 底部留更多间距
                sticky="ew"
            )

            # 绘制颜色渐变
            for j, color_value in enumerate(color_band):
                color = cmap(color_value)
                color_hex = mpl_colors.rgb2hex(color[:3])
                color_bar.create_line(j, 0, j + 1, 20, fill=color_hex)

            # 绑定点击事件
            color_bar.bind(
                "<Button-1>",
                lambda event, cmap_name=cmap_name: self.choose_color(cmap_name)
            )

            # 更新行列索引
            col += 1
            if col == num_columns:
                col = 0
                row += 2  # 每行包含名称和颜色条，因此+2

        # 配置滚动区域权重
        scrollable_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # 绑定鼠标滚轮事件
        self.canvas1.bind_all("<MouseWheel>", self.on_mouse_wheel)

        # 添加关闭事件时，移除Canvas绑定
        palette_win.protocol("WM_DELETE_WINDOW", lambda: self.on_close_palette(palette_win))

    def on_close_palette(self, palette_win):
        # 在关闭窗口时解除事件绑定
        if hasattr(self, 'canvas') and self.canvas1.winfo_exists():
            self.canvas1.unbind_all("<MouseWheel>")  # 移除滚动事件绑定
        palette_win.destroy()  # 销毁窗口

    def choose_color(self, cmap_name):
        # 更新颜色调名称
        self.plot_settings['colorbar'].set(cmap_name)  # 更新颜色调名称

    def _execute_waveletplot(self, task_name):
        """执行实际绘图操作"""
        # 获取设置参数
        time0 = time.time()
        print(self.plot_settings.items())
        settings = {k: v.get() for k, v in self.plot_settings.items()}
        print(settings)
        # 验证参数
        if settings['var'] == '请选择':
            messagebox.showerror("错误", "请先选择X轴和Y轴变量")
            return

        # 清除旧图形
        self.fig.clf()
        plt.style.use(settings['drawing_style'])
        plt.rcParams['figure.dpi'] = settings['dpi']
        plt.rcParams['font.family'] = settings['fonts']
        plt.rcParams['font.size'] = settings['fontsize']
        plt.rcParams['mathtext.fontset'] = 'stix'
        self.axes = self.fig.subplots(nrows=settings['nrows'], ncols=settings['ncols'])

        try:
            # 在第一个子图绘制
            self._plot_to_axis_wavelet(self.axes, settings)
            # 调整布局并刷新
            self.fig.tight_layout()
            self.canvas.draw()
            time1 = time.time()
            self.run_analysis(''.join(['draw_', task_name]), time0, time1)

        except Exception as e:
            messagebox.showerror("绘图错误", f"发生错误: {str(e)}")
            time1 = time.time()
            self.run_analysis('draw_corr', time0, time1, e)

    def _plot_to_axis_wavelet(self, axes, settings):
        """通用绘图方法"""
        if settings['plot_type'] == 'contourf':
            self.wavelet_plot(axes, self.plot_data['wavelet'][settings['var']], settings['colorbar'])
        else:
            messagebox.showerror("暂不支持使用该功能")

    def wavelet_plot(self, ax, var, color1):
        t = np.arange(0, 1800, 0.1)
        dt = 0.1
        period = var['power'].columns
        power, sig95, coi = var['power'].T, var['sig95'].T, var['coi'].T.values[0]
        levels = np.linspace(-4, 4, 101)
        c = ax.contourf(t, np.log2(period), np.log2(power), levels, extend='both', cmap=plt.get_cmap(color1))
        extent = [t.min(), t.max(), 0, max(period)]
        ax.contour(t, np.log2(period), sig95, [-99, 1], colors='k', linewidths=0.5,
                   extent=extent)
        ax.fill(np.concatenate([t, t[-1:] + dt, t[-1:] + dt,
                                t[:1] - dt, t[:1] - dt]),
                np.concatenate([np.log2(coi), [1e-9], np.log2(period[-1:]),
                                np.log2(period[-1:]), [1e-9]]),
                'k', alpha=0.3, hatch='x')
        ax.set_xlim(0, 1800)
        ax.set_ylim(-2, 10)
        ax.set_xticks(np.arange(0, 1801, 300))
        ax.set_yticks(np.arange(-2, 11, 2), [0.25, 1, 4, 16, 64, 256, 1024])
        cax = self.fig.add_axes([0.93, 0.2, 0.012, 0.6])
        bar = self.fig.colorbar(c, ax=ax, cax=cax)
        bar.ax.set_yticks([-4, -2, 0, 2, 4])
        bar.set_label(r'Wavelet power (2$^{n}$)', fontsize=10, labelpad=3)
        # 自动调整布局
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        # 强制刷新画布显示新图形
        self.canvas.draw()

    # 新增的MOST绘图设置

    # 打开工作区
    def on_click_workspace(self, task_info):
        viewer = WorkspaceViewer(self.root)
        viewer.update_workspace(self.plot_data[task_info])
        viewer.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = TurbulentAnalysisApp(root)
    root.mainloop()