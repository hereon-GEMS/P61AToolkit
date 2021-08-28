from multiprocessing import Pool, cpu_count
from scipy.optimize import least_squares
from uncertainties import ufloat
import numpy as np
import logging

from peak_fit_utils.models import peak_models, background_models
from peak_fit_utils.metrics import upd_metrics
from utils import log_ex_time

logger = logging.getLogger('peak_fit_utils')


def get_peak_intervals(peak_list):
    """
    This is the most important function here. It defines the way each spectrum is separated into areas that can be used
    for refinement independently. The logic goes as follows:
    1. Go through all peak-type models in the composite. For each calculate its overlap base.
    2. Do a recursive merge of all overlap bases: if two overlap bases intersect they become one
    3. All peak models that have their centers within an overlap base have to be refined together
    4. For each overlap base a refinement base is calculated. This one defines an area over which the functions will be
    calculated.
    Note that base does not mean that peak function is set to 0 everywhere outside of it like some fitting programs do.
    """

    def recursive_merge(inter, start_index=0):
        for i in range(start_index, len(inter) - 1):
            if (min(inter[i + 1]) <= inter[i][0] <= max(inter[i + 1])) or \
                    (min(inter[i + 1]) <= inter[i][1] <= max(inter[i + 1])):
                inter[i] = [min(inter[i][0], inter[i + 1][0]), max(inter[i][1], inter[i + 1][1])] + inter[i][2:] + inter[i + 1][2:]
                del inter[i + 1]
                return recursive_merge(inter.copy(), start_index=i)
        return inter

    overlap_intervals = [
        [peak.md_params['center'].n - peak.md_params['overlap_base'].n * peak.md_params['sigma'].n,
            peak.md_params['center'].n + peak.md_params['overlap_base'].n * peak.md_params['sigma'].n]
        for peak in peak_list
    ]

    overlap_intervals = recursive_merge(overlap_intervals, 0)

    result = []
    for l, r in overlap_intervals:
        tmp = []
        for ii, peak in enumerate(peak_list):
            if l < peak.md_params['center'].n < r:
                tmp.append([
                    peak.md_params['center'].n - peak.md_params['base'].n * peak.md_params['sigma'].n,
                    peak.md_params['center'].n + peak.md_params['base'].n * peak.md_params['sigma'].n,
                ii])
        result.extend(recursive_merge(tmp, 0))

    return list(sorted(result, key=lambda x: x[0]))


class IntervalOptimizer:
    def __init__(self, peak_list, xdata, ydata, optimizer):
        self.peak_list = peak_list
        self.xdata = xdata
        self.ydata = ydata
        self.opt = optimizer

    def __call__(self, interval):
        ll, rr, *peak_ids = interval
        logger.info('IntervalOptimizer.__call__: refining peaks (%s) on [%d, %d]' % (str(peak_ids), ll, rr))
        iy = self.ydata[(self.xdata > ll) & (self.xdata < rr)]
        ix = self.xdata[(self.xdata > ll) & (self.xdata < rr)]
        iy, ix = iy.astype(np.float64), ix.astype(np.float64)

        iy_c_static = np.zeros(iy.shape)
        for ii in range(len(self.peak_list)):
            if ii not in peak_ids:
                iy_c_static += peak_models[self.peak_list[ii].md_name](ix,
                                                                       **{name: self.peak_list[ii].md_params[name].n for name
                                                                     in
                                                                     self.peak_list[ii].md_params})
        iy -= iy_c_static

        refined_params = {ii: [k for k in self.peak_list[ii].md_p_refine.keys() if
                               self.peak_list[ii].md_p_refine[k]] for ii in peak_ids}
        kwds = {ii: {k: self.peak_list[ii].md_params[k].n
                     for k in self.peak_list[ii].md_p_refine.keys() if not self.peak_list[ii].md_p_refine[k]}
                for ii in peak_ids}

        def residuals(x, *args, **kwargs):
            ycalc = np.zeros(iy.shape)
            shift = 0
            for ii in peak_ids:
                x_ = x[shift:]
                ycalc += peak_models[self.peak_list[ii].md_name](ix, **(kwds[ii]), **{name: val for (name, val) in
                                                                                      zip(refined_params[ii], x_)})
                shift += len(refined_params[ii])
            return (iy - ycalc)**2

        x0 = tuple([self.peak_list[ii].md_params[k].n for ii in peak_ids for k in self.peak_list[ii].md_p_refine.keys()
              if self.peak_list[ii].md_p_refine[k]])
        bounds = np.array([self.peak_list[ii].md_p_bounds[k] for ii in peak_ids for k in self.peak_list[ii].md_p_refine.keys()
              if self.peak_list[ii].md_p_refine[k]]).T

        opt_result = self.opt(residuals, x0=x0, bounds=bounds)
        cov = np.sqrt(np.diagonal(np.linalg.inv(opt_result.jac.T.dot(opt_result.jac))))

        idx = 0
        for ii in peak_ids:
            for k in self.peak_list[ii].md_p_refine.keys():
                if self.peak_list[ii].md_p_refine[k]:
                    self.peak_list[ii].md_params[k] = ufloat(opt_result.x[idx], cov[idx])
                    idx += 1

        return self.peak_list


@log_ex_time(logger=logger)
def fit_peaks(peak_list, bckg_list, xx, yy):
    intervals = get_peak_intervals(peak_list)

    yy_calc_bckg = np.zeros(yy.shape)

    for bc_md in bckg_list:
        yy_calc_bckg += background_models[bc_md.md_name](xx, **bc_md.func_params)

    # parallel = True  # 22151.7 ms
    parallel = False  # 718.5 ms

    iopt = IntervalOptimizer(peak_list, xx, yy - yy_calc_bckg, least_squares)
    if not parallel:
        for interval in intervals:
            try:
                peak_list = iopt(interval)
            except Exception as e:
                print(type(e), e)
                logger.error('fit_peaks: error %s' % str(e))
    else:
        with Pool(cpu_count()) as p:
            upd_peaks = p.map(iopt, intervals)

        for interval, upd in zip(intervals, upd_peaks):
            for ii in interval[2:]:
                peak_list[ii] = upd[ii]

    peak_list = list(sorted(peak_list, key=lambda item: item.md_params['center']))

    for peak in peak_list:
        lb, rb = peak.md_params['center'].n - peak.md_params['base'].n * peak.md_params['sigma'].n, \
                 peak.md_params['center'].n + peak.md_params['base'].n * peak.md_params['sigma'].n

        peak.upd_nref_params(lr_bh=np.interp([lb, rb], xx, yy_calc_bckg))
    chi2, peak_list = upd_metrics(peak_list, bckg_list, xx, yy)
    return chi2, bckg_list, peak_list
