import os
import itertools
import pandas as pd
from matplotlib import pyplot as plt
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, get_peak_ids, peak_id_str
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import sin2psi, deviatoric_stresses

if __name__ == '__main__':
	# this script handles exported peak fit data of P61A:Viewer for sin2psi measurement in reflection mode

	# general parameters
	plot_sin2psi = True
	plot_stresses = True
	export_sin2psi = True
	export_stresses = True
	res_file_delim = ','
	file_mwl_fit_append = '_mwl_fit.csv'
	file_mwl_stresses_append = '_mwl_stresses.csv'
	polar_motor = 'eu.chi'
	azimuth_motor = 'eu.phi'

	# measurement specific parameters
	element = 'Fe'
	peakfile = r'Z:\current\processed\Steel_sample.csv'
	decfile = r'../../../data/dec/bccFe.csv'
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

	# calculating d values and depth
	for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
		d_val = bragg(en=unumpy.uarray(dd[(peak_id, 'center')], dd[(peak_id, 'center_std')]), tth=tth)['d']
		dd[(peak_id, 'd')] = unumpy.nominal_values(d_val)
		dd[(peak_id, 'd_std')] = unumpy.std_devs(d_val)
		dd[(peak_id, 'depth')] = tau(mu(element, dd[(peak_id, 'center')].mean()), tth=tth, psi=dd[('md', polar_motor)],
			eta=90.)

	# perform sin2psi analysis and calculate stresses
	analysis = sin2psi(dataset=dd, phi_col=azimuth_motor, phi_atol=5., psi_col=polar_motor, psi_atol=.1, psi_min=min_psi,
		psi_max=max_psi)
	stresses = deviatoric_stresses(dd, analysis, dec)
	analysis = analysis.squeeze(axis=0)
	stresses = stresses.squeeze(axis=0)

	# show results on screen
	print(analysis)
	print(stresses)

	if export_sin2psi:
		# export sin2psi regression results
		file, ext = os.path.splitext(peakfile)
		fid = open(file + file_mwl_fit_append, 'w')
		sin2psi_head_groups = list(itertools.product(analysis.index.get_level_values(1).unique(),
			('slope', 'slope_std', 'intercept', 'intercept_std')))
		sin2psi_head = list((r[1] + '_' + r[0] for r in sin2psi_head_groups))
		fid.write('%s\n' % res_file_delim.join(('peak_id', 'peak_name', *sin2psi_head)))
		for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
			if peak_id in set(analysis.index.get_level_values(0)):
				cur_val_str = res_file_delim.join((peak_id, peak_id_str(dd, peak_id)))
				for sin2psi_head_group in sin2psi_head_groups:
					cur_val_str += '%s%g' % (res_file_delim, eval('analysis[("' + peak_id + '", "' + sin2psi_head_group[0] + '")].' + sin2psi_head_group[1]))
				fid.write(cur_val_str + '\n')
		fid.close()

	if export_stresses:
		# export stresses
		file, ext = os.path.splitext(peakfile)
		fid = open(file + file_mwl_stresses_append, 'w')
		fid.write('%s\n' % res_file_delim.join((
			'peak_id', 'peak_name', 'depth_min', 'depth_max', 'depth', 's11-s33', 'std_s11-s33', 's22-s33',
			'std_s22-s33', 's13', 'std_s13', 's23', 'std_s23')))
		for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
			if peak_id in set(stresses.index.get_level_values(0)):
				fid.write((res_file_delim.join(2 * ('%s',)) + res_file_delim + res_file_delim.join(
					3 * ('%g',)) + res_file_delim + res_file_delim.join(8 * ('%.0f',)) + '\n') % (
							peak_id, peak_id_str(dd, peak_id), stresses[(peak_id, 'depth_min')],
							stresses[(peak_id, 'depth_max')], stresses[(peak_id, 'depth')],
							stresses[(peak_id, 's11-s33')].n, stresses[(peak_id, 's11-s33')].s,
							stresses[(peak_id, 's22-s33')].n, stresses[(peak_id, 's22-s33')].s,
							stresses[(peak_id, 's13')].n, stresses[(peak_id, 's13')].s, stresses[(peak_id, 's23')].n,
							stresses[(peak_id, 's23')].s))
		fid.close()

	if plot_sin2psi:
		# plot sin2psi curves
		for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', 'center', 'center_std')):
			if peak_id not in set(analysis.index.get_level_values(0)):
				continue
			fig = plt.figure(peak_id)
			fig.suptitle(peak_id_str(dd, peak_id))
			ax1, ax2 = plt.subplot(121), plt.subplot(122)
			for proj in analysis[peak_id].index:
				if '+' in proj:
					ax1.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ydata, '+', label=proj)
					ax1.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ycalc, '--', label=None,
						color='black')
				elif '-' in proj:
					ax2.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ydata, '+', label=proj)
					ax2.plot(analysis[peak_id][proj].xdata, analysis[peak_id][proj].ycalc, '--', label=None,
						color='black')
			ax1.set_xlabel(r'$\sin^2(\psi)$')
			ax2.set_xlabel(r'$\sin(2\psi)$')
			ax1.set_ylabel(r'd [AA]')
			ax2.set_ylabel(r'd [AA]')
			ax1.legend()
			ax2.legend()
			plt.tight_layout()

	if plot_stresses:
		# plot deviatoric stress results
		plt.figure('Deviatoric stresses')
		plt.errorbar(x=stresses[stresses.index.get_level_values(1) == 'depth'],
			y=stresses[stresses.index.get_level_values(1) == 's11-s33'].apply(lambda x: x.n),
			yerr=stresses[stresses.index.get_level_values(1) == 's11-s33'].apply(lambda x: x.s),
			label=r'$\sigma_{11}-\sigma_{33}$', marker='x', linestyle='')
		plt.errorbar(x=stresses[stresses.index.get_level_values(1) == 'depth'],
			y=stresses[stresses.index.get_level_values(1) == 's22-s33'].apply(lambda x: x.n),
			yerr=stresses[stresses.index.get_level_values(1) == 's22-s33'].apply(lambda x: x.s),
			label=r'$\sigma_{22}-\sigma_{33}$', marker='x', linestyle='')
		plt.xlabel('Information depth [μm]')
		plt.ylabel('Stress [MPa]')
		plt.legend()

		# plot shear stress results
		plt.figure('Shear stresses')
		plt.errorbar(x=stresses[stresses.index.get_level_values(1) == 'depth'],
			y=stresses[stresses.index.get_level_values(1) == 's13'].apply(lambda x: x.n),
			yerr=stresses[stresses.index.get_level_values(1) == 's13'].apply(lambda x: x.s), label=r'$\sigma_{13}$',
			marker='x', linestyle='')
		plt.errorbar(x=stresses[stresses.index.get_level_values(1) == 'depth'],
			y=stresses[stresses.index.get_level_values(1) == 's23'].apply(lambda x: x.n),
			yerr=stresses[stresses.index.get_level_values(1) == 's23'].apply(lambda x: x.s), label=r'$\sigma_{23}$',
			marker='x', linestyle='')
		plt.xlabel('Information depth [μm]')
		plt.ylabel('Stress [MPa]')
		plt.legend()

		plt.show()
