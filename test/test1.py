import glob
from tur_dattonc import read_datfiles,custom_sort_key
import pandas as pd
import matplotlib.pyplot as plt

paths = 'G:/inldata/ecdata/*'
deltaS_dataframe, CEM_dataframe, ICEM_dataframe = read_datfiles(paths, 0,'2021-04-27', '2021-04-28',
                                                                    '10:00:00','16:00:00',
                                                                    ['2021-05-06', '2021-05-07', '2021-06-07',
                                                                     '2021-06-17', '2021-04-30'],
                                                                    ['u', 'v', 'w', 't', 'water', 'CO2'],
                                                                    [1.2,2.0,3.5,6.0,8.2,12.8,15.8,23.0,30.3,40.2,50.6,60.5])

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['figure.dpi'] = 200
plt.rcParams['font.size'] = 12
plt.rcParams['mathtext.fontset'] = 'stix'
dates = ["2021-04-27", "2021-04-28"]
times = ["12:00", "12:30", "13:00", "13:30"]
# 生成时间序列
datetime_list = [f"{date} {time}" for date in dates for time in times]
datetime_index = pd.to_datetime(datetime_list)
height = [1.2,2.0,3.5,6.0,8.2,12.8,15.8,23.0,30.3,40.2,50.6,60.5]
fig,axes = plt.subplots(2,4,figsize=(10,8),sharey=True)
for ax,S,CEM,ICEM,time_index in zip(axes.flat,deltaS_dataframe.values,CEM_dataframe.values,ICEM_dataframe.values,datetime_index):
        ax.plot(S,height,linestyle = '--',color='#FF1F5B',marker = "o",markersize=5,markeredgecolor='#FF1F5B',markerfacecolor='none',zorder=0,label=r'$\Delta$S')
        ax.plot(CEM,height,linestyle = '-',color='#009ADE',zorder=2,label='CEM')
        ax.plot(ICEM,height,linestyle = '-',color='#AF58BA',zorder=3,label='ICEM')
        ax.annotate(time_index, xy=(0.5, 1.02),ha='center',xycoords='axes fraction', fontsize=12)

for ax in axes[1,:]:
    ax.set_xlabel(R'$\Delta$S$_{0}$',fontsize=12,labelpad=6)
for ax in axes[:,0]:
    ax.set_ylabel(r'z (m)',fontsize=12,labelpad=6)
axes[0,0].legend(loc="center",bbox_to_anchor=(0.75, 0.85),edgecolor='none',fontsize=8)
plt.show()

