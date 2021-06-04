import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import h5py

from utils import write_fio


dd = r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs\stress_00004'


def p_voigt(xx_, a, x0, n, s, g):
    return a * (n * np.exp((xx_ - x0) ** 2 / (-2. * s ** 2)) + (1. - n) * (g ** 2) /
                ((xx_ - x0) ** 2 + g ** 2))


if __name__ == '__main__':
    n_bins = 4096

    dataset = pd.read_csv(r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\src\scripts\Scan4_CD_P61.dat',
                          sep='\t', skiprows=1)
    prefixes = set(col.split('_')[0] for col in dataset.columns if 'center' in col)

    if not os.path.exists(dd):
        os.mkdir(dd)

    for idx in dataset.index:
        xx = np.arange(n_bins) * 5E-2 + 0.025
        # yy = 10 * np.random.random(n_bins)
        yy = np.ones(shape=xx.shape)
        for prefix in prefixes:
            yy += p_voigt(xx,
                          # a=dataset.loc[idx, '_'.join((prefix, 'amplitude'))],
                          a=1e5,
                          x0=dataset.loc[idx, '_'.join((prefix, 'center'))],
                          n=0.5,
                          # s=dataset.loc[idx, '_'.join((prefix, 'sigma'))] / np.sqrt(2. * np.log(2.)),
                          # g=dataset.loc[idx, '_'.join((prefix, 'sigma'))])
                          s=3e-1 / np.sqrt(2. * np.log(2.)),
                          g=3e-1)

        # plt.plot(xx, yy)
        # plt.show()

        # with h5py.File(os.path.join(dd, 'stress_%05d.nxs' % idx), 'w') as f:
        #     f.create_dataset('entry/instrument/xspress3/channel00/histogram', data=yy.reshape((1, n_bins)))

    fio_header = {
        'eu.x': 0.,
        'eu.y': 0.,
        'eu.z': 0.,
        'eu.eta': 0.,
        'eu.phi': 0.,
        'eu.psi': 0.,
    }

    fio_table = pd.DataFrame(columns=('eu.phi', 'eu.psi', 'xspress3_index'))

    for idx in dataset.index:
        fio_table.loc[fio_table.shape[0]] = {
            'eu.phi': dataset.loc[idx, 'phi'],
            'eu.psi': dataset.loc[idx, 'psi'],
            'xspress3_index': idx
        }

    # write_fio(fio_header, fio_table, dd + '.fio')