from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, \
    QProgressDialog, QDoubleSpinBox
from PyQt5.Qt import Qt
from scipy.signal import find_peaks
import numpy as np

from P61App import P61App
from DatasetManager import DatasetSelector
from peak_fit_utils import PeakData, PeakDataTrack


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
        self.height_label.setToolTip('Minimal absolute height (see also: prominence).')
        self.height_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # self.height_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=20.)
        self.height_edit = QDoubleSpinBox(parent=self, minimum=1., maximum=1e8, singleStep=1, decimals=0,
                                          suffix=' cts')
        self.height_edit.setValue(1e3)

        self.dist_label = QLabel('Distance')
        self.dist_label.setToolTip('Minimal horizontal distance between neighbouring peaks.\n'
                                   'Smaller peaks are removed first until the condition is fulfilled '
                                   'for all remaining peaks.')
        self.dist_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # self.dist_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=5E-1)
        self.dist_edit = QDoubleSpinBox(parent=self, minimum=0., maximum=200, singleStep=1, decimals=1,
                                          suffix=' keV')
        self.dist_edit.setValue(0.5)

        self.width_label = QLabel('Width')
        self.width_label.setToolTip('Minimal width of peaks.')
        self.width_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # self.width_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=5E-2)
        self.width_edit = QDoubleSpinBox(parent=self, minimum=0., maximum=10, singleStep=0.1, decimals=2,
                                          suffix=' keV')
        self.width_edit.setValue(0.05)

        self.prom_label = QLabel('Prominence')
        self.prom_label.setToolTip('Minimal height relative to surrounding background.')
        self.prom_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # self.prom_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=1e3)
        self.prom_edit = QDoubleSpinBox(parent=self, minimum=1., maximum=1e8, singleStep=1., decimals=0,
                                          suffix=' cts')
        self.prom_edit.setValue(1e3)

        self.tw_label = QLabel('Track window')
        # self.tw_edit = FloatEdit(inf_allowed=False, none_allowed=True, init_val=3E-1)
        self.tw_edit = QDoubleSpinBox(parent=self, minimum=0., maximum=2., singleStep=.1, decimals=2,
                                          suffix=' keV')
        self.tw_edit.setValue(0.3)
        self.tw_label.setToolTip('Max shift in peak position between neighbouring spectra '
                                 'for the two peaks to be on the same track.')
        self.tw_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.btn_all = QPushButton('Find')
        self.btn_stack = QPushButton('Make tracks')

        self.btn_all.clicked.connect(self.on_btn_all)
        self.btn_stack.clicked.connect(self.on_btn_stack)

        layout = QVBoxLayout()
        self.setLayout(layout)

        l1 = QGridLayout()

        l1.addWidget(self.height_label, 1, 1, 1, 1)
        l1.addWidget(self.height_edit, 1, 2, 1, 1)
        l1.addWidget(self.dist_label, 1, 3, 1, 1)
        l1.addWidget(self.dist_edit, 1, 4, 1, 1)

        l1.addWidget(self.width_label, 2, 1, 1, 1)
        l1.addWidget(self.width_edit, 2, 2, 1, 1)
        l1.addWidget(self.prom_label, 2, 3, 1, 1)
        l1.addWidget(self.prom_edit, 2, 4, 1, 1)
        l1.addWidget(self.btn_all, 3, 1, 1, 4, alignment=Qt.AlignRight)

        l2 = QHBoxLayout()
        l2.addWidget(self.tw_label, alignment=Qt.AlignLeft)
        l2.addWidget(self.tw_edit, alignment=Qt.AlignLeft)
        l1.addLayout(l2, 4, 1, 1, 3, alignment=Qt.AlignLeft)
        l1.addWidget(self.btn_stack, 4, 4, 1, 1)
        layout.addLayout(l1)

    def on_btn_stack(self):
        tw = self.tw_edit.value()
        ids = self.q_app.get_active_ids()
        tracks = []

        for idx in ids:
            peak_list = self.q_app.get_peak_data_list(idx)
            if peak_list is None:
                continue
            for pdt in peak_list:
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
            'height': self.height_edit.value(),
            'distance': self.dist_edit.value(),
            'prominence': self.prom_edit.value(),
            'width': self.width_edit.value()
        }

        if idx == -1:
            idx = self.q_app.get_selected_idx()

        if idx != -1:
            yy = self.q_app.data.loc[idx, 'DataY']
            xx = self.q_app.data.loc[idx, 'DataX']

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
