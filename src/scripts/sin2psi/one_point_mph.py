from matplotlib import pyplot as plt
import pandas as pd
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, get_peak_ids, peak_id_str
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import sin2psi, deviatoric_stresses


if __name__ == '__main__':
    element = 'Fe'
    dd = read_peaks(r'Z:\p61\2021\data\11011682\processed\Duplex_1-4362_FW_80bar\Peaks.csv')
    dec = dict()
    dec['BCC'] = pd.read_csv(r'../../../data/dec/bccFe.csv', index_col=None, comment='#')
    dec['FCC'] = pd.read_csv(r'../../../data/dec/bccFe.csv', index_col=None, comment='#')
    tth = dd[('md', 'd1.rx')].mean()
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

    phases = dict()
    for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
        if dd[(peak_id, 'phase')].iloc[0] not in phases.keys():
            phases[dd[(peak_id, 'phase')].iloc[0]] = [peak_id]
        else:
            phases[dd[(peak_id, 'phase')].iloc[0]].append(peak_id)

    analysis = sin2psi(dataset=dd, phi_col='eu.phi', phi_atol=5.,
                       psi_col='eu.chi', psi_atol=.1, psi_max=90.)
    analysis_ = analysis.squeeze(axis=0)
    print(analysis_)

    for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
        if peak_id not in set(analysis_.index.get_level_values(0)):
            continue

        fig = plt.figure(peak_id)
        fig.suptitle(peak_id_str(dd, peak_id))
        ax1, ax2 = plt.subplot(121), plt.subplot(122)

        for proj in analysis_[peak_id].index:
            if '+' in proj:
                ax1.plot(analysis_[peak_id][proj].xdata, analysis_[peak_id][proj].ydata, '+', label=proj)
                ax1.plot(analysis_[peak_id][proj].xdata, analysis_[peak_id][proj].ycalc, '--', label=None, color='black')
            elif '-' in proj:
                ax2.plot(analysis_[peak_id][proj].xdata, analysis_[peak_id][proj].ydata, '+', label=proj)
                ax2.plot(analysis_[peak_id][proj].xdata, analysis_[peak_id][proj].ycalc, '--', label=None, color='black')
        ax1.set_xlabel(r'$\sin^2(\psi)$')
        ax2.set_xlabel(r'$\sin(2\psi)$')
        ax1.set_ylabel(r'd [AA]')
        ax2.set_ylabel(r'd [AA]')
        ax1.legend()
        ax2.legend()
        plt.tight_layout()

    for phase in phases.keys():
        print(phase, phases[phase])
        analysis_ = analysis.drop(
            columns=[col for col in set(analysis.columns.get_level_values(0)) if col not in phases[phase]],
            level=0
        )
        stresses = deviatoric_stresses(dd, analysis_, dec[phase])
        stresses = stresses.squeeze(axis=0)

        print(stresses)

        plt.figure('Deviatoric stresses %s' % phase)
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
        plt.xlabel('Information depth [μm]')
        plt.ylabel('Stress [MPa]')
        plt.legend()
    plt.show()
