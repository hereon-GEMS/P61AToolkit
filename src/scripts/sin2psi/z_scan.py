import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from uncertainties import unumpy
from copy import deepcopy

from py61a.viewer_utils import read_peaks, valid_peaks
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import Sin2Psi, MultiWaveLength, DeviatoricStresses


def deviatoric_one_point(dataset):
    # calculating information depth (tau) and d values
    for peak_id in valid_peaks(dataset, valid_for='sin2psi'):
        dataset.loc[:, (peak_id, 'depth')] = tau(
            mu=mu(element, dataset[peak_id]['center']),
            tth=tth,
            eta=90.,
            psi=dataset['md']['eu.chi']
        )
        bragg_data = bragg(
            en=unumpy.uarray(dataset[peak_id]['center'].values, dataset[peak_id]['center_std'].values),
            tth=tth)
        dataset.loc[:, (peak_id, 'd')] = unumpy.nominal_values(bragg_data['d'])
        dataset.loc[:, (peak_id, 'd_std')] = unumpy.std_devs(bragg_data['d'])

    # sin2psi analysis
    analysis = Sin2Psi(dataset, psi_max=90., phi_atol=10., psi_atol=.1)

    # deviatoric stress component analysis
    analysis = DeviatoricStresses(
        analysis,
        dec=pd.read_csv(r'../../../data/dec/bccFe.csv', index_col=None, comment='#')
    )

    return analysis.s11m33, analysis.s22m33, analysis.depths


if __name__ == '__main__':
    element = 'Fe'
    dd = read_peaks((r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aYscan_02000\Peaks_2ayscan.csv',
                     r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aZscan_01999\Peaks_2aZscan.csv'))
    tth = dd[('md', 'd1.rx')].mean()

    dd[('md', 'z.group')] = Sin2Psi.psi_group(dd[('md', 'eu.z')], cutoff=1e20, atol=1e-3)

    zs, s11m33, s22m33 = [], [], []
    zs_mean, s11m33_mean, s22m33_mean = [], [], []
    for zg in set(dd[('md', 'z.group')]):
        tmp = dd.loc[dd[('md', 'z.group')] == zg].copy()
        s1, s2, ts = deviatoric_one_point(tmp)
        s11m33.extend(list(s1))
        s22m33.extend(list(s2))
        zs.extend([tmp[('md', 'eu.z')].mean()] * s1.shape[0])
        s11m33_mean.append(s1.mean())
        s22m33_mean.append(s2.mean())
        zs_mean.append(tmp[('md', 'eu.z')].mean())

    zs, s11m33, s22m33 = np.array(zs), np.array(s11m33), np.array(s22m33)
    zs_mean, s11m33_mean, s22m33_mean = np.array(zs_mean), np.array(s11m33_mean), np.array(s22m33_mean)
    ids = np.argsort(zs_mean)
    zs_mean, s11m33_mean, s22m33_mean = zs_mean[ids], s11m33_mean[ids], s22m33_mean[ids]

    ax = plt.subplot(111)
    ax.errorbar(zs, unumpy.nominal_values(s11m33), yerr=unumpy.std_devs(s11m33), marker='.', linestyle='',
                 label=r'$\sigma_{11} - \sigma_{33}$', color='blue')
    ax.plot(zs_mean, unumpy.nominal_values(s11m33_mean), marker='', linestyle='--', color='blue', label=None)
    ax.errorbar(zs, unumpy.nominal_values(s22m33), yerr=unumpy.std_devs(s22m33), marker='.', linestyle='',
                 label=r'$\sigma_{22} - \sigma_{33}$', color='orange')
    ax.plot(zs_mean, unumpy.nominal_values(s22m33_mean), marker='', linestyle='--', color='orange', label=None)
    plt.xlabel('eu.z')
    plt.ylabel('Stress [MPa]')
    plt.legend()
    plt.show()