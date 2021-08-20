import numpy as np
import pandas as pd
from uncertainties import unumpy, ufloat
from .sin2psi import Sin2Psi
from .hooke import hooke


class MultiWaveLength:
    def __init__(self, analysis: Sin2Psi, dec: pd.DataFrame, d0: pd.DataFrame):
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
            d0_ = None
            for _, row in d0.iterrows():
                if row['h'] == analysis.peak_md[peak]['h'] and \
                        row['k'] == analysis.peak_md[peak]['k'] and \
                        row['l'] == analysis.peak_md[peak]['l']:
                    d0_ = ufloat(row['d0'], row['d0_std'])
                    break
            s1, hs2 = None, None
            for _, row in dec.iterrows():
                if row['h'] == analysis.peak_md[peak]['h'] and \
                        row['k'] == analysis.peak_md[peak]['k'] and \
                        row['l'] == analysis.peak_md[peak]['l']:
                    s1 = row['s1']
                    hs2 = row['hs2']
                    break
            if (d0_ is None) or (s1 is None) or (hs2 is None):
                continue
            else:
                e11[ii] = (analysis[peak, '0+180'].uslope + analysis[peak, '0+180'].uintercept - d0_) / d0_
                e22[ii] = (analysis[peak, '90+270'].uslope + analysis[peak, '90+270'].uintercept - d0_) / d0_
                e33[ii] = (0.5 * (analysis[peak, '0+180'].uintercept + analysis[peak, '90+270'].uintercept) - d0_) / d0_

                e13[ii] = analysis[peak, '0-180'].uslope / d0_
                e23[ii] = analysis[peak, '90-270'].uslope / d0_

                s = hooke(np.array([
                    [[e11[ii]], [e12[ii]], [e13[ii]]],
                    [[e12[ii]], [e22[ii]], [e23[ii]]],
                    [[e13[ii]], [e23[ii]], [e33[ii]]]
                ]), s1, hs2)

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