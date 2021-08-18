from .sin2psi import Sin2Psi
import numpy as np
from uncertainties import unumpy, ufloat


class StressBaseClass:
    def __init__(self, sin2psi: Sin2Psi):
        self.depths = None
        self.depths_min = None
        self.depths_max = None
        self._get_depths(sin2psi)

    def _get_depths(self, sin2psi):
        tau_mean, tau_min, tau_max = [], [], []
        for peak in sin2psi.peaks:
            depths = []
            for projection in sin2psi.projections:
                depths.append(sin2psi[peak, projection].depth)
            depths = np.concatenate(depths)
            if depths.size == 0:
                tau_mean.append(np.nan)
                tau_min.append(np.nan)
                tau_max.append(np.nan)
            else:
                tau_mean.append(np.mean(depths))
                tau_min.append(np.min(depths))
                tau_max.append(np.max(depths))

        self.depths = np.array(tau_mean)
        self.depths_min = np.array(tau_min)
        self.depths_max = np.array(tau_max)

    @property
    def depth_xerr(self):
        mi = self.depths - self.depths_min
        ma = self.depths_max - self.depths
        return mi, ma


class DeviatoricStresses(StressBaseClass):
    def __init__(self, sin2psi: Sin2Psi, dec):
        StressBaseClass.__init__(self, sin2psi)

        self.s11m33 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)
        self.s22m33 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)

        for ii, peak in enumerate(sin2psi.peaks):
            tmp = dec[
                dec['h'] == sin2psi.peak_md[peak]['h']
                ][
                dec['k'] == sin2psi.peak_md[peak]['k']
                ][
                dec['l'] == sin2psi.peak_md[peak]['l']
                ]
            self.s11m33[ii] = (1. / tmp['hs2'].mean()) * sin2psi[peak, '0+180'].uslope / \
                              sin2psi[peak, '0+180'].uintercept
            self.s22m33[ii] = (1. / tmp['hs2'].mean()) * sin2psi[peak, '90+270'].uslope / \
                              sin2psi[peak, '90+270'].uintercept

        ids = np.argsort(self.depths)
        self.depths, self.depths_min, self.depths_max, self.s11m33, self.s22m33 = \
            self.depths[ids], self.depths_min[ids], self.depths_max[ids], self.s11m33[ids], self.s22m33[ids]

    @property
    def s11m33_n(self):
        return unumpy.nominal_values(self.s11m33)

    @property
    def s11m33_std(self):
        return unumpy.std_devs(self.s11m33)

    @property
    def s22m33_n(self):
        return unumpy.nominal_values(self.s22m33)

    @property
    def s22m33_std(self):
        return unumpy.std_devs(self.s22m33)