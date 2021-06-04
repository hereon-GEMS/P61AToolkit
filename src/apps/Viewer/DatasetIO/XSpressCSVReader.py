import h5py
import numpy as np
import pandas as pd
import os

from P61App import P61App


class XSpressCSVReader:

    def __init__(self):
        self.q_app = P61App.instance()

    def validate(self, f_name):
        try:
            d = pd.read_csv(f_name)
            return ('channel' in d.columns) & ('0' in d.columns) & ('1' in d.columns)
        except Exception:
            return False

    def read(self, f_name):
        dd = pd.read_csv(f_name)
        ii = 0
        while ii < dd.shape[0]:
            try:
                float(dd['channel'][ii])
                break
            except ValueError:
                ii += 1

        result = pd.DataFrame(columns=self.q_app.data.columns)
        for ch in ('0', '1'):
            row = {c: None for c in self.q_app.data.columns}
            row.update({
                'DataX': (1E-3 * dd.loc[ii:dd.shape[0] - 2, 'channel'].astype(np.float)).to_numpy(),
                'DataY': (dd.loc[ii:dd.shape[0] - 2, ch].astype(np.float)).to_numpy(),
                'DataID': f_name + ':0' + ch,
                'Channel': int(ch),
                'DeadTime': dd[dd['channel'] == 'dt'][ch][1].astype(np.float),
                'ScreenName': os.path.basename(f_name) + ':' + ch,
                'Active': True,
                'Color': next(self.q_app.params['ColorWheel'])
            })
            result.loc[result.shape[0]] = row

        result = result.astype('object')
        result[pd.isna(result)] = None
        return result
