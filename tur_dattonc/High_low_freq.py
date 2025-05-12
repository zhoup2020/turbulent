"""
This python file uses EMD decomposition to decompose the data into high and low frequency signals.
Edit Time: 2025/04/25
"""

import numpy as np
import pandas as pd
import time
from joblib import Parallel, delayed
from PyEMD import EMD
from scipy.signal import hilbert

# Calculate average frequency of every imf model
def compute_avg_frequency(imf, t):
    analytic_signal = hilbert(imf)
    instantaneous_phase = np.unwrap(np.angle(analytic_signal))
    instantaneous_frequency = np.diff(instantaneous_phase) / (2 * np.pi * np.diff(t))
    return np.mean(instantaneous_frequency)

# Let signal decompose high and low signal (Using EMD decomposition is used)
def process_emd(signal, threshold=0.1, max_imf=14):
    emd = EMD()
    t = np.arange(0, 1800, 0.1)
    imfs = emd(signal.values, t, max_imf=max_imf)

    # Dealing with the situation of insufficient IMFs numbers
    if len(imfs) <= 1:
        return pd.DataFrame({
            'high_freq_signal': np.zeros_like(signal.values),
            'low_freq_signal': signal.values
        }, index=signal.index)

    # Calculate average frequency
    avg_frequencies = [compute_avg_frequency(imf, t) for imf in imfs[:-1]]
    avg_freq_array = np.array(avg_frequencies)

    # Check if the frequency array is empty
    if avg_freq_array.size == 0:
        return pd.DataFrame({
            'high_freq_signal': np.zeros_like(signal.values),
            'low_freq_signal': signal.values
        }, index=signal.index)

    # 找到分割点
    valid_indices = np.where(avg_freq_array < threshold)[0]
    if valid_indices.size > 0:
        split_idx = valid_indices[0]
    else:
        split_idx = len(avg_freq_array)  # At this time, all IMFs are considered high-frequency

    # Make sure that the split_idx does not exceed the IMFs number
    split_idx = min(split_idx, len(imfs))

    # 分割高频和低频IMF
    high_freq_imfs = imfs[:split_idx]
    low_freq_imfs = imfs[split_idx:]

    # 处理空数组求和
    high_freq_signal = high_freq_imfs.sum(axis=0) if len(high_freq_imfs) > 0 else np.zeros_like(signal.values)
    low_freq_signal = low_freq_imfs.sum(axis=0) if len(low_freq_imfs) > 0 else signal.values

    return pd.DataFrame({
        'high_freq_signal': high_freq_signal,
        'low_freq_signal': low_freq_signal
    }, index=signal.index)


# Use Joblib Parallel computing
def parallel_emd_processing(series, freq='30min', n_jobs=-1):
    groups = [group for _, group in series.resample(freq) if not group.empty]

    results = Parallel(n_jobs=n_jobs, verbose=0)(
        delayed(process_emd)(group)
        for group in groups
    )

    return pd.concat(results)


def high_low_freq(paths,start_date,end_date,start_time,end_time,exclude_dates,vars_list,height):
    dates = pd.date_range(start=start_date,end=end_date)
    exclude_dates = exclude_dates   # 数据缺失的日期
    exclude_dates = pd.to_datetime(exclude_dates)
    dates = dates[~dates.isin(exclude_dates)]                   # 剔除掉缺测日期
    dates1 = dates.strftime('%m%d').tolist()
    dates2 = dates.strftime('%m-%d').tolist()
    w_low,w_high,t_low,t_high,uf_all = [],[],[],[],[]
    for path in paths:
        df_list = []
        time1 = time.time()
        for date,date1,date2 in zip(dates,dates1,dates2):
            try:
                filename = ''.join(['/ec_flux_2021',date1,'_0000.dat'])
                file = ''.join([path,filename])
                df = pd.read_csv(file,header=None)
                df.columns = vars_list
                df.index = pd.date_range(start=date, periods=len(df), freq='0.1s')
                # Filter the data and populate the missing values.
                df_sel = df[(df.index >= pd.to_datetime(' '.join([start_date[:5] + date2, start_time]))) & (
                        df.index < pd.to_datetime(' '.join([end_date[:5] + date2, end_time])))][['u', 'v', 'w', 't']]
                # Set the missing value -9999.0 in the data to NAN to facilitate interpolation.
                df_sel.replace(-9999.0, np.nan, inplace=True)
                df_sel.interpolate(method='linear')
                df_sel = df_sel.ffill()
                df_sel = df_sel.bfill()
                df_sel = df_sel.dropna()
                half_hour_means = df_sel.groupby(pd.Grouper(freq='30min')).transform('mean')
                df_tur = df_sel - half_hour_means     # turbulent
                df_list.append(df_tur)
            except FileNotFoundError as e:
                print(e)
        #         print(f'There is no data for {date1}')
                continue
        df_dataframe = pd.concat(df_list, axis=0)
        uf= np.sqrt(np.sqrt(np.abs(((df_dataframe['u']*df_dataframe['w']).resample('30min').mean().dropna())**2+((df_dataframe['v']*df_dataframe['w']).resample('30min').mean().dropna())**2)))
        signal_w = parallel_emd_processing(df_dataframe['w'])
        signal_t = parallel_emd_processing(df_dataframe['t'])
        w_high_freq,t_high_freq = signal_w['high_freq_signal'],signal_t['high_freq_signal']
        w_low_freq,t_low_freq = signal_w['low_freq_signal'],signal_t['low_freq_signal']
        # Collect all the variables and merge them
        w_high.append(w_high_freq),t_high.append(t_high_freq),w_low.append(w_low_freq),t_low.append(t_low_freq)
        uf_all.append(uf)
        time2 = time.time()
        print(f'Calculation of layer consumption time {(time2-time1)/60} minutes')
    w_large = pd.concat(w_low,axis=1)
    w_small = pd.concat(w_high,axis=1)
    t_large = pd.concat(t_low,axis=1)
    t_small = pd.concat(t_high,axis=1)
    uf_df = pd.concat(uf_all,axis=1)
    w_large.columns = height
    w_small.columns = height
    t_large.columns = height
    t_small.columns = height
    uf_df.columns = height
    return w_large,w_small,t_large,t_large,uf_df

