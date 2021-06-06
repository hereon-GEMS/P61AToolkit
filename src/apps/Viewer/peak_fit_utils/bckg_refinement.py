import numpy as np
from uncertainties import ufloat


class BckgData:
    def __init__(self, model):
        self.md_name = model

        self.md_params = dict()
        self.md_p_bounds = dict()
        self.md_p_refine = dict()

        self._poly_coefs = np.zeros(100)
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


def fit_bckg(bckg_list, xx, yy):
    return bckg_list