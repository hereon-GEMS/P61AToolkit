import pandas as pd
from matplotlib import pyplot as plt
from itertools import permutations
from uncertainties import unumpy
from py61a.viewer_utils import read_peaks, valid_peaks
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import Sin2Psi, DeviatoricStresses

from simulate_stresses import sigma_at_tau, eta, tth


if __name__ == '__main__':
    psi_max = 10.
    abs_element = 'Fe'  # for absorption data

    # getting the dataset
    dd = read_peaks(r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs\tut02_00001_true.csv')
    # getting DECs
    dec_path = r'../../../data/dec/bccFe.csv'
    dec = pd.read_csv(dec_path, index_col=None, comment='#')
    dec['hkl'] = dec.apply(lambda row: '%d%d%d' % (row['h'], row['k'], row['l']), axis=1)

    # calculating tau (information depth), strain projection, and DECs (s1, hs2)
    for peak_id in valid_peaks(dd):
        for x in permutations(dd[peak_id][['h', 'k', 'l']].mean().astype(int).tolist()):
            if '%d%d%d' % x in dec['hkl'].values:
                dd.loc[:, (peak_id, 's1')] = dec[dec['hkl'] == '%d%d%d' % x].s1.mean()
                dd.loc[:, (peak_id, 'hs2')] = dec[dec['hkl'] == '%d%d%d' % x].hs2.mean()
                break

        dd.loc[:, (peak_id, 'depth')] = tau(mu=mu(abs_element, dd[peak_id]['center']),
                                            tth=tth, eta=eta, psi=dd['md']['eu.chi'])
        ens = unumpy.uarray(dd[peak_id]['center'].values, dd[peak_id]['center_std'].values)
        ds = bragg(en=ens, tth=tth)['d']
        dd.loc[:, (peak_id, 'd')] = unumpy.nominal_values(ds)
        dd.loc[:, (peak_id, 'd_std')] = unumpy.std_devs(ds)

    analysis = Sin2Psi(dataset=dd, phi_atol=.1, psi_atol=.001, psi_max=psi_max)
    for peak in analysis.peaks:
        plt.figure(peak)
        ax1 = plt.subplot(121)

        ax12 = ax1.secondary_yaxis('right', functions=analysis.d_star_transform(peak))
        ax12.set_ylabel(r'(d - d$^*$) / d$^*$')
        ax2 = plt.subplot(122)
        ax22 = ax2.secondary_yaxis('right', functions=analysis.d_star_transform(peak))
        ax22.set_ylabel(r'(d - d$^*$) / d$^*$')

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

    analysis = DeviatoricStresses(analysis, dec=dec)
    stress_md = sigma_at_tau(analysis.depths)

    plt.figure('Deviatoric stresses')
    plt.errorbar(analysis.depths, analysis.s11m33_n, xerr=analysis.depth_xerr, yerr=analysis.s11m33_std,
                 label=r'$\sigma_{11} - \sigma_{33}$', linestyle='', marker='x', color='blue')
    plt.plot(analysis.depths, stress_md[0, 0] - stress_md[2, 2],
             label=None, linestyle='--', marker=None, color='blue')
    plt.errorbar(analysis.depths, analysis.s22m33_n, xerr=analysis.depth_xerr, yerr=analysis.s22m33_std,
                 label=r'$\sigma_{22} - \sigma_{33}$', linestyle='', marker='x', color='orange')
    plt.plot(analysis.depths, stress_md[1, 1] - stress_md[2, 2],
             label=None, linestyle='--', marker=None, color='orange')
    plt.xlabel('Information depth, [mcm]')
    plt.ylabel('Stress [MPa]')
    plt.legend()
    plt.show()
