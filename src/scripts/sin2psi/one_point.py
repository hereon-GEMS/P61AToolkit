import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, valid_peaks, peak_id_str
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import sin2psi, MultiWaveLength


if __name__ == '__main__':
    element = 'Fe'
    dd = read_peaks(r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_1-4.csv')
    tth = 15.

    # calculating d values
    for peak_id in valid_peaks(dd, valid_for='sin2psi'):
        d_val = bragg(en=unumpy.uarray(dd[(peak_id, 'center')], dd[(peak_id, 'center_std')]), tth=tth)['d']
        dd[(peak_id, 'd')] = unumpy.nominal_values(d_val)
        dd[(peak_id, 'd_std')] = unumpy.std_devs(d_val)

    analysis = sin2psi(dataset=dd, phi_col='eu.phi', phi_atol=5.,
                       psi_col='eu.chi', psi_atol=.1, psi_max=90.)

    for peak_id in valid_peaks(dd, valid_for='sin2psi'):
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
    plt.show()
