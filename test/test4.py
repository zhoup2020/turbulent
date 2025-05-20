# 用于象限分析可视化
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import string

file = "G:/inldata/ecdata/B1/ec_flux_20210427_0000.dat"
df = pd.read_csv(file,header=None,names=['u','v','w','theta','water','CO2'])
df.index = pd.date_range(start="2021-04-27 00:00:00", periods=len(df), freq='0.1s')
df.replace(-9999.0, np.nan, inplace=True)   # 将数据中的缺测值-9999.0设置为NAN，方便插值
df.interpolate(method='linear')
df = df.ffill()
df = df.bfill()
df = df.dropna()
df_tur = df - df.groupby(pd.Grouper(freq='30min')).transform('mean')

w_stdf = df_tur['w'].resample('30min').std(ddof=0).dropna()
t_stdf = df_tur['theta'].resample('30min').std(ddof=0).dropna()


def PDF(ax, w, t, w_std, vt_std):
    w = w.values
    t = t.values
    # 如果需标准化为u/σu和ω/σω（根据原图示例）
    w_normalized = w / w_std
    t_normalized = t / t_std
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
    contour = ax.contour(X, Y, Z_normalized, levels=levels, colors='k', linewidths=1)
    #     ax.scatter(data_points[0], data_points[1], s=1, alpha=0.3, c='blue')  # 叠加数据点
    return ax


plt.style.use(['classic'])
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['mathtext.fontset'] = 'stix'
times = ["12:00", "12:30", "13:00", "13:30", "14:00", "14:30"]
# 生成时间序列
datetime_list = [f"2021-04-27 {time}" for time in times]
datetime_index = pd.to_datetime(datetime_list)
fig, axes = plt.subplots(2, 3, figsize=(10, 5), sharex=True, sharey=True)
fig.patch.set_facecolor('w')
for ax, w_std, t_std, time_index, i in zip(axes.flat, w_stdf[24:], t_stdf[24:], datetime_index, range(6)):
    j = i + 24
    ax = PDF(ax, df_tur['w'].iloc[j * 18000:(j + 1) * 18000], df_tur['theta'].iloc[j * 18000:(j + 1) * 18000], w_std,
             t_std)
    ax.annotate(f'({string.ascii_lowercase[i]})' + str(time_index), xy=(0.5, 1.05), ha='center',
                xycoords='axes fraction', fontsize=12)
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
plt.show()