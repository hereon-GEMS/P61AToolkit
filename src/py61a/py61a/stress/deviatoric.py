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
            print(ii, sin2psi[peak])