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
    def uslope(self):
        return ufloat(self.slope, self.slope_std)

    @property
    def uintercept(self):
        return ufloat(self.intercept, self.intercept_std)


class Sin2Psi:
    """
    Performs sin^2(psi) analysis of the provided data.

    """

    _projections = '0+180', '0-180', '90+270', '90-270', '45+225', '45-225', '135+315', '135-315'

    def __init__(self, dataset, phi_atol=5., psi_atol=.1, psi_max=45.,
                 phi_col_name=('md', 'eu.phi'), psi_col_name=('md', 'eu.chi')):

        # grouping data by phi, psi
        # phis within phi_atol degrees are grouped together
        # psis within psi_atol degrees are grouped together
        # psis larger than psi_max degrees are discarded
        dataset[('md', 'phi.group')] = self.phi_group(dataset[phi_col_name], atol=phi_atol)
        dataset[('md', 'psi.group')] = self.psi_group(dataset[psi_col_name], psi_max, atol=psi_atol)
        dataset = dataset[dataset[('md', 'psi.group')] != -1]

        self.peak_md = dict()
        self.data = pd.DataFrame(columns=self._projections, index=pd.Index([], dtype=str))

        self._prep_peak_data(dataset, psi_col_name)

    @property
    def projections(self):
        return self.data.columns

    @property
    def peaks(self):
        return self.data.index

    def __getitem__(self, item):
        return self.data.loc[item]

    def _prep_peak_data(self, dataset, psi_col_name):
        for peak_id in valid_peaks(dataset, valid_for=None):
            str_id = peak_id_str(dataset, peak_id)

            self.peak_md[str_id] = {
                'h': dataset[peak_id]['h'].mean().astype(np.int),
                'k': dataset[peak_id]['k'].mean().astype(np.int),
                'l': dataset[peak_id]['l'].mean().astype(np.int),
                's1': dataset[peak_id]['s1'].mean(),
                'hs2': dataset[peak_id]['hs2'].mean(),
                'd0': dataset[peak_id]['d0'].mean(),
            }

            peak_data = dataset[[('md', 'phi.group'), ('md', 'psi.group'), psi_col_name, (peak_id, 'd'),
                                 (peak_id, 'depth')]]
            for phi in (0, 45, 90, 135):
                def invert_e(row):
                    if row[('md', 'phi.group')] == phi + 180:
                        row[(peak_id, 'd')] = -row[(peak_id, 'd')]
                    return row

                proj_data = pd.concat((
                    peak_data[peak_data[('md', 'phi.group')] == phi],
                    peak_data[peak_data[('md', 'phi.group')] == (phi + 180)]
                ))

                d1 = proj_data.groupby(by=('md', 'psi.group')).mean()
                self.data.loc[str_id, '%d+%d' % (phi, phi + 180)] = Sin2PsiObject(
                    np.sin(np.radians(d1[psi_col_name].to_numpy(copy=True))) ** 2,
                    d1[(peak_id, 'd')].to_numpy(copy=True),
                    d1[(peak_id, 'depth')].to_numpy(copy=True)
                )

                d2 = proj_data.apply(invert_e, axis=1)
                d2 = d2.groupby(by=('md', 'psi.group')).mean()
                self.data.loc[str_id, '%d-%d' % (phi, phi + 180)] = Sin2PsiObject(
                    np.sin(2. * np.radians(d2[psi_col_name].to_numpy(copy=True))),
                    d2[(peak_id, 'd')].to_numpy(copy=True),
                    d2[(peak_id, 'depth')].to_numpy(copy=True),
                    intercept=0.
                )

    @staticmethod
    def phi_group(phis, atol=5.):
        result = np.zeros(phis.shape) + np.NAN
        for phi in np.linspace(0, 360, 45):
            result[np.isclose(phis, phi, atol=atol)] = phi
        result = result.astype(np.int)
        return result

    @staticmethod
    def psi_group(psis, cutoff, atol=0.1):
        result = np.zeros(psis.shape) - 1

        ii, unique_values = 0, np.array(psis).copy()
        while ii < unique_values.size:
            unique_values = unique_values[
                (~np.isclose(unique_values, unique_values[ii], atol=atol)) |
                (np.arange(0, unique_values.size) == ii)
                ]
            ii += 1

        for ii, psi in enumerate(unique_values):
            if psi < cutoff:
                result[np.isclose(psi, psis, atol=atol)] = ii

        result = result.astype(np.int)
        return result
