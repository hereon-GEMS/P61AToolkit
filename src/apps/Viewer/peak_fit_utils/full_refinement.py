import logging

from peak_fit_utils.metrics import upd_metrics
from peak_fit_utils.bckg_refinement import fit_bckg
from peak_fit_utils.peak_refinement import fit_peaks


logger = logging.getLogger('peak_fit_utils')


def fit_to_precision(peak_list, bckg_list, xx, yy, max_cycles=10, min_chi_change=0.1):
    chi2, peak_list = upd_metrics(peak_list, bckg_list, xx, yy)
    cond, ii = True, 1

    while cond:
        chi2_, bckg_list, peak_list = fit_bckg(peak_list, bckg_list, xx, yy)
        chi2_, bckg_list, peak_list = fit_peaks(peak_list, bckg_list, xx, yy)

        if 0 < (chi2 - chi2_) / chi2_ < min_chi_change:
            cond = False
        else:
            chi2 = chi2_

        if ii >= max_cycles:
            cond = False
        else:
            ii += 1

        logger.info('fit_to_precision: cycle %d, chi2 = %e' % (ii, chi2))

    chi2, peak_list = upd_metrics(peak_list, bckg_list, xx, yy)
    return chi2, bckg_list, peak_list