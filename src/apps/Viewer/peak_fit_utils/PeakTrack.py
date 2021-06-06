import numpy as np
import pandas as pd
import copy
from uncertainties import ufloat


prefixes = {'Gaussian': 'gau',
            'Lorentzian': 'lor',
            'Pearson7': 'pvii',
            'PseudoVoigt': 'pv',
            'SplitLorentzian': 'spl',
            'Interpolation': 'int',
            'Chebyshev': 'che'}


class PeakData:
    def __init__(self, idx, cx, cy, l_ip, r_ip, l_b, r_b, l_bh, r_bh, model='PseudoVoigt'):
        """

        """
        self._cx = cx
        self._cy = cy
        self._l_ip = l_ip
        self._r_ip = r_ip
        self._l_b = l_b
        self._r_b = r_b
        self._l_bh = l_bh
        self._r_bh = r_bh

        self._track = None
        self._idx = idx

        self.md_name = model
        self.md_prefix = prefixes[model]
        self.md_params = dict()
        self.md_p_bounds = dict()
        self.md_p_refine = dict()

        self.make_md_params()

    def make_md_params(self):
        self.md_params, self.md_p_bounds = dict(), dict()

        if self.md_name == 'PseudoVoigt':
            self.md_params['width'] = ufloat(self.peak_width, np.NAN)
            self.md_params['sigma'] = self.md_params['width'] / (2. * np.sqrt(2. * np.log(2)))
            self.md_params['center'] = ufloat(self.cx, np.NAN)
            self.md_params['amplitude'] = self.peak_height * np.sqrt(2. * np.pi) * \
                                          self.md_params['sigma'] / np.sqrt(2. * np.log(2))
            self.md_params['height'] = ufloat(self.peak_height, np.NAN)
            self.md_params['fraction'] = ufloat(0., np.NAN)
            self.md_params['base'] = ufloat(3., np.NAN)
            self.md_params['overlap_base'] = ufloat(1e-2, np.NAN)
            self.md_params['rwp'] = ufloat(np.NAN, np.NAN)
            self.md_params['chi2'] = ufloat(np.NAN, np.NAN)

            self.md_p_bounds['width'] = (0., np.inf)
            # self.md_p_bounds['sigma'] = (0.9 * self.md_params['sigma'].n, 1.1 * self.md_params['sigma'].n)
            self.md_p_bounds['sigma'] = (1e-4, 1.0)
            self.md_p_bounds['center'] = (self.md_params['center'].n - .5 * self.md_params['width'].n,
                                          self.md_params['center'].n + .5 * self.md_params['width'].n)
            self.md_p_bounds['amplitude'] = (0., 1e7)
            self.md_p_bounds['height'] = (0., np.inf)
            self.md_p_bounds['fraction'] = (0., 1.)
            self.md_p_bounds['base'] = (0., np.inf)
            self.md_p_bounds['overlap_base'] = (0., np.inf)
            self.md_p_bounds['rwp'] = (0., np.inf)
            self.md_p_bounds['chi2'] = (0., np.inf)

            self.md_p_refine['sigma'] = True
            self.md_p_refine['center'] = True
            self.md_p_refine['amplitude'] = True
            self.md_p_refine['fraction'] = True

    def upd_nref_params(self):
        if self.md_name == 'PseudoVoigt':
            self.md_params['width'] = self.md_params['sigma'] * (2. * np.sqrt(2. * np.log(2)))
            self.md_params['height'] = self.md_params['amplitude'] / (
                        np.sqrt(2. * np.pi) * self.md_params['sigma'] / np.sqrt(2. * np.log(2)))

            self.md_p_bounds['width'] = (
                self.md_p_bounds['sigma'][0] * (2. * np.sqrt(2. * np.log(2))),
                self.md_p_bounds['sigma'][1] * (2. * np.sqrt(2. * np.log(2)))
            )
            self.md_p_bounds['height'] = (self.md_p_bounds['amplitude'][0] / (
                    np.sqrt(2. * np.pi) * self.md_params['sigma'].n / np.sqrt(2. * np.log(2))),
                                          self.md_p_bounds['amplitude'][1] / (
                                                  np.sqrt(2. * np.pi) * self.md_params['sigma'].n / np.sqrt(
                                              2. * np.log(2)))
                                          )

    def md_param_keys(self):
        ref = tuple(k for k in self.md_params if k in self.md_p_refine)
        n_ref = tuple(k for k in self.md_params if k not in self.md_p_refine)
        return ref + n_ref

    def __copy__(self):
        return PeakData(self._idx, self._cx, self._cy,
                        self._l_ip, self._r_ip,
                        self._l_b, self._r_b, self._l_bh, self._r_bh)

    @property
    def cx(self):
        return self._cx

    @cx.setter
    def cx(self, val):
        self._cx = val

    @property
    def cy(self):
        return self._cy

    @cy.setter
    def cy(self, val):
        self._cy = val

    @property
    def idx(self):
        return self._idx

    @idx.setter
    def idx(self, val):
        self._idx = val

    @property
    def bckg_height(self):
        return np.mean([self._l_bh, self._r_bh])

    @property
    def peak_height(self):
        return np.abs(self.cy - self.bckg_height)

    @property
    def peak_width(self):
        return self._r_ip - self._l_ip

    @property
    def l_b(self):
        return self._l_b

    @l_b.setter
    def l_b(self, val):
        self._l_b = val

    @property
    def l_bh(self):
        return self._l_bh

    @l_bh.setter
    def l_bh(self, val):
        self.l_bh = val

    @property
    def r_b(self):
        return self._r_b

    @r_b.setter
    def r_b(self, val):
        self._r_b = val

    @property
    def r_bh(self):
        return self._l_bh

    @r_bh.setter
    def r_bh(self, val):
        self._r_bh = val

    @property
    def l_ip(self):
        return self._l_ip

    @l_ip.setter
    def l_ip(self, val):
        self._l_ip = val

    @property
    def r_ip(self):
        return self._r_ip

    @r_ip.setter
    def r_ip(self, val):
        self._r_ip = val

    @property
    def track(self):
        return self._track

    @track.setter
    def track(self, val):
        if not isinstance(val, (type(None), PeakDataTrack)):
            raise ValueError('Track should be PeakDataTrack or None')
        self._track = val


