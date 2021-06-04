import numpy as np
import pandas as pd


def sin2psi_peak(data: pd.DataFrame):
    print(data.columns)
    stress = np.zeros(shape=(3, 3, data.shape[0]))
    print(stress)


def sin2psi_analysis(data: pd.DataFrame):
    prefixes = set(col.split('_')[0] for col in data.columns if 'center' in col)

    for prefix in prefixes:
        cols = ['a0', 'tth', 'chi', 'phi', 'eta'] + [col for col in data.columns if prefix in col]
        peak_data = data[cols]
        peak_data.rename(columns=lambda x: x.replace(prefix + '_', ''), inplace=True)

        sin2psi_peak(peak_data)
