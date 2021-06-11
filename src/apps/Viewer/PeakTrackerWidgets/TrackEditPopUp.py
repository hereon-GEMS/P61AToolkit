from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QAbstractItemView, QCheckBox, QDialog, QGroupBox, QHBoxLayout
import numpy as np
from functools import reduce
import copy
import logging

from FitWidgets.FloatEdit import FloatEdit
from DatasetManager import DatasetSelector

from P61App import P61App


class TrackEditPopUp(QDialog):
    """"""

    def __init__(self, parent=None, track_ids=None):
        QDialog.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.setWindowTitle('Edit tracks')
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

        self.gb_amplitude = QGroupBox(parent=self)
        self.gb_amplitude.setCheckable(True)
        self.gb_amplitude.setChecked(False)
        self.gb_amplitude.setTitle('Amplitude')

        self.lb_amplitude_v = QLabel('Value', parent=self)
        self.lb_amplitude_mi = QLabel('Min', parent=self)
        self.lb_amplitude_ma = QLabel('Max', parent=self)

        # self.ed_amplitude_v = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.ed_amplitude_v = QLabel('None', parent=self)
        self.ed_amplitude_mi = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.ed_amplitude_ma = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)

        gb_amplitude_l = QHBoxLayout()
        self.gb_amplitude.setLayout(gb_amplitude_l)
        gb_amplitude_l.addWidget(self.lb_amplitude_v)
        gb_amplitude_l.addWidget(self.ed_amplitude_v)
        gb_amplitude_l.addWidget(self.lb_amplitude_mi)
        gb_amplitude_l.addWidget(self.ed_amplitude_mi)
        gb_amplitude_l.addWidget(self.lb_amplitude_ma)
        gb_amplitude_l.addWidget(self.ed_amplitude_ma)

        self.gb_sigma = QGroupBox(parent=self)
        self.gb_sigma.setCheckable(True)
        self.gb_sigma.setChecked(False)
        self.gb_sigma.setTitle('Sigma')

        self.lb_sigma_v = QLabel('Value', parent=self)
        self.lb_sigma_mi = QLabel('Min', parent=self)
        self.lb_sigma_ma = QLabel('Max', parent=self)

        # self.ed_sigma_v = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.ed_sigma_v = QLabel('None', parent=self)
        self.ed_sigma_mi = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.ed_sigma_ma = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)

        gb_sigma_l = QHBoxLayout()
        self.gb_sigma.setLayout(gb_sigma_l)
        gb_sigma_l.addWidget(self.lb_sigma_v)
        gb_sigma_l.addWidget(self.ed_sigma_v)
        gb_sigma_l.addWidget(self.lb_sigma_mi)
        gb_sigma_l.addWidget(self.ed_sigma_mi)
        gb_sigma_l.addWidget(self.lb_sigma_ma)
        gb_sigma_l.addWidget(self.ed_sigma_ma)

        self.gb_base = QGroupBox(parent=self)
        self.gb_base.setCheckable(True)
        self.gb_base.setChecked(False)
        self.gb_base.setTitle('Base')

        self.lb_base_v = QLabel('Value', parent=self)

        self.ed_base_v = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)

        gb_base_l = QHBoxLayout()
        self.gb_base.setLayout(gb_base_l)
        gb_base_l.addWidget(self.lb_base_v)
        gb_base_l.addWidget(self.ed_base_v)

        self.gb_o_base = QGroupBox(parent=self)
        self.gb_o_base.setCheckable(True)
        self.gb_o_base.setChecked(False)
        self.gb_o_base.setTitle('Overlap base')

        self.lb_o_base_v = QLabel('Value', parent=self)

        self.ed_o_base_v = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)

        gb_o_base_l = QHBoxLayout()
        self.gb_o_base.setLayout(gb_o_base_l)
        gb_o_base_l.addWidget(self.lb_o_base_v)
        gb_o_base_l.addWidget(self.ed_o_base_v)

        self.list_span = DatasetSelector(parent=self)

        self.init_edits()

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.gb_center, 1, 1, 1, 1)
        layout.addWidget(self.gb_sigma, 2, 1, 1, 1)
        layout.addWidget(self.gb_amplitude, 3, 1, 1, 1)
        layout.addWidget(self.gb_base, 4, 1, 1, 1)
        layout.addWidget(self.gb_o_base, 5, 1, 1, 1)
        layout.addWidget(self.list_span, 1, 2, 5, 2)
        layout.addWidget(self.button_ok, 6, 2, 1, 1)
        layout.addWidget(self.button_cancel, 6, 3, 1, 1)

        self.button_ok.clicked.connect(self.on_btn_ok)
        self.button_cancel.clicked.connect(self.on_btn_cancel)

        self.gb_center.clicked.connect(self.on_gb_clicked)
        self.gb_sigma.clicked.connect(self.on_gb_clicked)
        self.gb_amplitude.clicked.connect(self.on_gb_clicked)
        self.gb_base.clicked.connect(self.on_gb_clicked)
        self.gb_o_base.clicked.connect(self.on_gb_clicked)

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
                self.list_span.set_selected(sum((self._tracks[idx].ids for idx in self._track_ids), []))
            else:
                self.ed_center_v.set_value(ps['center'], emit=False)
                self.list_span.set_selected(self._tracks[self._track_ids[0]].ids)

            self.ed_center_mi.set_value(ps['center_min'] - ps['center'])
            self.ed_center_ma.set_value(ps['center_max'] - ps['center'])

        if not self.gb_sigma.isChecked():
            # self.ed_sigma_v.set_value(ps['sigma'])
            self.ed_sigma_v.setText('%.03f' % ps['sigma'])
            self.ed_sigma_mi.set_value(ps['sigma_min'])
            self.ed_sigma_ma.set_value(ps['sigma_max'])

        if not self.gb_amplitude.isChecked():
            # self.ed_amplitude_v.set_value(ps['amplitude'])
            self.ed_amplitude_v.setText('%.03f' % ps['amplitude'])
            self.ed_amplitude_mi.set_value(ps['amplitude_min'])
            self.ed_amplitude_ma.set_value(ps['amplitude_max'])

        if not self.gb_base.isChecked():
            self.ed_base_v.set_value(ps['base'])

        if not self.gb_o_base.isChecked():
            self.ed_o_base_v.set_value(ps['overlap_base'])

    def on_btn_ok(self):
        spectra_ids = self.list_span.get_selected()

        for spectra_idx in spectra_ids:
            peak_list = self.q_app.get_peak_data_list(spectra_idx)
            if peak_list is None:
                peak_list = []
            for track_idx in self._track_ids:
                if spectra_idx not in self._tracks[track_idx].ids:
                    new_peak = self._tracks[track_idx].predict_by_average(spectra_idx,
                                                                          self.q_app.data.loc[spectra_idx, 'DataX'],
                                                                          self.q_app.data.loc[spectra_idx, 'DataY'])
                    self._tracks[track_idx].append(new_peak)
                    peak_list.append(new_peak)
            self.q_app.set_peak_data_list(spectra_idx, peak_list, emit=False)

        if self.gb_center.isChecked():
            # if we're editing multiple tracks (hence c_val will be None), we don't touch track's mean value,
            # only adjust peaks that go outside [min, max] range.
            # if we're editing one track, we can both shift its mean and compress the variance
            c_min = min(self.ed_center_mi.get_value(), 0)
            c_max = max(self.ed_center_ma.get_value(), 0)

            for track_idx in self._track_ids:
                c_val = self.ed_center_v.get_value()

                if c_val is not None:
                    c_shift = c_val - np.mean(self._tracks[track_idx].cxs)
                    for spectra_idx in self._tracks[track_idx].ids:
                        self._tracks[track_idx][spectra_idx].cx += c_shift
                else:
                    c_val = np.mean(self._tracks[track_idx].cxs)

                c_min_, c_max_ = c_val + c_min, c_val + c_max
                for spectra_idx in self._tracks[track_idx].ids:
                    if self._tracks[track_idx][spectra_idx].cx > c_max_:
                        self._tracks[track_idx][spectra_idx].cx = c_max_
                    if self._tracks[track_idx][spectra_idx].cx < c_min_:
                        self._tracks[track_idx][spectra_idx].cx = c_min_

                    self._tracks[track_idx][spectra_idx].cx_bounds = (c_min_, c_max_)

        if self.gb_amplitude.isChecked():
            a_min = max(self.ed_amplitude_mi.get_value(), 0)
            a_max = max(self.ed_amplitude_ma.get_value(), 0)

            for track_idx in self._track_ids:
                for spectra_idx in self._tracks[track_idx].ids:
                    if self._tracks[track_idx][spectra_idx].amplitude > a_max:
                        self._tracks[track_idx][spectra_idx].amplitude = a_max
                    if self._tracks[track_idx][spectra_idx].amplitude < a_min:
                        self._tracks[track_idx][spectra_idx].amplitude = a_min

                    self._tracks[track_idx][spectra_idx].amplitude_bounds = (a_min, a_max)

        if self.gb_sigma.isChecked():
            s_min = max(self.ed_sigma_mi.get_value(), 0)
            s_max = max(self.ed_sigma_ma.get_value(), 0)

            for track_idx in self._track_ids:
                for spectra_idx in self._tracks[track_idx].ids:
                    if self._tracks[track_idx][spectra_idx].sigma > s_max:
                        self._tracks[track_idx][spectra_idx].sigma = s_max
                    if self._tracks[track_idx][spectra_idx].sigma < s_min:
                        self._tracks[track_idx][spectra_idx].sigma = s_min

                    self._tracks[track_idx][spectra_idx].sigma_bounds = (s_min, s_max)

        if self.gb_base.isChecked():
            b_val = self.ed_base_v.get_value()
            for track_idx in self._track_ids:
                self._tracks[track_idx].bases = b_val

        if self.gb_o_base.isChecked():
            o_b_val = self.ed_o_base_v.get_value()
            for track_idx in self._track_ids:
                self._tracks[track_idx].overlap_bases = o_b_val

        for spectra_idx in spectra_ids:
            peak_list = self.q_app.get_peak_data_list(spectra_idx)
            peak_list = list(sorted(peak_list, key=lambda item: item.md_params['center']))
            self.q_app.set_peak_data_list(spectra_idx, peak_list, emit=False)

        self.q_app.peakListChanged.emit(spectra_ids)

        self._tracks = list(sorted(self._tracks, key=lambda x: np.mean(x.cxs)))
        self.q_app.set_pd_tracks(self._tracks)
        self.close()

    def on_btn_cancel(self):
        self.close()
