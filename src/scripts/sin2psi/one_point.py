import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from uncertainties import unumpy
from copy import deepcopy

from py61a.viewer_utils import read_peaks, valid_peaks
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import Sin2Psi, MultiWaveLength, DeviatoricStresses


if __name__ == '__main__':
    element = 'Fe'
    # dd = read_peaks(r'Z:\p61\2021\commissioning\c20210813_000_gaf_2s21\processed\Swerim\41\sin2psi_GD.csv')
    dd = read_peaks(r'Z:\p61\2021\commissioning\c20210813_000_gaf_2s21\processed\com4pBending_fullScan_01712.csv')
    tth = dd[('md', 'd1.rx')].mean()

    # calculating information depth (tau) and d values
    for peak_id in valid_peaks(dd, valid_for='sin2psi'):
        dd.loc[:, (peak_id, 'depth')] = tau(
            mu=mu(element, dd[peak_id]['center']),
            tth=tth,
            eta=90.,
            psi=dd['md']['eu.chi']
        )
        bragg_data = bragg(
            en=unumpy.uarray(dd[peak_id]['center'].values, dd[peak_id]['center_std'].values),
            tth=tth)
        dd.loc[:, (peak_id, 'd')] = unumpy.nominal_values(bragg_data['d'])
        dd.loc[:, (peak_id, 'd_std')] = unumpy.std_devs(bragg_data['d'])

    # sin2psi analysis
    analysis = Sin2Psi(dd, psi_max=90., phi_atol=10., psi_atol=1.)
    for peak in analysis.peaks:
        plt.figure(peak)
        ax1 = plt.subplot(121)
        # ax12 = ax1.secondary_yaxis('right', functions=(
        #     lambda x: (x - deepcopy(analysis.d_star(peak))) / deepcopy(analysis.d_star(peak)),
        #     lambda x: x * (1. + deepcopy(analysis.d_star(peak)))
        # ))
        # ax12.set_ylabel(r'(d - d$^*$) / d$^*$')
        ax2 = plt.subplot(122)
        # ax22 = ax2.secondary_yaxis('right', functions=(
        #     lambda x: (x - analysis.d_star(peak).copy()) / analysis.d_star(peak).copy(),
        #     lambda x: x * (1. + analysis.d_star(peak).copy())
        # ))
        # ax22.set_ylabel(r'(d - d$^*$) / d$^*$')

        for projection in analysis.projections:
            if '+' in projection:
                ax1.plot(analysis[peak, projection].x, analysis[peak, projection].y, 'o',
                         label=projection)
                ax1.plot(analysis[peak, projection].x, analysis[peak, projection].y_calc, '--',
                         label=None, color='black')
            elif '-' in projection:
                ax2.plot(analysis[peak, projection].x, analysis[peak, projection].y, 'o',
                         label=projection)
                ax2.plot(analysis[peak, projection].x, analysis[peak, projection].y_calc, '--',
                         label=None, color='black')
        ax1.set_xlabel(r'$\sin^2(\psi)$')
        ax2.set_xlabel(r'$\sin(2\psi)$')
        ax1.set_ylabel(r'd [AA]')
        ax2.set_ylabel(r'd [AA]')
        ax1.legend()
        ax2.legend()
        plt.tight_layout()
    plt.show()

    # deviatoric stress component analysis
    analysis = DeviatoricStresses(
        analysis,
        dec=pd.read_csv(r'../../../data/dec/bccFe.csv', index_col=None, comment='#')
    )

    plt.figure('Deviatoric stresses')
    plt.errorbar(analysis.depths, analysis.s11m33_n, xerr=analysis.depth_xerr, yerr=analysis.s11m33_std,
                 label=r'$\sigma_{11} - \sigma_{33}$')
    plt.errorbar(analysis.depths, analysis.s22m33_n, xerr=analysis.depth_xerr, yerr=analysis.s22m33_std,
                 label=r'$\sigma_{22} - \sigma_{33}$')
    plt.xlabel('Information depth, [mcm]')
    plt.ylabel('Stress [MPa]')
    plt.legend()
    plt.show()