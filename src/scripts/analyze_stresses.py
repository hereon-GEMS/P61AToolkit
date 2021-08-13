import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from itertools import permutations
from uncertainties import unumpy
from py61a.viewer_utils import read_peaks, valid_peaks, peak_id_str
from py61a.cryst_utils import tau, mu, bragg, lattice_planes
from py61a.stress import Sin2Psi, MultiWaveLength

from simulate_stresses import sigma_at_tau


"""
Relaxed lattice at 2θ = 15.0°:
    [1 1 0]: E = 23.6 keV, I = 1000 cts
    [2 0 0]: E = 33.4 keV, I = 234 cts
    [2 1 1]: E = 41.0 keV, I = 92 cts
    [2 2 0]: E = 47.3 keV, I = 46 cts
    [3 1 0]: E = 52.9 keV, I = 26 cts
    [2 2 2]: E = 57.9 keV, I = 17 cts
    [3 2 1]: E = 62.6 keV, I = 11 cts
    [4 0 0]: E = 66.9 keV, I = 8 cts
    [4 1 1]: E = 70.9 keV, I = 12 cts
    [4 2 0]: E = 74.8 keV, I = 5 cts
    [3 3 2]: E = 78.4 keV, I = 4 cts
    [5 2 1]: E = 91.6 keV, I = 2 cts
"""


