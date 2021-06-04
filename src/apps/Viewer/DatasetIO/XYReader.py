import h5py
import numpy as np
import pandas as pd
import os

from P61App import P61App


class XYReader:

    def __init__(self):
        self.q_app = P61App.instance()

    def validate(self, f_name):
        return '.xy' in f_name

    def read(self, f_name):
        header_size = 0
        with open(f_name, 'r') as f:
            for header_size, line in enumerate(f.readlines()):
                if line[0] != '#':
                    break

        dd = pd.read_csv(f_name, sep='\s+', skiprows=header_size, header=None)

        result = pd.DataFrame(columns=self.q_app.data.columns)
        row = {c: None for c in self.q_app.data.columns}
        row.update({
            'DataX': np.array(dd.loc[:, 0]).astype(np.float),
            'DataY': np.array(dd.loc[:, 1]).astype(np.float),
            'DataID': f_name,
            'ScreenName': os.path.basename(f_name),
            'Active': True,
            'Color': next(self.q_app.params['ColorWheel'])
        })
        result.loc[result.shape[0]] = row

        result = result.astype('object')
        result[pd.isna(result)] = None
        return result
