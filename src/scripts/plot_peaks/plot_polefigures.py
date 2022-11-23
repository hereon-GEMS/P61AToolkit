import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, get_peak_ids, peak_id_str, peak_hkl_str

if __name__ == '__main__':
	peakfile = r'Z:\current\processed\Steel_texture.csv'
	alp = 'eu.chi'  # polar angle, tilting (psi)
	bet = 'eu.phi'  # azimuth angle, rotation (phi)
	only_valid_vals = True
	show_polefigures = True
	export_data = True
	file_exp_append = '_pf.ifwtex'
	# usedPar = 'center'
	# usedPar = 'sigma'
	usedPar = 'amplitude'
	# usedPar = 'height'

	dd = read_peaks(peakfile)
	# dd[('md', bet)] = (dd[('md', bet)] - 45) % 360

	if export_data:
		file, ext = os.path.splitext(peakfile)
		fid = open(file + file_exp_append, 'w')
		fid.write('%s\n' % '\t'.join(('psi', 'phi', 'int', 'hkl')))

	# selecting relevant data and plot pole figures
	for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', usedPar, usedPar + '_std')):
		used_val = unumpy.uarray(dd[(peak_id, usedPar)], dd[(peak_id, usedPar + '_std')])
		det_val = unumpy.nominal_values(used_val)
		std_val = unumpy.std_devs(used_val)
		alp_val = dd[('md', alp)].to_numpy()
		bet_val = dd[('md', bet)].to_numpy()

		if only_valid_vals:
			alp_val = alp_val[~pd.isna(det_val)]
			bet_val = bet_val[~pd.isna(det_val)]
			det_val = det_val[~pd.isna(det_val)]

		if export_data:
			res_vals = np.transpose(np.array((alp_val, bet_val, det_val, np.ones(det_val.shape) * int(peak_hkl_str(dd, peak_id)))))
			np.savetxt(fid,  res_vals, fmt='%g', delimiter='\t')

		if show_polefigures:
			fig = plt.figure()
			ax = fig.add_subplot(111, projection='polar')
			c = ax.scatter(np.deg2rad(bet_val), np.tan(np.deg2rad(0.5 * alp_val)), c=det_val, cmap='jet')
			fig.colorbar(c, orientation='vertical')
			ax.set_title(peak_id_str(dd, peak_id).replace('[', '(').replace(']', ')'))
			plt.tight_layout()  # layout without overlapping
			plt.show()

	if export_data:
		fid.close()
