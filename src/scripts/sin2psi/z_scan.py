import pandas as pd
from matplotlib import pyplot as plt
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, valid_peaks, group_by_motors, peak_id_str
from py61a.cryst_utils import bragg
from py61a.stress import sin2psi, deviatoric_stresses


if __name__ == '__main__':
    # read the data
    dd = read_peaks(r'Z:\p61\2021\commissioning\c20210813_000_gaf_2s21\processed\com4pBending_fullScan_01712.csv')
    dec = pd.read_csv(r'../../../data/dec/bccFe.csv', index_col=None, comment='#')

    # calculate the d values from peak positions
    tth = dd[('md', 'd1.rx')].mean()
    for peak_id in valid_peaks(dd, valid_for='sin2psi'):
        d_val = bragg(en=unumpy.uarray(dd[(peak_id, 'center')], dd[(peak_id, 'center_std')]), tth=tth)['d']
        dd[(peak_id, 'd')] = unumpy.nominal_values(d_val)
        dd[(peak_id, 'd_std')] = unumpy.std_devs(d_val)

    # defining the scan: it was over eu.z
    dd = group_by_motors(dd, motors=[{'mot_name': 'eu.z', 'atol': 1e-3}])

    analysis = sin2psi(dataset=dd, phi_col='eu.phi', phi_atol=5.,
                       psi_col='eu.chi', psi_atol=.1, psi_max=90.)
    print(analysis)

    stress = deviatoric_stresses(dd, analysis, dec)
    stress = stress.reset_index()
    stress.set_index('eu.z', inplace=True)
    z_pos = dd[[('scanpts', 'eu.z'), ('md', 'eu.z')]].groupby(by=('scanpts', 'eu.z')).mean()

    plt.figure()
    for peak_id in set(stress.columns.get_level_values(0)):
        ax1, ax2 = plt.subplot(121), plt.subplot(122)
        print(unumpy.std_devs(stress.loc[:, (peak_id, 's22-s33')]))

        if 's11-s33' in stress[peak_id].columns:
            ax1.errorbar(
                x=z_pos.loc[stress.index].values.flatten(),
                y=unumpy.nominal_values(stress.loc[:, (peak_id, 's11-s33')]),
                yerr=unumpy.std_devs(stress.loc[:, (peak_id, 's11-s33')]),
                marker='x', linestyle='', label=peak_id_str(dd, peak_id)
            )
        if 's22-s33' in stress[peak_id].columns:
            ax2.errorbar(
                x=z_pos.loc[stress.index].values.flatten(),
                y=unumpy.nominal_values(stress.loc[:, (peak_id, 's22-s33')]),
                yerr=unumpy.std_devs(stress.loc[:, (peak_id, 's22-s33')]),
                marker='x', linestyle='', label=peak_id_str(dd, peak_id)
            )

    ax1.legend()
    ax2.legend()
    plt.show()

