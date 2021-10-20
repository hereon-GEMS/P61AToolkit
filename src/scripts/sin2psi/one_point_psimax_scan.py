from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, get_peak_ids, peak_id_str
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import sin2psi, deviatoric_stresses


if __name__ == '__main__':
    element = 'Fe'
    dd = read_peaks(r'Z:\p61\2021\data\11012378\processed\SMSS_oven_test_after.csv')
    dec = pd.read_csv(r'../../../data/dec/bccFe.csv', index_col=None, comment='#')
    tth = dd[('md', 'd0.rz')].mean()
    dd[('md', 'eu.chi')] = 90. - dd[('md', 'eu.chi')]
    # dd[('md', 'eu.phi')] = (dd[('md', 'eu.phi')] - 45) % 360

    # calculating d values and depth
    for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
        d_val = bragg(en=unumpy.uarray(dd[(peak_id, 'center')], dd[(peak_id, 'center_std')]), tth=tth)['d']
        dd[(peak_id, 'd')] = unumpy.nominal_values(d_val)
        dd[(peak_id, 'd_std')] = unumpy.std_devs(d_val)
        dd[(peak_id, 'depth')] = tau(
            mu(element, dd[(peak_id, 'center')].mean()),
            tth=tth, psi=dd[('md', 'eu.chi')], eta=90.
        )

    xx, yy11, yy22, zz = [], [], [], []
    for psi_max in np.arange(90., 30., -5.):
        print(psi_max)

        analysis = sin2psi(dataset=dd, phi_col='eu.phi', phi_atol=5.,
                           psi_col='eu.chi', psi_atol=.1, psi_max=psi_max)
        stresses = deviatoric_stresses(dd, analysis, dec)
        analysis = analysis.squeeze(axis=0)
        stresses = stresses.squeeze(axis=0)

        xx.extend(stresses[stresses.index.get_level_values(1) == 'depth'].to_list())
        yy11.extend(stresses[stresses.index.get_level_values(1) == 's11-s33'].apply(lambda x: x.n).to_list())
        yy22.extend(stresses[stresses.index.get_level_values(1) == 's22-s33'].apply(lambda x: x.n).to_list())
        zz.extend([psi_max] * stresses[stresses.index.get_level_values(1) == 'depth'].shape[0])

        print(analysis)
        print(stresses)

    print(len(xx), len(yy11), len(yy22), len(zz))

    fig = plt.figure()
    ax1 = fig.add_subplot(121, projection='3d')
    ax1.scatter(xx, zz, yy11)
    ax1.set_xlabel('Information depth [μm]')
    ax1.set_ylabel('Ψ cutoff [deg]')
    ax1.set_zlabel('Stress [MPa]')
    ax2 = fig.add_subplot(122, projection='3d')
    ax2.scatter(xx, zz, yy22)

    # plt.figure('Deviatoric stresses')
    # plt.errorbar(
    #     x=stresses[stresses.index.get_level_values(1) == 'depth'],
    #     y=stresses[stresses.index.get_level_values(1) == 's11-s33'].apply(lambda x: x.n),
    #     yerr=stresses[stresses.index.get_level_values(1) == 's11-s33'].apply(lambda x: x.s),
    #     label=r'$\sigma_{11}-\sigma_{33}$', marker='x', linestyle=''
    # )
    # plt.errorbar(
    #     x=stresses[stresses.index.get_level_values(1) == 'depth'],
    #     y=stresses[stresses.index.get_level_values(1) == 's22-s33'].apply(lambda x: x.n),
    #     yerr=stresses[stresses.index.get_level_values(1) == 's22-s33'].apply(lambda x: x.s),
    #     label=r'$\sigma_{22}-\sigma_{33}$', marker='x', linestyle=''
    # )
    # plt.xlabel('Information depth [μm]')
    # plt.ylabel('Stress [MPa]')
    # plt.legend()
    plt.show()
