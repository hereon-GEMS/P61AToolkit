import numpy as np
from uncertainties import ufloat
from scipy.optimize import least_squares
import copy

import logging

from peak_fit_utils.models import peak_models, background_models
from peak_fit_utils.metrics import upd_metrics
from peak_fit_utils.peak_refinement import get_peak_intervals
from utils import log_ex_time

logger = logging.getLogger('peak_fit_utils')


class BckgData:
    def __init__(self, model):
        self.md_name = model

        self.md_params = dict()
        self.md_p_bounds = dict()
        self.md_p_refine = dict()

        self._poly_coefs = np.zeros(100) + 1
        self._interp_fn = lambda x: np.zeros(x.shape)
        self.make_md_params()

    def make_md_params(self):
        self.md_params, self.md_p_bounds = dict(), dict()

        if self.md_name == 'Chebyshev':
            self.md_params['xmin'] = ufloat(0, np.NAN)
            self.md_params['xmax'] = ufloat(200, np.NAN)
            self.md_params['degree'] = ufloat(7, np.NAN)

            self.md_p_bounds['xmin'] = (-np.inf, np.inf)
            self.md_p_bounds['xmax'] = (-np.inf, np.inf)
            self.md_p_bounds['degree'] = (0, 11)
        elif self.md_name == 'Interpolation':
            self.md_params['xmin'] = ufloat(0, np.NAN)
            self.md_params['xmax'] = ufloat(200, np.NAN)
            self.md_params['degree'] = ufloat(1, np.NAN)

            self.md_p_bounds['xmin'] = (-np.inf, np.inf)
            self.md_p_bounds['xmax'] = (-np.inf, np.inf)
            self.md_p_bounds['degree'] = (1, 3)
        else:
            pass

    @property
    def func_params(self):
        if self.md_name == 'Chebyshev':
            result = {'xmin': self.md_params['xmin'].n, 'xmax': self.md_params['xmax'].n}
            if 'degree' in self.md_params:
                deg = int(self.md_params['degree'].n)
                for ii in range(deg):
                    result['c%d' % ii] = self._poly_coefs[ii]
            return result
        elif self.md_name == 'Interpolation':
            result = {'func': self._interp_fn}
            return result
        else:
            return dict()

    def set_poly_coefs(self, new_coefs):
        for ii in range(len(new_coefs)):
            self._poly_coefs[ii] = new_coefs[ii]
        self._poly_coefs[len(new_coefs):] = 0.

    def to_dict(self):
        result = dict()
        result['md_name'] = self.md_name
        result['md_params'] = {k: (self.md_params[k].n, self.md_params[k].s) for k in self.md_params.keys()}
        result['md_p_bounds'] = self.md_p_bounds
        result['md_p_refine'] = self.md_p_refine
        if self.md_name == 'Chebyshev':
            result['poly_coefs'] = self._poly_coefs[:int(self.md_params['degree'].n) + 1].tolist()
        return result

    @classmethod
    def from_dict(cls, data):
        result = cls(model=data['md_name'])
        result.md_params = {k: ufloat(*data['md_params'][k]) for k in data['md_params'].keys()}
        result.md_p_bounds = data['md_p_bounds']
        result.md_p_refine = data['md_p_refine']
        if result.md_name == 'Chebyshev':
            result.set_poly_coefs(data['poly_coefs'])
        return result


class InterpFunc:
    def __init__(self, ixs, iys):
        self.ixs = ixs
        self.iys = iys

    def __call__(self, x):
        result = np.zeros(x.shape)
        cond = (x < np.max(self.ixs)) & (x > np.min(self.ixs))
        result[cond] = np.interp(x[cond], self.ixs, self.iys)
        return result


@log_ex_time(logger=logger)
def fit_bckg(peak_list, bckg_list, xx, yy):
    y_calc_peaks = np.zeros(yy.shape)

    for peak in peak_list:
        y_calc_peaks += peak_models[peak.md_name](xx, **{name: peak.md_params[name].n for name in peak.md_params})

    for bc_md in bckg_list:
        if bc_md.md_name != 'Interpolation':
            iy = (yy - y_calc_peaks)[(xx > bc_md.md_params['xmin'].n) & (xx < bc_md.md_params['xmax'].n)]
            ix = xx[(xx > bc_md.md_params['xmin'].n) & (xx < bc_md.md_params['xmax'].n)]

            logger.info('fit_bckg: refining background on [%d, %d]' % (bc_md.md_params['xmin'].n,
                                                                                         bc_md.md_params['xmax'].n))

            def residuals(x, *args, **kwargs):
                y_calc = background_models[bc_md.md_name](ix, xmin=bc_md.md_params['xmin'].n,
                                                          xmax=bc_md.md_params['xmax'].n,
                                                          **{'c%d' % ii: val for ii, val in enumerate(x)})
                return ((iy - y_calc) / np.max(iy)) ** 2

            x0 = bc_md.func_params
            x0.pop('xmin')
            x0.pop('xmax')
            x0 = [x0[k] for k in sorted(x0.keys())]

            opt_result = least_squares(residuals, x0=x0, ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=1000)
            bc_md.set_poly_coefs(opt_result.x)
        else:
            interp_xs = xx.copy()
            interp_ys = yy.copy()
            interp_xs = interp_xs[(xx > bc_md.md_params['xmin'].n) & (xx < bc_md.md_params['xmax'].n)]
            interp_ys = interp_ys[(xx > bc_md.md_params['xmin'].n) & (xx < bc_md.md_params['xmax'].n)]
            for ll, rr, *_ in get_peak_intervals(peak_list):
                interp_ys = interp_ys[(interp_xs < ll) | (interp_xs > rr)]
                interp_xs = interp_xs[(interp_xs < ll) | (interp_xs > rr)]

            bc_md._interp_fn = InterpFunc(interp_xs, interp_ys)

    chi2, peak_list = upd_metrics(peak_list, bckg_list, xx, yy)

    return chi2, bckg_list, peak_list