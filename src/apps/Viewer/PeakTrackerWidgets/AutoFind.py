import copy

from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QDialog, QAbstractItemView, QProgressDialog
from PyQt5.Qt import Qt
from scipy.signal import find_peaks
import numpy as np
import pandas as pd

from P61App import P61App
from FitWidgets.FloatEdit import FloatEdit
from DatasetManager import DatasetSelector


class PeakData:
    def __init__(self, idx, cx, cy, l_ip, r_ip, l_b, r_b, l_bh, r_bh):
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


class AutoFindPopUp(QDialog):
    """"""

    def __init__(self, parent=None):
        QDialog.__init__(self, parent=parent)
        self.q_app = P61App.instance()

        self.btn_ok = QPushButton('Search', parent=self)
        self.selection_list = DatasetSelector(parent=self)

        self.setWindowTitle('Auto search for peaks')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.btn_ok, 2, 1, 1, 1)
        layout.addWidget(self.selection_list, 1, 1, 1, 1)

        self.btn_ok.clicked.connect(self.on_btn_ok)

    def on_btn_ok(self):
        # fit_ids = [k for k in self.selection_list.proxy.selected if self.selection_list.proxy.selected[k]]
        fit_ids = self.selection_list.get_selected()

        progress = QProgressDialog("Searching", "Cancel", 0, len(fit_ids))
        progress.setWindowModality(Qt.ApplicationModal)

        for ii in fit_ids:
            self.parent().on_btn_this(idx=ii, emit=False)
            progress.setValue(ii)

        self.q_app.peakListChanged.emit(fit_ids)
        progress.setValue(len(fit_ids))

        self.close()


class AutoFindWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()

        self.title_label = QLabel('                ')

        self.height_label = QLabel('Height')
        self.height_label.setToolTip('Required minimal height of peaks. Either a number or None.')
        self.height_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=20.)
        self.thr_label = QLabel('Threshhold')
        self.thr_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=None)
        self.dist_label = QLabel('Distance')
        self.dist_label.setToolTip('Required minimal horizontal distance between neighbouring peaks.\n'
                                   'Smaller peaks are removed first until the condition is fulfilled '
                                   'for all remaining peaks.')
        self.dist_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=5E-1)
        self.prom_label = QLabel('Prominence')
        self.prom_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=10.)
        self.width_label = QLabel('Width')
        self.width_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=5E-2)
        self.width_label.setToolTip('Required minimal width of peaks. Either a number or None.')
        self.cutoff_label = QLabel('Cutoff')
        self.cutoff_edit = FloatEdit(inf_allowed=True, none_allowed=True, init_val=5.)
        self.cutoff_label.setToolTip('Peak base cutoff measured in sigmas.')
        self.tw_label = QLabel('Track window')
        self.tw_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=3E-1)
        self.tw_label.setToolTip('Max peak shift between the spectra.')
        # self.btn_this = QPushButton('Find')
        # self.btn_this.setDisabled(True)
        self.btn_all = QPushButton('Find')
        self.btn_stack = QPushButton('Make tracks')

        # self.btn_this.clicked.connect(self.on_btn_this)
        self.btn_all.clicked.connect(self.on_btn_all)
        self.btn_stack.clicked.connect(self.on_btn_stack)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.title_label, 1, 1, 1, 2)

        layout.addWidget(self.height_label, 2, 1, 1, 1)
        layout.addWidget(self.height_edit, 2, 2, 1, 1)

        layout.addWidget(self.dist_label, 3, 1, 1, 1)
        layout.addWidget(self.dist_edit, 3, 2, 1, 1)

        layout.addWidget(self.width_label, 4, 1, 1, 1)
        layout.addWidget(self.width_edit, 4, 2, 1, 1)

        layout.addWidget(self.thr_label, 5, 1, 1, 1)
        layout.addWidget(self.thr_edit, 5, 2, 1, 1)

        layout.addWidget(self.prom_label, 6, 1, 1, 1)
        layout.addWidget(self.prom_edit, 6, 2, 1, 1)

        layout.addWidget(self.cutoff_label, 7, 1, 1, 1)
        layout.addWidget(self.cutoff_edit, 7, 2, 1, 1)

        # layout.addWidget(self.btn_this, 8, 1, 1, 1)
        layout.addWidget(self.btn_all, 8, 2, 1, 1)

        layout.addWidget(self.tw_label, 9, 1, 1, 1)
        layout.addWidget(self.tw_edit, 9, 2, 1, 1)

        layout.addWidget(self.btn_stack, 10, 2, 1, 2)

    def on_btn_stack(self):
        tw = self.tw_edit.get_value()
        ids = self.q_app.get_active_ids()
        tracks = []

        for idx in ids:
            for pdt in self.q_app.get_peak_data_list(idx):
                for track in tracks:
                    if track.dist(pdt) <= tw:
                        track.append(pdt)
                        break
                else:
                    tracks.append(PeakDataTrack(pdt))

        tracks = list(sorted(tracks, key=lambda x: np.mean(x.cxs)))
        self.q_app.set_pd_tracks(tracks)

    def on_btn_this(self, *args, idx=-1, emit=True):
        params = {
            'height': self.height_edit.get_value(),
            'threshold': self.thr_edit.get_value(),
            'distance': self.dist_edit.get_value(),
            'prominence': self.prom_edit.get_value(),
            'width': self.width_edit.get_value()
        }
        cutoff = self.cutoff_edit.get_value()
        if cutoff is None:
            cutoff = np.inf

        if idx == -1:
            idx = self.q_app.get_selected_idx()

        if idx != -1:
            yy = self.q_app.data.loc[idx, 'DataY']
            xx = self.q_app.data.loc[idx, 'DataX']

            if self.q_app.peak_search_range is not None:
                yy = yy[(xx < self.q_app.peak_search_range[1]) & (xx > self.q_app.peak_search_range[0])]
                xx = xx[(xx < self.q_app.peak_search_range[1]) & (xx > self.q_app.peak_search_range[0])]

            if params['distance'] is not None:
                params['distance'] /= np.abs(np.max(xx) - np.min(xx)) / xx.shape[0]
                params['distance'] = params['distance'] if params['distance'] >= 1. else 1.
            if params['width'] is not None:
                params['width'] /= np.abs(np.max(xx) - np.min(xx)) / xx.shape[0]

            for pp in params:
                if pp != 'distance' and params[pp] is None:
                    params[pp] = (None, None)

            result_idx = find_peaks(yy, **params)
            pos_x = xx[result_idx[0]]
            pos_y = yy[result_idx[0]]
            left_ips = np.interp(result_idx[1]['left_ips'], np.arange(0, xx.shape[0]), xx)
            right_ips = np.interp(result_idx[1]['right_ips'], np.arange(0, xx.shape[0]), xx)
            width_heights = result_idx[1]['width_heights']

            if cutoff < np.inf:
                g_sigmas = (right_ips - left_ips) / (2. * np.sqrt(2. * np.log(2)))
                left_bases = pos_x - cutoff * g_sigmas
                right_bases = pos_x + cutoff * g_sigmas
                left_bases_heights = np.interp(left_bases, xx, yy)
                right_bases_heights = np.interp(right_bases, xx, yy)
            else:
                left_bases = xx[result_idx[1]['left_bases']]
                right_bases = xx[result_idx[1]['right_bases']]
                left_bases_heights = yy[result_idx[1]['left_bases']]
                right_bases_heights = yy[result_idx[1]['right_bases']]

            sort_ids = np.argsort(left_bases)
            peak_data_list = []

            for lb, rb, li, ri, wh, cx, cy, lbh, rbh in zip(left_bases[sort_ids], right_bases[sort_ids],
                                                            left_ips[sort_ids],
                                                            right_ips[sort_ids], width_heights[sort_ids],
                                                            pos_x[sort_ids],
                                                            pos_y[sort_ids], left_bases_heights[sort_ids],
                                                            right_bases_heights[sort_ids]):
                peak_data_list.append(
                    PeakData(idx, cx, cy, li, ri, lb, rb, lbh, rbh)
                )

            self.q_app.set_peak_data_list(idx, peak_data_list, emit=emit)

    def on_btn_all(self):
        af = AutoFindPopUp(parent=self)
        af.exec()
