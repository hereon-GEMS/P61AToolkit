import numpy as np
from uncertainties import ufloat

from peak_fit_utils.models import peak_models, background_models


def metrics(yy_o, yy_c):
    rwp2 = np.sum((1. / yy_o) * ((yy_o - yy_c) ** 2)) / np.sum((1. / yy_o) * (yy_o ** 2))
    rexp2 = yy_o.shape[0] / np.sum((1. / yy_o) * yy_o ** 2)
    return {'chi2': rwp2 / rexp2, 'rwp2': rwp2, 'rexp2': rexp2}


def upd_metrics(peak_list, bckg_list, xx, yy):
    yy_calc_bckg = np.zeros(yy.shape)
    for bc_md in bckg_list:
        yy_calc_bckg += background_models[bc_md.md_name](xx, **bc_md.func_params)

    y_calc_peaks = np.zeros(yy.shape)
    for peak in peak_list:
        y_calc_peaks += peak_models[peak.md_name](xx, **{name: peak.md_params[name].n for name in peak.md_params})

    for peak in peak_list:
        xmin, xmax = peak.md_params['center'].n - peak.md_params['base'].n * peak.md_params['sigma'].n, \
                     peak.md_params['center'].n + peak.md_params['base'].n * peak.md_params['sigma'].n

        mcs = metrics(
            yy[(xx > xmin) & (xx < xmax)],
            (y_calc_peaks + yy_calc_bckg)[(xx > xmin) & (xx < xmax)]
        )

        peak.md_params['rwp2'] = ufloat(mcs['rwp2'], np.NAN)
        peak.md_params['chi2'] = ufloat(mcs['chi2'], np.NAN)

    if len(bckg_list) == 0:
        total_chi2 = metrics(yy, y_calc_peaks)['chi2']
    else:
        y_c_w_bg = np.array([])
        y_o_w_bg = np.array([])
        for bc_md in bckg_list:
            y_c_w_bg = np.concatenate([y_c_w_bg, (y_calc_peaks + yy_calc_bckg)[
                (xx > bc_md.md_params['xmin']) & (xx < bc_md.md_params['xmax'])]])
            y_o_w_bg = np.concatenate([y_o_w_bg, yy[
                (xx > bc_md.md_params['xmin']) & (xx < bc_md.md_params['xmax'])]])
        total_chi2 = metrics(y_o_w_bg, y_c_w_bg)['chi2']
    return total_chi2, peak_list