if __name__ == '__main__':
    tth = 15.
    d0 = 2.84034
    psi_max = 45.
    element_name = 'Fe'  # for absorption data

    # getting the dataset
    # dd = read_peaks(r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs\tut02_00001_true.csv')
    dd = read_peaks(r'Z:\p61\2021\commissioning\c20210813_000_gaf_2s21\processed\com4pBending_initialTest_01711.csv')
    # getting DECs
    dec_path = r'/dec/bccFe.csv'
    dec = pd.read_csv(dec_path, index_col=None, comment='#')
    dec['hkl'] = dec.apply(lambda row: '%d%d%d' % (row['h'], row['k'], row['l']), axis=1)

    # calculating relaxed lattice
    d0_planes = lattice_planes('im-3m', d0, d0, d0, 90., 90., 90., tth, all_hkl=True)

    # calculating tau (information depth), strain projection, and DECs (s1, hs2)
    for peak_id in valid_peaks(dd):
        for d0_plane in d0_planes:
            if ((d0_plane['h'] == dd[peak_id]['h'].mean().astype(int)) and
                    (d0_plane['k'] == dd[peak_id]['k'].mean().astype(int)) and
                    (d0_plane['l'] == dd[peak_id]['l'].mean().astype(int))):
                d0_ = d0_plane['d']
                break
        else:
            print(peak_id_str(dd, peak_id), 'Not found')
            continue

        for x in permutations(dd[peak_id][['h', 'k', 'l']].mean().astype(int).tolist()):
            if '%d%d%d' % x in dec['hkl'].values:
                dd.loc[:, (peak_id, 's1')] = dec[dec['hkl'] == '%d%d%d' % x].s1.mean()
                dd.loc[:, (peak_id, 'hs2')] = dec[dec['hkl'] == '%d%d%d' % x].hs2.mean()
                break

        dd.loc[:, (peak_id, 'depth')] = tau(mu=mu(element_name, dd[peak_id]['center']),
                                            tth=tth, eta=90., psi=dd['md']['eu.chi'])
        ens = unumpy.uarray(dd[peak_id]['center'].values, dd[peak_id]['center_std'].values)
        ds = bragg(en=ens, tth=tth)['d']
        strains = (ds - d0_) / d0_
        dd.loc[:, (peak_id, 'e')] = unumpy.nominal_values(strains)
        dd.loc[:, (peak_id, 'e_std')] = unumpy.std_devs(strains)
        dd.loc[:, (peak_id, 'd')] = unumpy.nominal_values(ds)
        dd.loc[:, (peak_id, 'd_std')] = unumpy.std_devs(ds)
        dd.loc[:, (peak_id, 'd0')] = d0_

    # performing sin^2(psi) analysis
    analysis = Sin2Psi(dataset=dd, phi_atol=.1, psi_atol=.01, psi_max=psi_max)

    for peak in analysis.peaks:
        plt.figure(peak)
        ax1 = plt.subplot(121)
        ax2 = plt.subplot(122)
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

    analysis = MultiWaveLength(analysis)
    taus_md = np.linspace(np.min(analysis.depths_min), np.max(analysis.depths_max), 1000)
    stress_tensor_md = sigma_at_tau(taus_md)

    # plt.figure('Tensor components')
    #
    # plt.subplot(121)
    # plt.errorbar(analysis.depths, analysis.stress_tensor_n[0, 0], yerr=analysis.stress_tensor_std[0, 0],
    #              xerr=analysis.depth_xerr, marker='x', linestyle='', color='r', label=r'$\sigma_{11}$')
    # plt.errorbar(analysis.depths, analysis.stress_tensor_n[1, 1], yerr=analysis.stress_tensor_std[1, 1],
    #              xerr=analysis.depth_xerr, marker='x', linestyle='', color='g', label=r'$\sigma_{22}$')
    # plt.errorbar(analysis.depths, analysis.stress_tensor_n[2, 2], yerr=analysis.stress_tensor_std[2, 2],
    #              xerr=analysis.depth_xerr, marker='x', linestyle='', color='b', label=r'$\sigma_{33}$')
    # plt.plot(taus_md, stress_tensor_md[0, 0], '--', color='r', alpha=0.5, label=r'$\sigma_{11}$')
    # plt.plot(taus_md, stress_tensor_md[1, 1], '--', color='g', alpha=0.5, label=r'$\sigma_{22}$')
    # plt.plot(taus_md, stress_tensor_md[2, 2], '--', color='b', alpha=0.5, label=r'$\sigma_{33}$')
    # plt.xlabel('Information depth, [mcm]')
    # plt.ylabel('Stress, [MPa]')
    # plt.legend()
    #
    # plt.subplot(122)
    # plt.errorbar(analysis.depths, analysis.stress_tensor_n[0, 1], yerr=analysis.stress_tensor_std[0, 1],
    #              xerr=analysis.depth_xerr, marker='x', linestyle='', color='r', label=r'$\sigma_{12}$')
    # plt.errorbar(analysis.depths, analysis.stress_tensor_n[0, 2], yerr=analysis.stress_tensor_std[0, 2],
    #              xerr=analysis.depth_xerr, marker='x', linestyle='', color='g', label=r'$\sigma_{13}$')
    # plt.errorbar(analysis.depths, analysis.stress_tensor_n[1, 2], yerr=analysis.stress_tensor_std[1, 2],
    #              xerr=analysis.depth_xerr, marker='x', linestyle='', color='b', label=r'$\sigma_{23}$')
    # plt.plot(taus_md, stress_tensor_md[0, 1], '--', color='r', alpha=0.5, label=r'$\sigma_{12}$')
    # plt.plot(taus_md, stress_tensor_md[0, 2], '--', color='g', alpha=0.5, label=r'$\sigma_{13}$')
    # plt.plot(taus_md, stress_tensor_md[1, 2], '--', color='b', alpha=0.5, label=r'$\sigma_{23}$')
    # plt.xlabel('Information depth, [mcm]')
    # plt.ylabel('Stress, [MPa]')
    # plt.legend()
    # plt.tight_layout()

    plt.figure()
    s11m33 = analysis.stress_tensor[0, 0] - analysis.stress_tensor[2, 2]
    s22m33 = analysis.stress_tensor[1, 1] - analysis.stress_tensor[2, 2]
    plt.errorbar(analysis.depths, unumpy.nominal_values(s11m33), yerr=unumpy.std_devs(s11m33),
                 xerr=analysis.depth_xerr, marker='x', linestyle='', color='r', label=r'$\sigma_{11}-\sigma_{33}$')
    plt.errorbar(analysis.depths, unumpy.nominal_values(s22m33), yerr=unumpy.std_devs(s22m33),
                 xerr=analysis.depth_xerr, marker='x', linestyle='', color='g', label=r'$\sigma_{22}-\sigma_{33}$')
    plt.errorbar(analysis.depths, analysis.stress_tensor_n[2, 2], yerr=analysis.stress_tensor_std[2, 2],
                 xerr=analysis.depth_xerr, marker='x', linestyle='', color='b', label=r'$\sigma_{33}$')
    plt.plot(taus_md, stress_tensor_md[0, 0] - stress_tensor_md[2, 2], '--', color='r', alpha=0.5,
             label=r'$\sigma_{11}-\sigma_{33}$')
    plt.plot(taus_md, stress_tensor_md[1, 1] - stress_tensor_md[2, 2], '--', color='g', alpha=0.5,
             label=r'$\sigma_{22}-\sigma_{33}$')
    plt.plot(taus_md, stress_tensor_md[2, 2], '--', color='b', alpha=0.5, label=r'$\sigma_{33}$')
    plt.xlabel('Information depth, [mcm]')
    plt.ylabel('Stress, [MPa]')
    plt.legend()

    plt.show()
