from PyQt5.QtWidgets import QDialog, QGridLayout, QPushButton, QLabel, QComboBox, QProgressDialog, QCheckBox
from PyQt5.Qt import Qt
import copy
import logging

from P61App import P61App
from DatasetManager import DatasetSelector


class SeqFitPopUp(QDialog):
    """"""
    def __init__(self, parent=None):
        QDialog.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.progress = None
        self.sequence = None

        self.current_name = QLabel(parent=self)
        self.combo = QComboBox(parent=self)
        self.combo.addItems(['Do not init', 'Init all from current', 'Sequential from current'])
        self.cb_bckg = QCheckBox('Fit background')
        self.cb_bckg.setChecked(True)
        self.cb_peaks = QCheckBox('Fit peaks')
        self.cb_peaks.setChecked(True)
        self.cb_prec = QCheckBox('Quick fit (low quality)')
        self.cb_prec.setChecked(False)
        self.btn_ok = QPushButton('Fit', parent=self)
        self.selection_list = DatasetSelector(parent=self)

        self.setWindowTitle('Fit multiple spectra')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.combo, 1, 1, 1, 1)
        layout.addWidget(self.current_name, 2, 1, 1, 1)
        layout.addWidget(self.cb_peaks, 4, 1, 1, 1)
        layout.addWidget(self.cb_bckg, 5, 1, 1, 1)
        layout.addWidget(self.cb_prec, 6, 1, 1, 1)
        layout.addWidget(self.btn_ok, 7, 1, 1, 1)
        layout.addWidget(self.selection_list, 1, 2, 7, 1)

        self.btn_ok.clicked.connect(self.on_btn_ok)
        self.cb_peaks.clicked.connect(self.upd_cb_prec)
        self.cb_bckg.clicked.connect(self.upd_cb_prec)
        self.combo.currentIndexChanged.connect(self.on_combo_index_change)
        self.q_app.fitWorkerFinished.connect(self.on_tw_finished, Qt.QueuedConnection)

    def upd_cb_prec(self):
        if self.cb_bckg.isChecked() and self.cb_peaks.isChecked():
            self.cb_prec.setEnabled(True)
        else:
            self.cb_prec.setChecked(False)
            self.cb_prec.setEnabled(False)

    def on_combo_index_change(self):
        if self.q_app.get_selected_idx() == -1:
            return
        if self.combo.currentIndex() in (1, 2):
            self.current_name.setText(self.q_app.get_selected_screen_name())
        else:
            self.current_name.setText('')

    def on_btn_ok(self):
        if self.q_app.get_selected_idx() == -1:
            self.close()
            return

        fit_ids = self.selection_list.get_selected()
        start_idx = self.q_app.get_selected_idx()
        fit_type = self.combo.currentIndex()

        if fit_type == 1:
            # initiating all fit models from current
            # raise NotImplementedError('Init all from current is not supported')
            # copying background
            bckg_list = self.q_app.get_bckg_data_list(start_idx)
            for idx in fit_ids:
                self.q_app.set_bckg_data_list(idx, copy.deepcopy(bckg_list), emit=False)
            self.q_app.bckgListChanged.emit(fit_ids)

            # copying peaks
            tracks = self.q_app.get_pd_tracks()
            for fit_idx in fit_ids:
                peak_list = self.q_app.get_peak_data_list(fit_idx)
                for track in tracks:
                    if fit_idx in track.ids and start_idx in track.ids:
                        track[fit_idx].cx = track[start_idx].cx
                        track[fit_idx].cx_bounds = track[start_idx].cx_bounds
                        track[fit_idx].amplitude = track[start_idx].amplitude
                        track[fit_idx].amplitude_bounds = track[start_idx].amplitude_bounds
                        track[fit_idx].sigma = track[start_idx].sigma
                        track[fit_idx].sigma_bounds = track[start_idx].sigma_bounds
                        track[fit_idx].base = track[start_idx].base
                        track[fit_idx].overlap_base = track[start_idx].overlap_base
                    elif fit_idx in track.ids:
                        pass
                    elif start_idx in track.ids:
                        pass
                    else:
                        pass

            self.q_app.peakListChanged.emit(fit_ids)
            self.q_app.peakTracksChanged.emit()

        if self.q_app.get_selected_idx() in fit_ids:
            fit_ids.remove(self.q_app.get_selected_idx())
        fit_ids = [self.q_app.get_selected_idx(), self.q_app.get_selected_idx()] + fit_ids

        self.logger.debug('on_btn_ok: Launching sequential refinement type %d on ids %s' % (fit_type, str(fit_ids[1:])))

        self.progress = QProgressDialog("Sequential refinement", "Cancel", 0, len(fit_ids))
        self.progress.setWindowModality(Qt.ApplicationModal)
        cb = QPushButton('Cancel')
        cb.clicked.connect(self.on_cancel)
        self.progress.setCancelButton(cb)
        self.progress.show()

        self.sequence = enumerate(zip(fit_ids[:-1], fit_ids[1:]))
        self.on_tw_finished()

    def on_cancel(self):
        self.sequence = None

    def on_tw_finished(self):
        if self.parent().fit_idx is not None:
            self.parent().fit_idx = None

        try:
            ii, (prev_idx, idx) = next(self.sequence)
        except (StopIteration, TypeError):
            self.progress.close()
            self.close()
            return

        if self.combo.currentIndex() == 2:
            raise NotImplementedError('Sequential from current is not supported')
            # self.q_app.data.loc[idx, 'GeneralFitResult'] = \
            #     copy.deepcopy(self.q_app.data.loc[prev_idx, 'GeneralFitResult'])

        if self.cb_peaks.isChecked() and not self.cb_bckg.isChecked():
            self.parent().on_peak_fit_btn(idx=idx)
        elif self.cb_bckg.isChecked() and not self.cb_peaks.isChecked():
            self.parent().on_bckg_fit_btn(idx=idx)
        elif self.cb_peaks.isChecked() and self.cb_bckg.isChecked() and self.cb_prec.isChecked():
            self.parent().on_fit_to_prec_btn(idx=idx, max_cycles=1)
        elif self.cb_peaks.isChecked() and self.cb_bckg.isChecked() and not self.cb_prec.isChecked():
            self.parent().on_fit_to_prec_btn(idx=idx)

        self.progress.setValue(ii)
