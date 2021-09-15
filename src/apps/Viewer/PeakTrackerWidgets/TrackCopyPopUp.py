from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QAbstractItemView, QCheckBox, QDialog, QGroupBox, QHBoxLayout
import numpy as np
from functools import reduce
import copy
import logging

from FitWidgets.FloatEdit import FloatEdit
from DatasetManager import DatasetSelector

from P61App import P61App


class TrackCopyPopUp(QDialog):
    """"""

    def __init__(self, parent=None, track_ids=None):
        QDialog.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.setWindowTitle('New track')
        self.button_ok = QPushButton('Ok', parent=self)
        self.button_cancel = QPushButton('Cancel', parent=self)

        self._tracks = self.q_app.get_pd_tracks()
        if track_ids is None:
            self._track_ids = []
        else:
            self._track_ids = track_ids

        self.gb_center = QGroupBox(parent=self)
        self.gb_center.setCheckable(True)
        self.gb_center.setChecked(False)
        self.gb_center.setTitle('Center')

        self.lb_center_v = QLabel('Value', parent=self)
        self.lb_center_mi = QLabel('rel. Min', parent=self)
        self.lb_center_ma = QLabel('rel. Max', parent=self)

        self.ed_center_v = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.ed_center_mi = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.ed_center_ma = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)

        gb_center_l = QHBoxLayout()
        self.gb_center.setLayout(gb_center_l)
        gb_center_l.addWidget(self.lb_center_v)
        gb_center_l.addWidget(self.ed_center_v)
        gb_center_l.addWidget(self.lb_center_mi)
        gb_center_l.addWidget(self.ed_center_mi)
        gb_center_l.addWidget(self.lb_center_ma)
        gb_center_l.addWidget(self.ed_center_ma)

        self.init_edits()

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.gb_center, 1, 1, 1, 1)
        layout.addWidget(self.button_ok, 6, 2, 1, 1)
        layout.addWidget(self.button_cancel, 6, 3, 1, 1)

        self.button_ok.clicked.connect(self.on_btn_ok)
        self.button_cancel.clicked.connect(self.on_btn_cancel)

        self.gb_center.clicked.connect(self.on_gb_clicked)

    def on_gb_clicked(self,*args, **kwargs):
        self.init_edits()

    def init_edits(self):
        if len(self._track_ids) == 0:
            return

        ps = reduce(lambda a, b: a + b, [self._tracks[idx].export_ref_params.mean()
                                         for idx in self._track_ids]) / len(self._track_ids)

        if not self.gb_center.isChecked():
            if len(self._track_ids) != 1:
                self.ed_center_v.setReadOnly(True)
            else:
                self.ed_center_v.set_value(ps['center'], emit=False)

            self.ed_center_mi.set_value(ps['center_min'] - ps['center'])
            self.ed_center_ma.set_value(ps['center_max'] - ps['center'])

    def on_btn_ok(self):
        all_spectra_ids = []
        for track_idx in sorted(self._track_ids, reverse=True):
            new_track = copy.copy(self._tracks[track_idx])

            if self.gb_center.isChecked():
                # if we're editing multiple tracks (hence c_val will be None), we don't touch track's mean value,
                # only adjust peaks that go outside [min, max] range.
                # if we're editing one track, we can both shift its mean and compress the variance
                c_min = min(self.ed_center_mi.get_value(), 0)
                c_max = max(self.ed_center_ma.get_value(), 0)
                c_val = self.ed_center_v.get_value()

                if c_val is not None:
                    c_shift = c_val - np.mean(new_track.cxs)
                    for spectra_idx in new_track.ids:
                        new_track[spectra_idx].cx += c_shift
                else:
                    c_val = np.mean(new_track.cxs)

                c_min_, c_max_ = c_val + c_min, c_val + c_max
                for spectra_idx in new_track.ids:
                    if new_track[spectra_idx].cx > c_max_:
                        new_track[spectra_idx].cx = c_max_
                    if new_track[spectra_idx].cx < c_min_:
                        new_track[spectra_idx].cx = c_min_

                    new_track[spectra_idx].cx_bounds = (c_min_, c_max_)

            self._tracks = self._tracks[:track_idx] + [new_track] + self._tracks[track_idx:]

            for spectra_idx in new_track.ids:
                peak_list = self.q_app.get_peak_data_list(spectra_idx)
                peak_list.append(new_track[spectra_idx])
                peak_list = list(sorted(peak_list, key=lambda item: item.md_params['center']))
                self.q_app.set_peak_data_list(spectra_idx, peak_list, emit=False)

            all_spectra_ids.extend(new_track.ids)

        self._tracks = list(sorted(self._tracks, key=lambda x: np.mean(x.cxs)))
        self.q_app.peakListChanged.emit(list(set(all_spectra_ids)))
        self.q_app.set_pd_tracks(self._tracks)
        self.close()

    def on_btn_cancel(self):
        self.close()
