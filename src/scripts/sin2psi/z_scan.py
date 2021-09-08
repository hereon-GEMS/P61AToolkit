import pandas as pd
from matplotlib import pyplot as plt
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, get_peak_ids, group_by_motors, peak_id_str
from py61a.cryst_utils import bragg
from py61a.stress import sin2psi, deviatoric_stresses


if __name__ == '__main__':
    dd = read_peaks((r'../../../data/peaks/TiLSP/phi0Trans_3.csv', r'../../../data/peaks/TiLSP/phi90Trans_4.csv'))
    tth_ch1 = 5.274
    dec = pd.read_csv(r'../../../data/dec/alphaTi.csv', index_col=None, comment='#')

    for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
        d_val = bragg(en=unumpy.uarray(dd[(peak_id, 'center')], dd[(peak_id, 'center_std')]), tth=tth_ch1)['d']
        dd[(peak_id, 'd')] = unumpy.nominal_values(d_val)
        dd[(peak_id, 'd_std')] = unumpy.std_devs(d_val)

    # defining the scan: it was over eu.z
    dd = group_by_motors(dd, motors=[{'mot_name': 'eu.z', 'atol': 1e-3}])

    analysis = sin2psi(dataset=dd, phi_col='eu.phi', phi_atol=5.,
                       psi_col='eu.chi', psi_atol=.1, psi_max=90.)

    stress = deviatoric_stresses(dd, analysis, dec)
    stress = stress.reset_index()
    stress.set_index('eu.z', inplace=True)
    z_pos = dd[[('scanpts', 'eu.z'), ('md', 'eu.z')]].groupby(by=('scanpts', 'eu.z')).mean()

    plt.figure(figsize=(16, 4))
    for peak_id in set(stress.columns.get_level_values(0)):
        ax1, ax2 = plt.subplot(121), plt.subplot(122)
        ax1.set_title(r'$\sigma_{11}-\sigma_{33}$')
        ax2.set_title(r'$\sigma_{22}-\sigma_{33}$')
        ax1.set_xlabel('eu.z [mm]')
        ax2.set_xlabel('eu.z [mm]')
        ax1.set_ylabel('$\sigma_{11}-\sigma_{33}$ [MPa]')
        ax2.set_ylabel('$\sigma_{22}-\sigma_{33}$ [MPa]')

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