class PeakDataTrack:
    """
    Stores peaks that are in the same position across all spectra
    """
    def __init__(self, pd: PeakData):
        self._peaks = []
        self.append(pd)

    def __copy__(self):
        peaks = [copy.copy(peak) for peak in self._peaks]
        result = PeakDataTrack(peaks[0])
        for ii in range(1, len(peaks)):
            result.append(peaks[ii])
        return result

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        while self._peaks:
            self._peaks[0].track = None
            del self._peaks[0]

    def dist(self, pd: PeakData):
        return np.abs(self._peaks[-1].cx - pd.cx)

    def append(self, pd: PeakData):
        self._peaks.append(pd)
        self._peaks[-1].track = self
        self.sort_ids()

    def sort_ids(self):
        self._peaks = list(sorted(self._peaks, key=lambda x: x.idx))

    @property
    def series(self):
        xs, ys = [], []
        for peak in self._peaks:
            xs.append(peak.idx)
            ys.append(peak.cx)
        return pd.Series(data=ys, index=xs)

    @property
    def ids(self):
        return [peak.idx for peak in self._peaks]

    @property
    def cxs(self):
        return [peak.cx for peak in self._peaks]

    @property
    def cys(self):
        return [peak.cy for peak in self._peaks]

    @property
    def l_bs(self):
        return [peak.l_b for peak in self._peaks]

    @property
    def r_bs(self):
        return [peak.r_b for peak in self._peaks]

    @property
    def l_bhs(self):
        return [peak.l_bh for peak in self._peaks]

    @property
    def r_bhs(self):
        return [peak.r_bh for peak in self._peaks]

    @property
    def l_ips(self):
        return [peak.l_ip for peak in self._peaks]

    @property
    def r_ips(self):
        return [peak.r_ip for peak in self._peaks]

    def __getitem__(self, item):
        for peak in self._peaks:
            if peak.idx == item:
                return peak
        else:
            raise KeyError('Key %s not found' % str(item))

    def __lt__(self, other):
        return np.mean(self.cxs).__lt__(np.mean(other.cxs))

    def predict_by_average(self, idx, data_x, data_y):
        weights = np.sqrt(self.cys)
        mcx = np.average(self.cxs, weights=weights)
        mlb = np.average(self.l_bs, weights=weights)
        mrb = np.average(self.r_bs, weights=weights)
        mlip = np.average(self.l_ips, weights=weights)
        mrip = np.average(self.r_ips, weights=weights)

        data_y = data_y[(data_x <= mrb) & (data_x >= mlb)]
        cy = np.max(data_y) - np.min(data_y) + 1

        return PeakData(idx, mcx, cy, mlip, mrip, mlb, mrb, np.min(data_y), np.min(data_y))

    def shift_xs(self, by=0.):
        for peak in self._peaks:
            peak.cx += by
            peak.l_b += by
            peak.r_b += by
            peak.l_ip += by
            peak.r_ip += by

    def compress_energies(self, new_range):
        avg_e = np.mean(self.cxs)
        min_e = np.min(self.cxs)
        max_e = np.max(self.cxs)

        new_min = (avg_e * (max_e - min_e) - new_range * (avg_e - min_e)) / (max_e - min_e)
        new_max = new_range + new_min

        for peak in self._peaks:
            if peak.cx > new_max:
                shift = new_max - peak.cx
            elif peak.cx < new_min:
                shift = new_min - peak.cx
            else:
                shift = 0.

            peak.cx += shift
            peak.l_b += shift
            peak.r_b += shift
            peak.l_ip += shift
            peak.r_ip += shift