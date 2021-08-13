import numpy as np
from uncertainties import unumpy, ufloat
from .sin2psi import Sin2Psi
from .hooke import hooke


class MultiWaveLength:
    def __init__(self, analysis: Sin2Psi):
        tau_mean, tau_min, tau_max = [], [], []
        for peak in analysis.peaks:
            depths = []
            for projection in analysis.projections:
                depths.append(analysis[peak, projection].depth)
            depths = np.concatenate(depths)
            tau_mean.append(np.mean(depths))
            tau_min.append(np.min(depths))
            tau_max.append(np.max(depths))

        self.depths = np.array(tau_mean)
        self.depths_min = np.array(tau_min)
        self.depths_max = np.array(tau_max)

        e11 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)
        e12 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)
        e13 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)
        e22 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)
        e23 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)
        e33 = np.array([ufloat(np.nan, np.nan)] * self.depths.size)
        stress_tensor = np.zeros((3, 3, self.depths.size)) + ufloat(np.nan, np.nan)

        for ii, peak in enumerate(analysis.peaks):
            d0 = analysis.peak_md[peak]['d0']
            e11[ii] = (analysis[peak, '0+180'].uslope + analysis[peak, '0+180'].uintercept - d0) / d0
            e22[ii] = (analysis[peak, '90+270'].uslope + analysis[peak, '90+270'].uintercept - d0) / d0
            e33[ii] = (0.5 * (analysis[peak, '0+180'].uintercept + analysis[peak, '90+270'].uintercept) - d0) / d0

            e13[ii] = analysis[peak, '0-180'].uslope / d0
            e23[ii] = analysis[peak, '90-270'].uslope / d0

            s = hooke(np.array([
                [[e11[ii]], [e12[ii]], [e13[ii]]],
                [[e12[ii]], [e22[ii]], [e23[ii]]],
                [[e13[ii]], [e23[ii]], [e33[ii]]]
            ]), analysis.peak_md[peak]['s1'], analysis.peak_md[peak]['hs2'])

            stress_tensor[:, :, ii] = s[:, :, 0]

        ids = np.argsort(self.depths)
        self.depths, self.depths_min, self.depths_max = self.depths[ids], self.depths_min[ids], self.depths_max[ids]
        e11, e12, e13, e22, e23, e33 = e11[ids], e12[ids], e13[ids], e22[ids], e23[ids], e33[ids]
        stress_tensor = stress_tensor[:, :, ids]

        self.stress_tensor = stress_tensor
        self.strain_tensor = np.array([
            [e11, e12, e13],
            [e12, e22, e23],
            [e13, e23, e33]
        ])

    @property
    def depth_xerr(self):
        mi = self.depths - self.depths_min
        ma = self.depths_max - self.depths
        return mi, ma

    @property
    def stress_tensor_n(self):
        return unumpy.nominal_values(self.stress_tensor)

    @property
    def stress_tensor_std(self):
        return unumpy.std_devs(self.stress_tensor)

    @property
    def strain_tensor_n(self):
        return unumpy.nominal_values(self.strain_tensor)

    @property
    def strain_tensor_std(self):
        return unumpy.std_devs(self.strain_tensor)