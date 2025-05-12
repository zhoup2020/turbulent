import numpy as np
import pandas as pd
import glob
import time
from tur_dattonc.Quadrant_analysis import quan

def read_datfiles(paths, hole,start_date, end_date, start_time,end_time,exclude_dates, vars_list,height):
    dates = pd.date_range(start=start_date, end=end_date)
    exclude_dates = exclude_dates  # Date of missing data
    exclude_dates = pd.to_datetime(exclude_dates)
    dates = dates[~dates.isin(exclude_dates)]  # Excluding missing dates
    dates1 = dates.strftime('%m%d').tolist()
    dates2 = dates.strftime('%m-%d').tolist()
    # Pre-listing of each variable
    deltas_all, m12_all, m21_all, cem_all, icem_all, wp2_all, wu_all = [], [], [], [], [], [], []
    for path in paths:
        # read data
        time1 = time.time()
        df_dataframe = []  # Pre-list used when filtering data
        for date,date1,date2 in zip(dates,dates1,dates2):
            try:
                filename = ''.join(['/ec_flux_2021', date1, '_0000.dat'])
                file = ''.join([path, filename])
                df = pd.read_csv(file, header=None)
                df.columns = vars_list
                df.index = pd.date_range(start=date, periods=len(df), freq='0.1s')
                # Filter out data between 10 and 16 hours and fill in missing values
                df_sel = df[(df.index >= pd.to_datetime(' '.join([start_date[:5] + date2,start_time]))) & (
                            df.index < pd.to_datetime(' '.join([start_date[:5] + date2,end_time])))][['u', 'v', 'w', 't']]
                df_sel.replace(-9999.0, np.nan, inplace=True)  # 将数据中的缺测值-9999.0设置为NAN，方便插值
                df_sel.interpolate(method='linear')
                df_sel = df_sel.ffill()
                df_sel = df_sel.bfill()
                df_sel = df_sel.dropna()
                df_dataframe.append(df_sel)
            except FileNotFoundError as e:
                print(e)
                #         print(f'不存在 2021-{date1}的数据')
                continue
        df_dataframe = pd.concat(df_dataframe, axis=0)
        # 计算方差以及位温的平均值
        means = df_dataframe.groupby(pd.Grouper(freq='30min')).agg(
            mean_t=('t', lambda x: x.mean()),
            mean_u=('u', lambda x: x.mean()),
            mean_v=('v', lambda x: x.mean())).dropna()
        # 计算扰动值以及标准差
        df_means = df_dataframe.groupby(pd.Grouper(freq='30min')).transform('mean')
        df_tur = df_dataframe - df_means
        stds = df_tur.groupby(pd.Grouper(freq='30min')).agg(
            std_w=('w', lambda x: x.std(ddof=0)),
            std_t=('t', lambda x: x.std(ddof=0))).dropna()
        # Calculate the mean value of the temperature flux, and the mean value of the temperature perturbation squared
        wt = pd.DataFrame({'wt': df_tur['w'] * df_tur['t']})
        wt_mean = wt.resample('30min').mean().dropna()
        wu_mean = pd.DataFrame({'wu': df_tur['w'] * df_tur['u']}).resample('30min').mean().dropna()
        t2 = pd.DataFrame({'t2': df_tur['t'] ** 2})
        t2mean = t2.resample('30min').mean().dropna()
        wp2mean = pd.DataFrame({'wp2': df_tur['w'] ** 2}).resample('30min').mean().dropna()

        # After this,a quadrant transformation is formed
        wt_judge = wt.groupby(pd.Grouper(freq='30min')).transform('mean')
        condition_judge = wt_judge['wt'] > 0
        t_tran = (-df_tur['t']).where(condition_judge, df_tur['t'])
        mixing_moment = pd.DataFrame({'wtt': df_tur['w'] * t_tran ** 2,
                                      'wwt': t_tran * df_tur['w'] ** 2})
        mixing_moment_mean = mixing_moment.groupby(pd.Grouper(freq='30min')).agg(
            wtt=('wtt', lambda x: x.mean()),
            wwt=('wwt', lambda x: x.mean())).dropna()
        wt_singleness = (t_tran * df_tur['w']).resample('30min').mean().dropna()

        # Solving deltaS from mixed moments and third-order moments
        r = wt_singleness / (stds['std_w'] * stds['std_t'])
        three_moments = pd.DataFrame({'w3': df_tur['w'] ** 3,
                                      't3': t_tran ** 3})
        three_moments_mean = three_moments.groupby(pd.Grouper(freq='30min')).agg(
            w3=('w3', lambda x: x.mean()),
            t3=('t3', lambda x: x.mean())).dropna()
        m03 = three_moments_mean['w3'] / (stds['std_w'] ** 3)
        m30 = three_moments_mean['t3'] / (stds['std_t'] ** 3)
        m21 = mixing_moment_mean['wtt'] / (stds['std_w'] * (stds['std_t'] ** 2))
        m12 = mixing_moment_mean['wwt'] / (stds['std_t'] * (stds['std_w'] ** 2))
        c11 = (1 + r) * ((m03 - m30) / 6 + (m21 - m12) / 2)
        c22 = -((2 - r) * (m03 - m30) / 6 + (m21 - m12) / 2)
        gamma = m21 / m12 - 1

        # Calculating Sweeps and Ejections flux and time fraction
        # Quadrants III and I,II and IV
        wt_mean_30min = (df_tur['w'] * t_tran).groupby(pd.Grouper(freq='30min')).transform('mean')
        s1, s2, s3, s4, _, _, _, _ = quan(df_tur['w'], t_tran, hole)

        # Calculate deltaS,cem and icem from the conditions
        cem = (r + 1) * (2 * c11 / (1 + r) ** 2 + c22 / (1 + r)) / (r * np.sqrt(2 * np.pi))
        icem = (m21 - m12) / (2 * r * np.sqrt(2 * np.pi))
        deltaS31 = (s3 - s1).dropna()
        deltaS24 = (s2 - s4).dropna()
        deltaS = deltaS24.where(wt_mean_30min < 0, deltaS31)

        # Save calculations in a list
        deltas_all.append(deltaS)
        m21_all.append(m21), m12_all.append(m12), cem_all.append(cem), icem_all.append(icem)
        time2 = time.time()
        print(f'Calculation of layer consumption time {(time2 - time1) / 60} minutes.')
    deltaS_dataframe = pd.concat(deltas_all, axis=1)
    m21_dataframe = pd.concat(m21_all, axis=1)
    m12_dataframe = pd.concat(m12_all, axis=1)
    cem_dataframe = pd.concat(cem_all, axis=1)
    icem_dataframe = pd.concat(icem_all, axis=1)
    # Write index
    deltaS_dataframe.columns = height
    m21_dataframe.columns = height
    m12_dataframe.columns = height
    cem_dataframe.columns = height
    icem_dataframe.columns = height
    return deltaS_dataframe, cem_dataframe, icem_dataframe


def custom_sort_key(path):
    category = path.split('\\')[-1][0]  # 提取 A, B, C
    number = 4-int(path.split('\\')[-1][1:])  # 提取数字 1, 2, 3, 4
    return category, number

if __name__ == '__main__':
    print('Test program:')
    try:
        paths = glob.glob( 'G:/inldata/ecdata/*')
        paths = sorted(paths, key=custom_sort_key, reverse=True)  # 文件夹从低到高进行排序，从C1到A4
        deltaS_dataframe, cem_dataframe, icem_dataframe = read_datfiles(paths, 0,'2021-04-27', '2021-04-28',
                                                                        '10:00:00','16:00:00',
                                                                        ['2021-05-06', '2021-05-07', '2021-06-07',
                                                                         '2021-06-17', '2021-04-30'],
                                                                        ['u', 'v', 'w', 't', 'water', 'CO2'],
                                                                        [1.2,2.0,3.5,6.0,8.2,12.8,15.8,23.0,30.3,40.2,50.6,60.5])
    except FileNotFoundError as e:
        print('The corresponding test .dat file needs to exist')
