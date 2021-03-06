from matplotlib import pyplot as plt
import pandas as pd
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

    analysis = sin2psi(dataset=dd, phi_col='eu.phi', phi_atol=5.,
                       psi_col='eu.chi', psi_atol=.1, psi_max=90.)
    stresses = deviatoric_stresses(dd, analysis, dec)
    analysis = analysis.squeeze(axis=0)
    stresses = stresses.squeeze(axis=0)

    print(analysis)
    print(stresses)
    for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
        if peak_id not in set(analysis.index.get_level_values(0)):
            continue

        fig = plt.figure(peak_id)
        fig.suptitle(peak_id_str(dd, peak_id))
        ax1, ax2 = plt.subplot(121), plt.subplot(122)

        for proj in analysis[peak_id].index:
            if '+' in proj:
                ax1.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ydata, '+', label=proj)
                ax1.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ycalc, '--', label=None, color='black')
            elif '-' in proj:
                ax2.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ydata, '+', label=proj)
                ax2.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ycalc, '--', label=None, color='black')
        ax1.set_xlabel(r'$\sin^2(\psi)$')
        ax2.set_xlabel(r'$\sin(2\psi)$')
        ax1.set_ylabel(r'd [AA]')
        ax2.set_ylabel(r'd [AA]')
        ax1.legend()
        ax2.legend()
        plt.tight_layout()

    plt.figure('Deviatoric stresses')
    plt.errorbar(
        x=stresses[stresses.index.get_level_values(1) == 'depth'],
        y=stresses[stresses.index.get_level_values(1) == 's11-s33'].apply(lambda x: x.n),
        yerr=stresses[stresses.index.get_level_values(1) == 's11-s33'].apply(lambda x: x.s),
        label=r'$\sigma_{11}-\sigma_{33}$', marker='x', linestyle=''
    )
    plt.errorbar(
        x=stresses[stresses.index.get_level_values(1) == 'depth'],
        y=stresses[stresses.index.get_level_values(1) == 's22-s33'].apply(lambda x: x.n),
        yerr=stresses[stresses.index.get_level_values(1) == 's22-s33'].apply(lambda x: x.s),
        label=r'$\sigma_{22}-\sigma_{33}$', marker='x', linestyle=''
    )
    plt.xlabel('Information depth [??m]')
    plt.ylabel('Stress [MPa]')
    plt.legend()
    plt.show()
