import numpy as np
import pandas as pd
import warnings

# Calculate the correlation of turbulent variance1 and turbulent variance2 based on pandas cluster
def safe_correlation(x):
    corr_dict = {}
    a = x.columns
    columns = [i[1] for i in a[:int(len(a)/2)]]
    for col in columns:
        col_1 = x["tur1"][col]
        col_2 = x["tur2"][col]
        if len(col_1) < 2 or len(col_2) < 2:
            corr = np.nan
        else:
            std_1 = col_1.std()
            std_2 = col_1.std()
            if std_1 == 0 or std_2 == 0:
                corr = np.nan
            else:
                corr = col_1.corr(col_2)
        corr_dict[col] = corr
    return pd.Series(corr_dict)

def calculate_corr(tur1,tur2,time_seg):
    combined = pd.concat({"tur1": tur1, "tur2": tur2}, axis=1)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        corr_results = combined.resample(time_seg).apply(safe_correlation).dropna()
    return corr_results