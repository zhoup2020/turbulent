import xarray as xr
import pandas as pd
import numpy as np

# 读取单个 netCDF 文件
def read_single_nc(path,tur1,tur2):
    ds = xr.open_dataset(path)
    df1 = pd.DataFrame(ds[tur1].values[:,5:11],columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time.values))
    df2 = pd.DataFrame(ds[tur2].values[:,5:11],columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time.values))
    uf = pd.DataFrame(ds['u_fraction'].values[:,5:11],columns=ds.Height.values[5:11],index=pd.to_datetime(ds.Time1.values))
    return df1,df2,uf

# 合并多个 netCDF 文件
def read_and_merge_ncs(file_list):
    ds = xr.open_mfdataset(file_list, combine='by_coords')
    return {
        'tur1': ds['tur1'].values,
        'tur2': ds['tur2'].values
    }

# 读取单个 csv 或 dat 文件（默认逗号分隔符）
def read_single_csv_or_dat(path):
    df = pd.read_csv(path, delim_whitespace=path.endswith('.dat'), engine='python')
    return {
        'tur1': df['tur1'],
        'tur2': df['tur2']
    }

# 合并多个 csv 或 dat 文件
def read_and_merge_csvs_or_dats(file_list):
    dfs = []
    for file in file_list:
        df = pd.read_csv(file, delim_whitespace=file.endswith('.dat'), engine='python')
        dfs.append(df)
    merged_df = pd.concat(dfs, ignore_index=True)
    return {
        'tur1': merged_df['tur1'],
        'tur2': merged_df['tur2']
    }
