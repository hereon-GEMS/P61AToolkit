import h5py
import numpy as np
import pandas as pd
import os

from P61App import P61App


class P61ACSVReader:

    def __init__(self):
        self.q_app = P61App.instance()

    def validate(self, f_name):
        try:
            d = pd.read_csv(f_name)
            return ('eV' in d.columns) & ('counts' in d.columns)
        except Exception:
            return False

    def read(self, f_name):
        dd = pd.read_csv(
            f_name,
            index_col='eV'
        )

        ch = int(f_name.replace('.csv', '')[-2:])

        result = pd.DataFrame(columns=self.q_app.data.columns)
        row = {c: None for c in self.q_app.data.columns}
        row.update({
            'DataX': 1E-3 * dd.index.to_numpy(),
            'DataY': dd['counts'].to_numpy(),
            'DataID': f_name.replace('.csv', '')[:-3] + ':' + f_name.replace('.csv', '')[-2:],
            'Channel': ch,
            'ScreenName': os.path.basename(f_name),
            'Active': True,
            'Color': next(self.q_app.params['ColorWheel'])
        })
        result.loc[result.shape[0]] = row

        result = result.astype('object')
        result[pd.isna(result)] = None
        return result
