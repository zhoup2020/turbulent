import xarray as xr
from tur_dattonc import calculate_corr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import string
H = 0

with xr.open_dataset('G:/inldata/wt_tur.nc') as ds:
    w_large = ds.w_large
    t_large = ds.t_large
    w_small = ds.w_small
    t_small = ds.t_small
    u_fraction = ds.u_fraction
dfwl = pd.DataFrame(w_large.sel(Height=slice(12.8,50.6)).values,columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time.values))
dftl = pd.DataFrame(t_large.sel(Height=slice(12.8,50.6)).values,columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time.values))
dfws = pd.DataFrame(w_small.sel(Height=slice(12.8,50.6)).values,columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time.values))
dfts = pd.DataFrame(t_small.sel(Height=slice(12.8,50.6)).values,columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time.values))
dfuf = pd.DataFrame(u_fraction.sel(Height=slice(12.8,50.6)).values,columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time1.values))

corr_results = calculate_corr(dfwl,dftl,"30min")

# 定义分箱边界和中点
bins = np.arange(0, 1.5, 0.1)  # 分箱边界: [0.0, 0.2, 0.4, ..., 1.4]
bin_centers = (bins[:-1] + bins[1:]) / 2  # 中点: [0.1, 0.3, ..., 1.3]
height = [12.8, 15.8, 23.0, 30.3, 40.2, 50.6]
# 全局样式设置
plt.style.use('default')
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 12
plt.rcParams['mathtext.fontset'] = 'stix'

# 创建子图（2行3列）
fig, axes = plt.subplots(2, 3, figsize=(12, 8), sharey=True, sharex=True)

# 假设 dfuf 和 corr_results 是预定义的DataFrame
for ax, singleheight, i in zip(axes.flat, dfwl.columns, range(6)):
    data1 = pd.DataFrame({'uf': dfuf[singleheight], 'corr': corr_results[singleheight]})
    data1['bin'] = pd.cut(data1['uf'], bins=bins, labels=bin_centers)
    ax.scatter(data1['uf'], data1['corr'], color='red', alpha=0.6, s=20)
    bin_stats = data1.groupby('bin', observed=False).agg(
        mean_y=('corr', 'mean'),
        std_y=('corr', 'std')).reset_index()
    #     bin_stats['bin_center'] = bin_stats['bin'].apply(
    #                                                     lambda interval: (interval.left + interval.right) / 2)
    ax.errorbar(x=bin_stats['bin'],
                y=bin_stats['mean_y'],
                yerr=bin_stats['std_y'],
                fmt='s', color='royalblue',
                ecolor='black', capsize=4)
    # 设置坐标轴范围
    ax.set_xlim(0, 1.4)  # 覆盖全部分箱
    ax.set_ylim(0, 1)
    ax.set_xticks(np.arange(0, 1.5, 0.2))
    #     ax.set_xticks(bin_centers)
    #     ax.set_xticklabels([f"{bin1:.1f}" for bin1 in bin_centers], rotation=0)
    ax.annotate(f'({string.ascii_lowercase[i]}){singleheight} m', xy=(0.5, 1.02), ha='center', xycoords='axes fraction',
                fontsize=12)
# 统一设置坐标轴标签
for ax in axes[1, :]:
    ax.set_xlabel(r'$u_{\ast}$ (m/s)')
for ax in axes[:, 0]:
    ax.set_ylabel('$R_{wT}$')
plt.tight_layout()
plt.show()