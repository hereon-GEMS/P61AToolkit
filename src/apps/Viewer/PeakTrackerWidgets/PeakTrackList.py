from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QAbstractItemView, QListWidget, QDialog
import numpy as np
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

        self.compress_lbl1 = QLabel('Mean Energy', parent=self)
        self.compress_lbl2 = QLabel('Energy range', parent=self)
        self.cmp_center_edt = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.cmp_range_edt = FloatEdit(inf_allowed=False, parent=self, none_allowed=True, init_val=None)
        self.range_lbl = QLabel('Span', parent=self)
        self.list_span = DatasetSelector(parent=self)

        if len(self._track_ids) != 1:
            self.cmp_center_edt.setReadOnly(True)
            self.cmp_range_edt.setReadOnly(True)
            self.list_span.set_selected(sum((self._tracks[idx].ids for idx in self._track_ids), []))
        else:
            self.cmp_center_edt.set_value(np.mean(self._tracks[self._track_ids[0]].cxs), emit=False)
            self.cmp_range_edt.set_value(np.max(self._tracks[self._track_ids[0]].cxs) -
                                         np.min(self._tracks[self._track_ids[0]].cxs), emit=False)

            self.list_span.set_selected(self._tracks[self._track_ids[0]].ids)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.compress_lbl1, 1, 1, 1, 1)
        layout.addWidget(self.compress_lbl2, 1, 2, 1, 1)
        layout.addWidget(self.cmp_center_edt, 2, 1, 1, 1)
        layout.addWidget(self.cmp_range_edt, 2, 2, 1, 1)
        layout.addWidget(self.range_lbl, 3, 1, 1, 2)
        layout.addWidget(self.list_span, 4, 1, 1, 2)
        layout.addWidget(self.button_ok, 5, 1, 1, 1)
        layout.addWidget(self.button_cancel, 5, 2, 1, 1)

        self.button_ok.clicked.connect(self.on_btn_ok)
        self.button_cancel.clicked.connect(self.on_btn_cancel)

    def on_btn_ok(self):
        spectra_ids = self.list_span.get_selected()

        for spectra_idx in spectra_ids:
            peak_list = self.q_app.get_peak_data_list(spectra_idx)
            for track_idx in self._track_ids:
                if spectra_idx not in self._tracks[track_idx].ids:
                    new_peak = self._tracks[track_idx].predict_by_average(spectra_idx,
                                                                          self.q_app.data.loc[spectra_idx, 'DataX'],
                                                                          self.q_app.data.loc[spectra_idx, 'DataY'])
                    self._tracks[track_idx].append(new_peak)
                    peak_list.append(new_peak)
            self.q_app.set_peak_data_list(spectra_idx, peak_list, emit=False)

        if len(self._track_ids) == 1:
            mean_shift = self.cmp_center_edt.get_value() - np.mean(self._tracks[self._track_ids[0]].cxs)
            new_range = self.cmp_range_edt.get_value()

            self._tracks[self._track_ids[0]].shift_xs(mean_shift)
            self._tracks[self._track_ids[0]].compress_energies(new_range)

            self._tracks = list(sorted(self._tracks, key=lambda x: np.mean(x.cxs)))

        self.q_app.peakListChanged.emit(spectra_ids)
        self.q_app.set_pd_tracks(self._tracks)
        self.close()

    def on_btn_cancel(self):
        self.close()


class PeakTrackList(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.lbl = QLabel('Peak tracks', parent=self)
        self.btn_del = QPushButton('-', parent=self)
        self.btn_hkl = QPushButton('!hkl', parent=self)
        self.btn_edt = QPushButton('Edit', parent=self)
        self.btn_cp = QPushButton('Copy', parent=self)
        self.lst = QListWidget(parent=self)

        self.lst.setSelectionMode(QAbstractItemView.ExtendedSelection)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.lbl, 1, 1, 1, 1)
        layout.addWidget(self.btn_edt, 1, 3, 1, 1)
        layout.addWidget(self.btn_cp, 1, 4, 1, 1)
        layout.addWidget(self.btn_del, 1, 5, 1, 1)
        layout.addWidget(self.btn_hkl, 1, 6, 1, 1)
        layout.addWidget(self.lst, 2, 1, 1, 6)

        self.btn_del.clicked.connect(self.on_btn_del)
        self.btn_hkl.clicked.connect(self.on_btn_hkl)
        self.btn_cp.clicked.connect(self.on_btn_cp)
        self.btn_edt.clicked.connect(self.on_btn_edt)
        self.lst.itemDoubleClicked.connect(self.on_btn_edt)
        self.q_app.peakTracksChanged.connect(self.upd_list)

    def on_btn_hkl(self):
        peaks_hkl = self.q_app.get_hkl_peaks()
        tracks = self.q_app.get_pd_tracks()

        ii = 0
        peaks_hkl = sum((peaks_hkl[phase] for phase in peaks_hkl), [])
        while ii < len(tracks):
            for peak in peaks_hkl:
                if peak['e'] - peak['de'] <= np.mean(tracks[ii].cxs) <= peak['e'] + peak['de']:
                    ii += 1
                    break
            else:
                tracks[ii].cleanup()
                del tracks[ii]

        self.clean_peaks()
        self.q_app.set_pd_tracks(tracks)

    def on_btn_del(self):
        ids = self.lst.selectedIndexes()
        rows = sorted(map(lambda x: x.row(), ids), reverse=True)
        tracks = self.q_app.get_pd_tracks()

        for row in sorted(rows, reverse=True):
            tracks[row].cleanup()
            del tracks[row]

        self.clean_peaks()
        self.q_app.set_pd_tracks(tracks)

    def on_btn_cp(self):
        ids = self.lst.selectedIndexes()
        rows = sorted(map(lambda x: x.row(), ids), reverse=True)
        tracks = self.q_app.get_pd_tracks()

        all_spectra_ids = []
        for row in sorted(rows, reverse=True):
            new_track = copy.copy(tracks[row])
            tracks = tracks[:row] + [new_track] + tracks[row:]

            for spectra_idx in new_track.ids:
                peak_list = self.q_app.get_peak_data_list(spectra_idx)
                peak_list.append(new_track[spectra_idx])
                self.q_app.set_peak_data_list(spectra_idx, peak_list, emit=False)

            all_spectra_ids.extend(new_track.ids)

        self.q_app.peakListChanged.emit(list(set(all_spectra_ids)))
        self.q_app.set_pd_tracks(tracks)

    def on_btn_edt(self):
        ids = self.lst.selectedIndexes()
        rows = sorted(map(lambda x: x.row(), ids), reverse=True)

        popup = TrackEditPopUp(parent=self,track_ids=rows)
        popup.exec_()

    def clean_peaks(self):
        ids = list(self.q_app.get_active_ids())
        for idx in ids:
            peaks = self.q_app.get_peak_data_list(idx)
            ii = 0
            while ii < len(peaks):
                if peaks[ii].track is None:
                    del peaks[ii]
                else:
                    ii += 1
            self.q_app.set_peak_data_list(idx, peaks, emit=False)
        self.q_app.peakListChanged.emit(ids)

    def upd_list(self):
        self.lst.clear()
        tracks = self.q_app.get_pd_tracks()
        tracks_items = ['%d: <E> = %.01f' % (ii, np.mean(track.cxs)) for ii, track in enumerate(tracks)]
        self.lst.addItems(tracks_items)
