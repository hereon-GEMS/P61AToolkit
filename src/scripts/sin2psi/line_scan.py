import os
import itertools
import pandas as pd
from matplotlib import pyplot as plt
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, get_peak_ids, peak_id_str, group_by_motors
from py61a.cryst_utils import bragg
from py61a.stress import sin2psi, deviatoric_stresses


if __name__ == '__main__':
    # this script handles exported peak fit data of P61A:Viewer for sin2psi measurement with line scan in transmission mode

    # general parameters
    plot_stresses = True
    export_stresses = True
    res_file_delim = ','
    file_linescan_stresses_append = '_linescan_stresses.csv'
    polar_motor = 'eu.chi'
    azimuth_motor = 'eu.phi'

    # measurement specific parameters
    peakfile = r'Z:\current\processed\Steel_sample_line.csv'
    decfile = r'../../../data/dec/bccFe.csv'
    scan_motor = 'eu.z'  # scan axis
    min_psi = -90.
    max_psi = 90.
    # tth_axis = 'd0.rz'  # relevant diffraction angle of detector 0 (horizontal)
    tth_axis = 'd1.rx'  # relevant diffraction angle of detector 1 (vertical)

    # import the data, set tth value and check azimuth and polar angles
    dd = read_peaks(peakfile)
    tth = abs(dd[('md', tth_axis)].mean())
    # tth = 8.4  # input manual value if wanted
    if dd[('md', tth_axis)].mean() < 0:  # for horizontal detector
        dd[('md', polar_motor)] = dd[('md', polar_motor)] - 90
    # dd[('md', azimuth_motor)] = (dd[('md', azimuth_motor)] - 45) % 360

    # import DEC values
    dec = pd.read_csv(decfile, index_col=None, comment='#')

    # calculating d values
    for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
        d_val = bragg(en=unumpy.uarray(dd[(peak_id, 'center')], dd[(peak_id, 'center_std')]), tth=tth)['d']
        dd[(peak_id, 'd')] = unumpy.nominal_values(d_val)
        dd[(peak_id, 'd_std')] = unumpy.std_devs(d_val)

    # grouping data based on scan axis
    dd = group_by_motors(dd, motors=[{'mot_name': scan_motor, 'atol': 1e-3}])

    # perform sin2psi analysis and calculate stresses
    analysis = sin2psi(dataset=dd, phi_col=azimuth_motor, phi_atol=5.,
                       psi_col=polar_motor, psi_atol=.1, psi_min=min_psi, psi_max=max_psi)
    scan_pos = dd[[('scanpts', scan_motor), ('md', scan_motor)]].groupby(by=('scanpts', scan_motor)).mean()
    stresses = deviatoric_stresses(dd, analysis, dec)
    stresses = stresses.reset_index()
    stresses.set_index(scan_motor, inplace=True)

    # show results on screen
    # print(stresses)
    for peak_id in sorted(set(stresses.columns.get_level_values(0))):
        print(peak_id_str(dd, peak_id))
        print(stresses[peak_id])

    if export_stresses:
        # export stresses
        file, ext = os.path.splitext(peakfile)
        fid = open(file + file_linescan_stresses_append, 'w')
        fid.write('%s\n' % res_file_delim.join((
            'peak_id', 'peak_name', scan_motor, 's11-s33', 'std_s11-s33', 's22-s33',
            'std_s22-s33', 's13', 'std_s13', 's23', 'std_s23')))
        for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
            if peak_id in set(stresses.columns.get_level_values(0)):
                for i in stresses.index:
                    fid.write((res_file_delim.join(2 * ('%s',)) + res_file_delim + '%g' + res_file_delim +
                               res_file_delim.join(8 * ('%.0f',)) + '\n') % (
                                  peak_id, peak_id_str(dd, peak_id), scan_pos.loc[i].values,
                                  stresses.loc[i, (peak_id, 's11-s33')].n, stresses.loc[i, (peak_id, 's11-s33')].s,
                                  stresses.loc[i, (peak_id, 's22-s33')].n, stresses.loc[i, (peak_id, 's22-s33')].s,
                                  stresses.loc[i, (peak_id, 's13')].n, stresses.loc[i, (peak_id, 's13')].s,
                                  stresses.loc[i, (peak_id, 's23')].n, stresses.loc[i, (peak_id, 's23')].s))
        fid.close()

    if plot_stresses:
        # plot deviatoric stress results
        plt.figure('Deviatoric stresses', figsize=(16, 4))
        for peak_id in set(stresses.columns.get_level_values(0)):
            ax1, ax2 = plt.subplot(121), plt.subplot(122)
            ax1.set_title(r'$\sigma_{11}-\sigma_{33}$')
            ax2.set_title(r'$\sigma_{22}-\sigma_{33}$')
            ax1.set_xlabel(scan_motor + ' [mm]')
            ax2.set_xlabel(scan_motor + ' [mm]')
            ax1.set_ylabel('$\sigma_{11}-\sigma_{33}$ [MPa]')
            ax2.set_ylabel('$\sigma_{22}-\sigma_{33}$ [MPa]')
            if 's11-s33' in stresses[peak_id].columns:
                ax1.errorbar(
                    x=scan_pos.loc[stresses.index].values.flatten(),
                    y=unumpy.nominal_values(stresses.loc[:, (peak_id, 's11-s33')]),
                    yerr=unumpy.std_devs(stresses.loc[:, (peak_id, 's11-s33')]),
                    marker='x', linestyle='', label=peak_id_str(dd, peak_id)
                )
            if 's22-s33' in stresses[peak_id].columns:
                ax2.errorbar(
                    x=scan_pos.loc[stresses.index].values.flatten(),
                    y=unumpy.nominal_values(stresses.loc[:, (peak_id, 's22-s33')]),
                    yerr=unumpy.std_devs(stresses.loc[:, (peak_id, 's22-s33')]),
                    marker='x', linestyle='', label=peak_id_str(dd, peak_id)
                )
        ax1.legend()
        ax2.legend()

        # plot shear stress results
        plt.figure('Shear stresses', figsize=(16, 4))
        for peak_id in set(stresses.columns.get_level_values(0)):
            ax1, ax2 = plt.subplot(121), plt.subplot(122)
            ax1.set_title(r'$\sigma_{13}$')
            ax2.set_title(r'$\sigma_{23}$')
            ax1.set_xlabel(scan_motor + ' [mm]')
            ax2.set_xlabel(scan_motor + ' [mm]')
            ax1.set_ylabel('$\sigma_{13}$ [MPa]')
            ax2.set_ylabel('$\sigma_{23}$ [MPa]')
            if 's13' in stresses[peak_id].columns:
                ax1.errorbar(
                    x=scan_pos.loc[stresses.index].values.flatten(),
                    y=unumpy.nominal_values(stresses.loc[:, (peak_id, 's13')]),
                    yerr=unumpy.std_devs(stresses.loc[:, (peak_id, 's13')]),
                    marker='x', linestyle='', label=peak_id_str(dd, peak_id)
                )
            if 's23' in stresses[peak_id].columns:
                ax2.errorbar(
                    x=scan_pos.loc[stresses.index].values.flatten(),
                    y=unumpy.nominal_values(stresses.loc[:, (peak_id, 's23')]),
                    yerr=unumpy.std_devs(stresses.loc[:, (peak_id, 's23')]),
                    marker='x', linestyle='', label=peak_id_str(dd, peak_id)
                )
        ax1.legend()
        ax2.legend()

        plt.show()
