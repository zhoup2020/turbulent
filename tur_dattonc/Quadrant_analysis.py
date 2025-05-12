import numpy as np
import pandas as pd

# Calculate sweeps and Ejection flux and time fractions
def quan(tur1,tur2,hole):
    tur = tur1*tur2
    tur_mean = tur.resample('30min').mean().dropna()     # one data per 30 minutes
    tur_mean_30min = (tur1 * tur2).groupby(pd.Grouper(freq='30min')).transform('mean')   # one data per timestep
    condition3 = ((tur1 < 0) & (tur2 < 0)) & (np.abs(tur1 * tur2) > hole * np.abs(tur_mean_30min))
    s3 = (tur.where(condition3, 0).resample('30min').mean().dropna()) / tur_mean  # sweeps flux fraction
    tf3 = condition3.astype(int).resample('30min').mean().dropna()  # sweeps time fraction
    condition1 = ((tur1 > 0) & (tur2 > 0)) & (np.abs(tur1 * tur2) > hole * np.abs(tur_mean_30min))
    s1 = (tur.where(condition1, 0).resample('30min').mean().dropna()) / tur_mean  # Ejections flux fraction
    tf1 = condition1.astype(int).resample('30min').mean().dropna()
    condition4 = ((tur1 > 0) & (tur2 < 0)) & (np.abs((tur1 * tur2)) > hole * np.abs(tur_mean_30min))
    s4 = (tur.where(condition4, 0).resample('30min').mean().dropna()) / tur_mean
    tf4 = condition4.astype(int).resample('30min').mean().dropna()
    condition2 = ((tur1 < 0) & (tur2 > 0)) & (np.abs(tur1 * tur2) > hole * np.abs(tur_mean_30min))
    s2 = (tur.where(condition2, 0).resample('30min').mean().dropna()) / tur_mean
    tf2 = condition2.astype(int).resample('30min').mean().dropna()
    return s1,s2,s3,s4,tf1,tf2,tf3,tf4