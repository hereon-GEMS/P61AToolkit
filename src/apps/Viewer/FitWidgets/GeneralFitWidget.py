from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
import pandas as pd
import logging
import copy

from P61App import P61App
from DatasetManager import DatasetViewer
from FitWidgets.LmfitInspector import LmfitInspector

from FitWidgets.SeqFitPopUp import SeqFitPopUp
from FitWidgets.ConstrainPopUp import ConstrainPopUp
from PlotWidgets import FitPlot
from ThreadIO import Worker
from peak_fit_utils import fit_peaks as fit_peaks2, fit_bckg as fit_bckg2, fit_to_precision as fit_to_precision2


class FitWorker(Worker):
    def __init__(self, x, y, peak_list, bckg_list, fit_type):
        if fit_type == 'peaks':
            super(FitWorker, self).__init__(fit_peaks2, args=[], kwargs={'xx': x, 'yy': y, 'peak_list': peak_list, 'bckg_list': bckg_list})
        elif fit_type == 'bckg':
            super(FitWorker, self).__init__(fit_bckg2, args=[], kwargs={'xx': x, 'yy': y, 'peak_list': peak_list, 'bckg_list': bckg_list})
        elif fit_type == 'prec':
            super(FitWorker, self).__init__(fit_to_precision2, args=[],
                                            kwargs={'xx': x, 'yy': y, 'peak_list': peak_list, 'bckg_list': bckg_list})
        else:
            raise ValueError('fit_type argument should be \'peaks\' or \'bckg\'')

        self.threadWorkerException = self.q_app.fitWorkerException
        self.threadWorkerResult = self.q_app.fitWorkerResult
        self.threadWorkerFinished = self.q_app.fitWorkerFinished
        self.threadWorkerStatus = self.q_app.fitWorkerStatus


class GeneralFitWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.fit_idx = None

        self.active_list = DatasetViewer()

        self.fit_btn = QPushButton('Fit')
        self.constrain_btn = QPushButton('Constrain parameters')
        self.bckg_fit_btn = QPushButton('Fit Background')
        self.peaks_fit_btn = QPushButton('Fit peaks')
        self.full_fit_btn = QPushButton('Fit this')
        self.fit_mult_btn = QPushButton('Fit multiple')
        self.copy_btn = QPushButton('Copy params')
        self.export_btn = QPushButton('Export')
        self.plot_w = FitPlot(parent=self)

        self.lmfit_inspector = LmfitInspector(fitPlot=self.plot_w)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.lmfit_inspector, 1, 1, 3, 3)
        layout.addWidget(self.active_list, 4, 3, 6, 1)
        layout.addWidget(self.constrain_btn, 4, 1, 1, 2)
        layout.addWidget(self.bckg_fit_btn, 5, 1, 1, 1)
        layout.addWidget(self.peaks_fit_btn, 5, 2, 1, 1)
        layout.addWidget(self.full_fit_btn, 6, 1, 1, 2)
        layout.addWidget(self.copy_btn, 8, 1, 1, 2)
        layout.addWidget(self.fit_mult_btn, 7, 1, 1, 2)
        layout.addWidget(self.export_btn, 9, 1, 1, 2)
        layout.addWidget(self.plot_w, 1, 4, 8, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 4)
        layout.setColumnStretch(4, 16)

        self.constrain_btn.clicked.connect(self.on_constrain_btn)
        self.fit_mult_btn.clicked.connect(self.on_fit_mult_btn)
        self.bckg_fit_btn.clicked.connect(self.on_bckg_fit_btn)
        self.peaks_fit_btn.clicked.connect(self.on_peak_fit_btn)
        self.full_fit_btn.clicked.connect(self.on_fit_to_prec_btn)
        self.copy_btn.clicked.connect(self.on_copy_btn)
        self.export_btn.clicked.connect(self.on_export_button)

        self.q_app.fitWorkerResult.connect(self.on_tw_result, Qt.QueuedConnection)
        self.q_app.fitWorkerException.connect(self.on_tw_exception, Qt.QueuedConnection)
        self.q_app.fitWorkerFinished.connect(self.on_tw_finished, Qt.QueuedConnection)

    def on_tw_finished(self):
        self.logger.debug('on_tw_finished: Handling FitWorker.threadWorkerFinished')
        self.fit_idx = None

    def on_tw_result(self, result):
        self.logger.debug('on_tw_result: Handling FitWorker.threadWorkerResult')
        chi2, bckg_list, peak_list = result

        self.q_app.data.loc[self.fit_idx, 'Chi2'] = chi2
        self.q_app.set_bckg_data_list(self.fit_idx, bckg_list)
        self.q_app.set_peak_data_list(self.fit_idx, peak_list)

    def on_tw_exception(self):
        self.logger.debug('on_tw_exception: Handling FitWorker.threadWorkerException')

    def on_constrain_btn(self, *args, idx=None):
        w = ConstrainPopUp(parent=self)
        w.exec_()

    def on_peak_fit_btn(self, *args, idx=None):
        if self.fit_idx is not None:
            return

        if self.q_app.get_selected_idx() == -1:
            return
        elif idx is None:
            idx = self.q_app.get_selected_idx()

        peak_list = self.q_app.get_peak_data_list(idx)
        if peak_list is None:
            return

        bckg_list = self.q_app.get_bckg_data_list(idx)
        if bckg_list is None:
            bckg_list = []

        xx, yy = self.q_app.data.loc[idx, 'DataX'], self.q_app.data.loc[idx, 'DataY']

        fw = FitWorker(xx, yy, peak_list, bckg_list, fit_type='peaks')
        self.fit_idx = idx
        if self.q_app.config['use_threads']:
            self.q_app.thread_pool.start(fw)
        else:
            fw.run()

    def on_bckg_fit_btn(self, *args, idx=None):
        if self.fit_idx is not None:
            return

        if self.q_app.get_selected_idx() == -1:
            return
        elif idx is None:
            idx = self.q_app.get_selected_idx()

        peak_list = self.q_app.get_peak_data_list(idx)
        if peak_list is None:
            peak_list = []

        bckg_list = self.q_app.get_bckg_data_list(idx)
        if bckg_list is None:
            return

        xx, yy = self.q_app.data.loc[idx, 'DataX'], self.q_app.data.loc[idx, 'DataY']

        fw = FitWorker(xx, yy, peak_list, bckg_list, fit_type='bckg')
        self.fit_idx = idx
        if self.q_app.config['use_threads']:
            self.q_app.thread_pool.start(fw)
        else:
            fw.run()

    def on_fit_to_prec_btn(self, *args, idx=None, max_cycles=None, min_chi_change=None):
        if self.fit_idx is not None:
            return

        if self.q_app.get_selected_idx() == -1:
            return
        elif idx is None:
            idx = self.q_app.get_selected_idx()

        peak_list = self.q_app.get_peak_data_list(idx)
        if peak_list is None:
            peak_list = []

        bckg_list = self.q_app.get_bckg_data_list(idx)
        if bckg_list is None:
            bckg_list = []

        xx, yy = self.q_app.data.loc[idx, 'DataX'], self.q_app.data.loc[idx, 'DataY']

        fw = FitWorker(xx, yy, peak_list, bckg_list, fit_type='prec')
        self.fit_idx = idx
        if self.q_app.config['use_threads']:
            self.q_app.thread_pool.start(fw)
        else:
            fw.run()

    def on_copy_btn(self, *args):
        pass

    def on_fit_mult_btn(self):
        w = SeqFitPopUp(parent=self)
        w.exec_()

    def on_export_button(self):
        f_name, _ = QFileDialog.getSaveFileName(self, "Save fit data as csv", "", "All Files (*);;CSV (*.csv)")
        if not f_name:
            return

        def expand_result(row):
            return row
            # if row['GeneralFitResult'] is None:
            #     return row.drop(labels=['GeneralFitResult'])
            # else:
            #     row['chi2'] = row['GeneralFitResult'].chisqr
            #     for p in row['GeneralFitResult'].params:
            #         if any(map(lambda x: x in p, ('center', 'height', 'amplitude', 'sigma', 'fwhm', 'fraction',
            #                                       'rwp2', 'chi2'))):
            #             row[p] = row['GeneralFitResult'].params[p].value
            #         if any(map(lambda x: x in p, ('center', 'height', 'amplitude', 'sigma', 'fwhm', 'fraction'))):
            #             row[p + '_std'] = row['GeneralFitResult'].params[p].stderr
            #     return row.drop(labels=['GeneralFitResult'])

        def expand_motors(row):
            if row['Motors'] is None:
                for motor in self.q_app.motors_all:
                    row[motor] = None
            else:
                for motor in self.q_app.motors_all:
                    row[motor] = row['Motors'][motor]
            return row.drop(labels=['Motors'])

        def add_phase_data(df):
            peak_centers = df.filter(regex='center$', axis=1)
            peak_centers = peak_centers.mean()
            for phase in self.q_app.get_hkl_peaks():
                peaks = self.q_app.hkl_peaks[phase]
                for peak in peaks:
                    _pc = peak_centers[(peak_centers < peak['e'] + peak['de']) &
                                       (peak_centers > peak['e'] - peak['de'])]
                    if _pc.shape[0] > 0:
                        label = (_pc - peak['e']).abs().idxmin()
                        df[label.replace('center', 'h')] = [peak['h']] * df.shape[0]
                        df[label.replace('center', 'k')] = [peak['k']] * df.shape[0]
                        df[label.replace('center', 'l')] = [peak['l']] * df.shape[0]
                        df[label.replace('center', '3gamma')] = [peak['3g']] * df.shape[0]
                        df[label.replace('center', 'phase')] = [phase] * df.shape[0]
            return df

        result = pd.DataFrame()
        result = result.append(self.q_app.data.loc[self.q_app.data['Active'], ['ScreenName', 'DeadTime',
                                                                               'Motors']])
        result = result.apply(expand_result, axis=1)
        result = result.apply(expand_motors, axis=1)
        result = add_phase_data(result)

        columns = list(sorted(result.columns))
        columns.remove('ScreenName')
        result = result[['ScreenName'] + columns]

        result.to_csv(f_name)


if __name__ == '__main__':
    import sys
    q_app = P61App(sys.argv)
    app = GeneralFitWidget()
    app.show()
    sys.exit(q_app.exec())
