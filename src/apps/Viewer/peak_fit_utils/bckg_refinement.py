import numpy as np
from uncertainties import ufloat
from scipy.optimize import least_squares
from matplotlib import pyplot as plt

from peak_fit_utils.peak_refinement import get_peak_intervals
from peak_fit_utils.models import peak_models, background_models


class BckgData:
    def __init__(self, model):
        self.md_name = model

        self.md_params = dict()
        self.md_p_bounds = dict()
        self.md_p_refine = dict()

        self._poly_coefs = np.zeros(100) + 1
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
            return dict()
        else:
            return dict()

    def set_poly_coefs(self, new_coefs):
        for ii in range(len(new_coefs)):
            self._poly_coefs[ii] = new_coefs[ii]


def fit_bckg(peak_list, bckg_list, xx, yy):
    intervals = get_peak_intervals(peak_list)

    y_calc_peaks = np.zeros(yy.shape)

    for peak in peak_list:
        y_calc_peaks += peak_models[peak.md_name](xx, **{name: peak.md_params[name].n for name in peak.md_params})

    for bc_md in bckg_list:
        iy = (yy - y_calc_peaks)[(xx > bc_md.md_params['xmin'].n) & (xx < bc_md.md_params['xmax'].n)]
        ix = xx[(xx > bc_md.md_params['xmin'].n) & (xx < bc_md.md_params['xmax'].n)]

        def residuals(x, *args, **kwargs):
            y_calc = background_models[bc_md.md_name](ix, xmin=bc_md.md_params['xmin'].n,
                                                      xmax=bc_md.md_params['xmax'].n,
                                                      **{'c%d' % ii: val for ii, val in enumerate(x)})
            return (iy - y_calc) ** 2

        x0 = bc_md.func_params
        x0.pop('xmin')
        x0.pop('xmax')
        x0 = [x0[k] for k in sorted(x0.keys())]

        opt_result = least_squares(residuals, x0=x0, ftol=None, xtol=None, max_nfev=5000)
        print(opt_result)
        bc_md.set_poly_coefs(opt_result.x)

    return bckg_list