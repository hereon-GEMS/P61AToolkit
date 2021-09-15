from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QAbstractItemView, QListWidget
import numpy as np
import copy
import logging

from PeakTrackerWidgets.TrackEditPopUp import TrackEditPopUp
from PeakTrackerWidgets.TrackCopyPopUp import TrackCopyPopUp

from P61App import P61App


class PeakTrackList(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.lbl = QLabel('Peak tracks', parent=self)
        self.btn_del = QPushButton('Delete', parent=self)
        # self.btn_hkl = QPushButton('!hkl', parent=self)
        self.btn_edt = QPushButton('Edit', parent=self)
        self.btn_cp = QPushButton('Duplicate', parent=self)
        self.lst = QListWidget(parent=self)

        self.lst.setSelectionMode(QAbstractItemView.ExtendedSelection)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.lbl, 1, 1, 1, 1)
        layout.addWidget(self.btn_edt, 1, 3, 1, 1)
        layout.addWidget(self.btn_cp, 1, 4, 1, 1)
        layout.addWidget(self.btn_del, 1, 5, 1, 1)
        # layout.addWidget(self.btn_hkl, 1, 6, 1, 1)
        layout.addWidget(self.lst, 2, 1, 1, 5)

        self.btn_del.clicked.connect(self.on_btn_del)
        # self.btn_hkl.clicked.connect(self.on_btn_hkl)
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

        if len(rows) > 1:
            return

        popup = TrackCopyPopUp(parent=self, track_ids=rows)
        popup.exec_()
        # ids = self.lst.selectedIndexes()
        # rows = sorted(map(lambda x: x.row(), ids), reverse=True)
        # tracks = self.q_app.get_pd_tracks()
        #
        # all_spectra_ids = []
        # for row in sorted(rows, reverse=True):
        #     new_track = copy.copy(tracks[row])
        #     tracks = tracks[:row] + [new_track] + tracks[row:]
        #
        #     for spectra_idx in new_track.ids:
        #         peak_list = self.q_app.get_peak_data_list(spectra_idx)
        #         peak_list.append(new_track[spectra_idx])
        #         peak_list = list(sorted(peak_list, key=lambda item: item.md_params['center']))
        #         self.q_app.set_peak_data_list(spectra_idx, peak_list, emit=False)
        #
        #     all_spectra_ids.extend(new_track.ids)
        #
        # self.q_app.peakListChanged.emit(list(set(all_spectra_ids)))
        # self.q_app.set_pd_tracks(tracks)

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
