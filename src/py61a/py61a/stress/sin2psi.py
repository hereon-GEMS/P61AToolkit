import numpy as np
import pandas as pd
from uncertainties import ufloat

from py61a.viewer_utils import valid_peaks, peak_id_str
from scipy.optimize import curve_fit
from functools import partial


class Sin2PsiObject:
    def __init__(self, xdata, ydata, depth, slope=None, intercept=None):
        self.x = xdata
        self.y = ydata
        self.depth = depth

        ids = np.isnan(self.x) | np.isnan(self.y) | np.isnan(self.depth)
        self.x, self.y, self.depth = self.x[~ids], self.y[~ids], self.depth[~ids]

        if self.x.size == 0 or self.y.size == 0:
            self.slope = np.nan
            self.intercept = np.nan
            self.slope_std = np.nan
            self.intercept_std = np.nan
            return

        def f(x, slp, intr):
            return x * slp + intr

        if slope is None and intercept is None:
            popt, pcov = curve_fit(f, self.x, self.y, p0=(0., 0.))
            pcov = np.sqrt(np.diag(pcov))
            self.slope = popt[0]
            self.intercept = popt[1]
            self.slope_std = pcov[0]
            self.intercept_std = pcov[1]
        elif slope is None and intercept is not None:
            f = partial(f, intr=intercept)
            popt, pcov = curve_fit(f, self.x, self.y, p0=(0.,))
            pcov = np.sqrt(np.diag(pcov))
            self.slope = popt[0]
            self.intercept = intercept
            self.slope_std = pcov[0]
            self.intercept_std = np.nan
        elif slope is not None and intercept is None:
            f = partial(f, slp=slope)
            popt, pcov = curve_fit(f, self.x, self.y, p0=(0.,))
            pcov = np.sqrt(np.diag(pcov))
            self.slope = slope
            self.intercept = popt[0]
            self.slope_std = np.nan
            self.intercept_std = pcov[0]
        else:
            self.slope = np.nan
            self.intercept = np.nan
            self.slope_std = np.nan
            self.intercept_std = np.nan

    @property
    def y_calc(self):
        return self.slope * self.x + self.intercept

    @property
    def y_median(self):
        return self.slope * 0.5 + self.intercept

    @property
    def uslope(self):
        return ufloat(self.slope, self.slope_std)

    @property
    def uintercept(self):
        return ufloat(self.intercept, self.intercept_std)

    def __repr__(self):
        return '%f * x + %f' % (self.slope, self.intercept)


class Sin2Psi:
    """
    Performs sin^2(psi) analysis of the provided data.

    """

    _projections = '0+180', '0-180', '90+270', '90-270', '45+225', '45-225', '135+315', '135-315'
    phi_values = (0, 45, 90, 135, 180, 225, 270, 315)

    def __init__(self, dataset):

        self.peak_md = dict()
        self.data = pd.DataFrame(columns=self._projections, index=pd.Index([], dtype=str))

        self._prep_peak_data(dataset)

    def d_star(self, peak_str_id):
        result = []
        for projection in self.projections:
            if '+' in projection:
                result.append(self.data.loc[peak_str_id, projection].intercept)
        result = np.array(result)
        result = result[~np.isnan(result)]
        return np.mean(result)

    @property
    def projections(self):
        return self.data.columns

    @property
    def peaks(self):
        return self.data.index

    def __getitem__(self, item):
        return self.data.loc[item]

    def _prep_peak_data(self, dataset):
        for peak_id in valid_peaks(dataset, valid_for='sin2psi'):
            str_id = peak_id_str(dataset, peak_id)
            self.peak_md[str_id] = {
                'h': dataset[peak_id]['h'].mean().astype(np.int),
                'k': dataset[peak_id]['k'].mean().astype(np.int),
                'l': dataset[peak_id]['l'].mean().astype(np.int),
            }

            peak_data = dataset[[('groups', 'eu.phi'), ('groups', 'eu.chi'), ('md', 'eu.chi'), (peak_id, 'd'),
                                 (peak_id, 'depth')]]
            for phi_g_idx in range(len(self.phi_values) // 2):
                def invert_e(row):
                    if row[('groups', 'eu.phi')] == phi_g_idx + len(self.phi_values) // 2:
                        row[(peak_id, 'd')] = -row[(peak_id, 'd')]
                    return row

                proj_data = pd.concat((
                    peak_data[peak_data[('groups', 'eu.phi')] == phi_g_idx],
                    peak_data[peak_data[('groups', 'eu.phi')] == (phi_g_idx + len(self.phi_values) // 2)]
                ))

                d1 = proj_data.groupby(by=('groups', 'eu.chi')).mean()
                self.data.loc[
                    str_id, '%d+%d' % (self.phi_values[phi_g_idx],
                                       self.phi_values[phi_g_idx + len(self.phi_values) // 2])] = Sin2PsiObject(
                    np.sin(np.radians(d1[('md', 'eu.chi')].to_numpy(copy=True))) ** 2,
                    d1[(peak_id, 'd')].to_numpy(copy=True),
                    d1[(peak_id, 'depth')].to_numpy(copy=True)
                )

                d2 = proj_data.apply(invert_e, axis=1)
                d2 = d2.groupby(by=('groups', 'eu.chi')).mean()
                self.data.loc[
                    str_id, '%d-%d' % (self.phi_values[phi_g_idx],
                                       self.phi_values[phi_g_idx + len(self.phi_values) // 2])] = Sin2PsiObject(
                    np.sin(2. * np.radians(d2[('md', 'eu.chi')].to_numpy(copy=True))),
                    d2[(peak_id, 'd')].to_numpy(copy=True),
                    d2[(peak_id, 'depth')].to_numpy(copy=True),
                    intercept=0.
                )

    def d_star_transform(self, peak):
        def forw(x):
            return (x - self.d_star(peak)) / self.d_star(peak)

        def back(x):
            return x * (1. + self.d_star(peak))

        return forw, back
