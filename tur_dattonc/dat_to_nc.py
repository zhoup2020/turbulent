import numpy as np
import pandas as pd
from numbers import Number
import xarray as xr


def custom_sort_key(path):
    category = path.split('\\')[-1][0]  # 提取 A, B, C
    number = 4 - int(path.split('\\')[-1][1:])  # 提取数字 1, 2, 3, 4
    return category, number


# 创建一个空的类
class Container:
    pass


# 创建预变量的对象，即为空列表
def prelist_creation(variables):
    obj = Container()
    for variable in variables:
        setattr(obj, variable, [])
    return obj

def save_to_nc(dataset1,outputpath,name):
    valid_types = (str, Number, np.ndarray, np.number, list, tuple)
    try:
        dataset1.to_netcdf(outputpath + '/' + f'{name}.nc')
    # Fails with TypeError: Invalid value for attr: ...
    except TypeError as e:
        print(e.__class__.__name__, e)
        for variable in dataset1.variables.values():
            for k, v in variable.attrs.items():
                if not isinstance(v, valid_types) or isinstance(v, bool):
                    variable.attrs[k] = str(v)
        dataset1.to_netcdf(outputpath + '/' + f'{name}.nc', compute=True)
# 将多个dat文件转换为nc文件
def dat_nc(input_paths, datetime, timestep, variables, heights, output_path):
    obj = prelist_creation(variables)
    for path in input_paths:
        # 对文件名进行排序
        # 读取数据
        try:
            df = pd.read_csv(path, header=None)
            df.columns = variables
            start_time = ' '.join([datetime, '00:00:00'])
            df.index = pd.date_range(start=start_time, periods=len(df), freq=f'{timestep}s')
            # 筛选出10至16时之间的数据，并填充缺失值
            df.replace(-9999.0, np.nan, inplace=True)
        except FileNotFoundError as e:
            print(e)
            continue

        try:
            for variable in variables:
                getattr(obj, variable).append(df[variable])
        except:
            print('Possible missing files!')

    try:
        for variable in variables:
            setattr(obj, variable, pd.concat(getattr(obj, variable), axis=1))
            setattr(obj, variable,
                    xr.DataArray(getattr(obj, variable).values,
                                 coords=[getattr(obj, variable).index, np.array(heights)],
                                 dims=['Time', 'Height']))
        dataset1 = xr.Dataset({variable: getattr(obj, variable) for variable in variables})
        name = datetime[:10]
        save_to_nc(dataset1, output_path, name)
    except ValueError as e:
        print(f'{e}\n Please make sure that the number of documents corresponds to their height')

