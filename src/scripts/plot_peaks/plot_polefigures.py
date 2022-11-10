import numpy as np
from matplotlib import pyplot as plt
from uncertainties import unumpy

from py61a.viewer_utils import read_peaks, get_peak_ids, peak_id_str


if __name__ == '__main__':
    peakfile = r'Z:\current\processed\Steel_texture.csv'
    alp = 'eu.chi'  # polar angle, tilting (psi)
    bet = 'eu.phi'  # azimuth angle, rotation (phi)
    # usedPar = 'center'
    # usedPar = 'sigma'
    usedPar = 'amplitude'
    # usedPar = 'height'

    dd = read_peaks(peakfile)
    # dd[('md', bet)] = (dd[('md', bet)] - 45) % 360

    # selecting relevant data and plot pole figures
    for peak_id in get_peak_ids(dd, columns=('h', 'k', 'l', usedPar, usedPar + '_std')):
        used_val = unumpy.uarray(dd[(peak_id, usedPar)], dd[(peak_id, usedPar + '_std')])
        det_val = unumpy.nominal_values(used_val)
        std_val = unumpy.std_devs(used_val)
        alp_val = dd[('md', alp)]
        bet_val = dd[('md', bet)]

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='polar')
        c = ax.scatter(np.deg2rad(bet_val), np.tan(np.deg2rad(0.5 * alp_val)), c=det_val, cmap='jet')
        fig.colorbar(c, orientation='vertical')
        ax.set_title(peak_id_str(dd, peak_id).replace('[', '(').replace(']', ')'))
        plt.tight_layout()  # layout without overlapping
        plt.show()
