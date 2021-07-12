"""
src/P61App.py
====================

"""
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QThreadPool
import pandas as pd
import numpy as np
import os
import logging

import pickle
from collections import defaultdict
from utils import log_ex_time
from DataSetStorageModel import DataSetStorageModel
from cryst_utils import PhaseData
from peak_fit_utils import PeakData, PeakDataTrack, BckgData


class P61App(QApplication):
    """
    .. _QApplication: https://doc.qt.io/qtforpython/PySide2/QtWidgets/QApplication.html
    .. _generator: https://wiki.python.org/moin/Generators

    **General:**

    QApplication_ child class that is used for managing the application data.

    This class is a singleton accessible to all application widgets. By convention all widgets store a reference to the
    :code:`P61App` instance as

    .. code-block:: python3

        self.q_app = P61App.instance()


    The widgets use the instance to store and sync data, such as nexus file variables, fit results, etc. Synchronization
    between widgets is done by pyqtSignals. *Important:* it is the widget's responsibility to emit the appropriate
    signal after changing anything in the :code:`P61App.instance()`.

    :code:`P61App.instance().data` **columns and their meaning:**

    :code:`P61App.instance().data` is a :code:`pandas.DataFrame`
    (https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html). Each row of the dataframe
    represents a dataset read from a .nxs file. At the moment .nxs files hold two datasets at
    :code:`'entry/instrument/xspress3/channel00/histogram'` and :code:`'entry/instrument/xspress3/channel01/histogram'`.

    - :code:`'DataX'`: numpy array representing x values on the spectra;
    - :code:`'DataY'`: numpy array representing y values on the spectra;
    - :code:`'DataID'`: unique ID of the dataset built from .nxs file name and field (channel00 / channel01);
    - :code:`'ScreenName'`: name of the dataset shown by the list widgets
    - :code:`'Active'`: boolean status. False means the dataset is not shown on the plot and in the list for fitting.
    - :code:`'Color'`: color of the plot line and screen name on the list
    - :code:`'FitResult'`: :code:`lmfit.ModelResult` object (https://lmfit.github.io/lmfit-py/model.html#lmfit.model.ModelResult)

    :code:`P61App.instance().params` **and their meaning:**

    - :code:`'LmFitModel'`: :code:`lmfit.Model` (https://lmfit.github.io/lmfit-py/model.html#lmfit.model.Model) to fit
      the data in FitWidget;
    - :code:`'SelectedActiveIdx'`: currently selected item's index in ActiveWidget;
    - :code:`'ColorWheel'`: a python generator_ holding the list of colors for plotting;
    - :code:`'ColorWheel2'`: same thing, we just need two of them;

    **Signals and their meaning:**

    - :code:`dataRowsInserted`: when new histograms (rows) are added to the :code:`P61App.instance().data` Dataframe;
    - :code:`dataRowsRemoved`: when histograms (rows) are deleted from the :code:`P61App.instance().data` Dataframe;
    - :code:`dataActiveChanged`: when the :code:`'Active'` status of the rows is changed;

    Three signals above do not just notify the receivers, but also hold the lists of indices of the rows that were
    changed, added or deleted.

    - :code:`selectedIndexChanged`: when the :code:`ActiveListWidget` selection changes (also sends the new
      selected index);
    - :code:`lmFitModelUpdated`: when the :code:`self.params['LmFitModel']` is updated;

    """
    name = 'P61A::Viewer'
    version = '1.0.0' + ' build 2021-07-12'

    dataRowsInserted = pyqtSignal(int, int)
    dataRowsRemoved = pyqtSignal(list)
    dataActiveChanged = pyqtSignal(list)
    selectedIndexChanged = pyqtSignal(int)
    dataSorted = pyqtSignal()

    peakListChanged = pyqtSignal(list)
    bckgListChanged = pyqtSignal(list)
    genFitResChanged = pyqtSignal(list)
    peakTracksChanged = pyqtSignal()
    hklPhasesChanged = pyqtSignal()
    hklPeaksChanged = pyqtSignal()

    foWorkerException = pyqtSignal(object)
    foWorkerResult = pyqtSignal(object)
    foWorkerFinished = pyqtSignal()
    foWorkerStatus = pyqtSignal(int)

    fitWorkerException = pyqtSignal(object)
    fitWorkerResult = pyqtSignal(object)
    fitWorkerFinished = pyqtSignal()
    fitWorkerStatus = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        QApplication.__init__(self, *args, **kwargs)

        # data storage for one-per-dataset items
        self.data = pd.DataFrame(columns=('DataX', 'DataY', 'DeadTime', 'Channel', 'DataID', 'ScreenName', 'Active',
                                          'Color', 'PeakDataList', 'BckgDataList', 'Chi2', 'Motors'))
        self.data_model = DataSetStorageModel(instance=self)
        self.motors_cols = ('eu.chi', 'eu.phi', 'eu.bet', 'eu.alp', 'eu.x', 'eu.y', 'eu.z')
        self.motors_all = set(self.motors_cols)

        self.peak_tracks = None
        self.hkl_phases = None
        self.hkl_peaks = None

        self.proj_f_name = None
        self.proj_f_name_hint = None
        self.data_dir = None

        self.logger = logging.getLogger(str(self.__class__))
        self.thread_pool = QThreadPool(parent=self)

        self.config = {
            'use_threads': True,
            'downsample_3d': True
        }

        # data storage for one-per application items
        self.params = {
            'LmFitModelColors': dict(),
            'SelectedActiveIdx': -1,
            'ColorWheel': self._color_wheel('def'),
            'ColorWheel2': self._color_wheel('def_no_red'),
        }

        self.wheels = {
            'def': (0x1f77b4, 0xff7f0e, 0x2ca02c, 0xd62728, 0x9467bd, 0x8c564b, 0xe377c2, 0x7f7f7f, 0xbcbd22, 0x17becf),
            'def_no_red': (0x1f77b4, 0xff7f0e, 0x2ca02c, 0x9467bd, 0x8c564b, 0xe377c2, 0x7f7f7f, 0xbcbd22, 0x17becf),
        }

        self.cmaps = dict((name.replace('.csv', ''), np.loadtxt(os.path.join('utils', 'cmaps', name)))
                          for name in filter(lambda arg: '.csv' in arg, os.listdir(os.path.join('utils', 'cmaps'))))

        self.genFitResChanged.connect(self.on_fit_res_changed)
        self.dataRowsInserted.connect(self.on_data_rows_inserted)
        self.dataRowsRemoved.connect(self.on_data_rows_removed)
        self.dataActiveChanged.connect(self.on_data_ac)
        # self.dataSorted.connect(self.on_data_sorted)

    def apply_cmap(self, vals, cmap :str, log_scale=False):
        if cmap not in self.cmaps:
            raise ValueError('Colormap %s not found' % cmap)
        cmap = self.cmaps[cmap]
        colors = (vals - np.min(vals)) / (np.max(vals) - np.min(vals))
        if log_scale:
            colors = np.log(1. + colors)
            colors = (colors - np.min(colors)) / (np.max(colors) - np.min(colors))
        return np.apply_along_axis(lambda a: np.interp(colors, np.linspace(0., 1., cmap.shape[0]), a), 0, cmap)

    def on_fit_res_changed(self, ids):
        self.logger.debug('on_fit_res_changed: handling genFitResChanged')

    def on_data_rows_inserted(self):
        self.logger.debug('on_data_rows_inserted: handling dataRowsInserted')

    def on_data_rows_removed(self):
        self.logger.debug('on_data_rows_removed: handling dataRowsRemoved')

    def on_data_ac(self):
        self.logger.debug('on_data_ac: handling dataActiveChanged')

    def insert_rows(self, position, rows):
        d1, d2 = self.data[:position], self.data[position:]
        insert = pd.DataFrame({col: [None] * rows for col in self.data.columns},
                              index=np.arange(position, position + rows).astype(np.int))
        self.data = pd.concat((d1, insert, d2.set_index(d2.index + rows)))

        self.logger.debug('insert_rows: Inserted %d rows to position %d' % (rows, position))

    def remove_rows(self, position, rows):
        self.data.drop(index=np.arange(position, position + rows).astype(np.int), inplace=True)
        self.data.set_index(np.arange(self.data.shape[0]), inplace=True)

        self.logger.debug('remove_rows: Removed %d rows from position %d' % (rows, position))

    def _color_wheel(self, key):
        ii = 0
        wheel = self.wheels[key]

        while True:
            yield wheel[ii % len(wheel)]
            ii += 1

    def get_active_ids(self):
        return self.data[self.data['Active']].index

    def get_all_ids(self):
        return self.data.index

    def get_selected_idx(self):
        if self.params['SelectedActiveIdx'] == -1:
            return -1
        return self.data.index[self.params['SelectedActiveIdx']]

    def get_selected_active_idx(self):
        return self.params['SelectedActiveIdx']

    def set_selected_active_idx(self, val, emit=True):
        self.params['SelectedActiveIdx'] = val
        if emit:
            self.logger.debug('set_selected_active_idx: Emitting selectedIndexChanged(%d)' % (val, ))
            self.selectedIndexChanged.emit(val)

    def get_screen_names(self, only_active=False):
        if only_active:
            return self.data.loc[self.data['Active'], 'ScreenName']
        else:
            return self.data['ScreenName']

    def get_screen_colors(self, only_active=False):
        if only_active:
            return self.data.loc[self.data['Active'], 'Color']
        else:
            return self.data['Color']

    def get_active_status(self):
        return self.data['Active']

    def set_active_status(self, idx, status, emit=True):
        self.data.loc[idx, 'Active'] = bool(status)
        if emit:
            self.logger.debug('set_active_status: Emitting dataActiveChanged([%d])' % (idx, ))
            self.dataActiveChanged.emit([idx])

    def get_selected_screen_name(self):
        if self.params['SelectedActiveIdx'] != -1:
            return self.data.loc[self.params['SelectedActiveIdx'], 'ScreenName']
        else:
            return ''

    def get_peak_data_list(self, idx):
        return self.data.loc[idx, 'PeakDataList']

    def set_peak_data_list(self, idx, result, emit=True):
        self.data.loc[idx, 'PeakDataList'] = result
        if emit:
            self.logger.debug('set_peak_list: Emitting peakListChanged([%d])' % (idx, ))
            self.peakListChanged.emit([idx])

    def get_bckg_data_list(self, idx):
        return self.data.loc[idx, 'BckgDataList']

    def set_bckg_data_list(self, idx, result, emit=True):
        self.data.loc[idx, 'BckgDataList'] = result
        if emit:
            self.logger.debug('set_bckg_data_list: Emitting bckgListChanged([%d])' % (idx, ))
            self.bckgListChanged.emit([idx])

    def get_pd_tracks(self):
        if self.peak_tracks is None:
            return []
        else:
            return self.peak_tracks

    def set_pd_tracks(self, result, emit=True):
        self.peak_tracks = result
        if emit:
            self.logger.debug('set_pd_tracks: Emitting peakTracksChanged')
            self.peakTracksChanged.emit()

    def get_hkl_phases(self):
        return self.hkl_phases

    def set_hkl_phases(self, result, emit=True):
        self.hkl_phases = result
        if emit:
            self.logger.debug('set_hkl_phases: Emitting hklPhasesChanged')
            self.hklPhasesChanged.emit()

    def get_hkl_peaks(self):
        if self.hkl_peaks is None:
            return []
        else:
            return self.hkl_peaks

    def set_hkl_peaks(self, result, emit=True):
        self.hkl_peaks = result
        if emit:
            self.logger.debug('set_hkl_peaks: Emitting hklPeaksChanged')
            self.hklPeaksChanged.emit()

    @log_ex_time()
    def sort_data(self, **kwargs):
        if kwargs['by'] not in self.data.columns:
            self.data['_tmp'] = self.data['Motors'].apply(
                lambda x: 0 if x is None else (0 if x[kwargs['by']] is None else x[kwargs['by']])
            )
            kwargs['by'] = '_tmp'

        self.data.sort_values(**kwargs)

        if kwargs['by'] == '_tmp':
            self.data.drop(['_tmp'], axis=1, inplace=True)

        self.data.reset_index(drop=True, inplace=True)

        def reindex_peaks(row):
            if row['PeakDataList'] is not None:
                for pd in row['PeakDataList']:
                    pd.idx = row.name

        self.data.apply(reindex_peaks, axis=1)

        if self.peak_tracks is not None:
            for pt in self.peak_tracks:
                pt.sort_ids()

        self.logger.debug('sort_data: Emitting dataSorted')
        self.dataSorted.emit()

    def save_proj_as(self, f_name=None):
        if f_name is not None:
            self.proj_f_name = f_name

        if self.proj_f_name is None:
            return

        spectra = []
        for idx in self.data.index:
            row_data = dict()
            for k in ('DataX', 'DataY'):
                row_data[k] = self.data.loc[idx, k].tolist()
            for k in ('DeadTime', 'Channel', 'DataID', 'ScreenName', 'Chi2', 'Active'):
                row_data[k] = self.data.loc[idx, k]

            row_data['Motors'] = dict(self.data.loc[idx, 'Motors']) \
                if self.data.loc[idx, 'Motors'] is not None else None

            for k in ('PeakDataList', 'BckgDataList'):
                row_data[k] = []
                if self.data.loc[idx, k] is not None:
                    for item in self.data.loc[idx, k]:
                        row_data[k].append(item.to_dict())
            spectra.append(row_data)

        all_data = {
            'spectra': spectra,
            'hkl_peaks': self.hkl_peaks,
            'hkl_phases': [phase.to_dict() for phase in self.hkl_phases] if self.hkl_phases else None
        }

        try:
            all_data = pickle.dumps(all_data)
        except Exception as e:
            self.logger.error('save_proj_as: could not save file, pickle failed with exception: %s' % str(e))

        with open(self.proj_f_name, 'wb') as f:
            f.write(all_data)

        self.logger.debug('save_proj_as: saved as %s' % str(self.proj_f_name))

    def load_proj_from(self, f_name=None):
        if f_name is not None:
            self.proj_f_name = f_name

        if self.proj_f_name is None:
            return

        rows = list(self.data.index)
        self.data_model.removeRows(0, len(rows))
        self.dataRowsRemoved.emit(rows)
        self.peak_tracks = None
        self.hkl_phases = None
        self.hkl_peaks = None

        # raw_data = json.load(open(self.proj_f_name, 'r'))
        with open(self.proj_f_name, 'rb') as f:
            raw_data = pickle.loads(f.read())

        pr_data = pd.DataFrame(columns=self.data.columns)
        self.peak_tracks = dict()

        # process the data
        self.hkl_peaks = raw_data['hkl_peaks']
        self.hkl_phases = [PhaseData.from_dict(phase) for phase in raw_data['hkl_phases']] \
            if raw_data['hkl_phases'] else None
        raw_data = raw_data['spectra']

        for row in raw_data:
            pr_row = {c: None for c in pr_data.columns}

            peak_list = [PeakData.from_dict(peak) for peak in row['PeakDataList']]
            for peak in peak_list:
                if peak.track_id is not None:
                    if peak.track_id not in self.peak_tracks:
                        self.peak_tracks[peak.track_id] = PeakDataTrack(peak)
                    else:
                        self.peak_tracks[peak.track_id].append(peak)
                del peak.track_id

            pr_row.update({
                'DataX': np.array(row['DataX']),
                'DataY': np.array(row['DataY']),
                'Motors': defaultdict(lambda *args: None, row['Motors']) if row['Motors'] is not None else None,
                'Color': next(self.params['ColorWheel']),
                'Active': True,
                'PeakDataList': peak_list,
                'BckgDataList': [BckgData.from_dict(bckg) for bckg in row['BckgDataList']],
                **{k: row[k] for k in ('DeadTime', 'Channel', 'DataID', 'ScreenName', 'Chi2', 'Active')}
            })

            if row['Motors'] is not None:
                self.motors_all.update(row['Motors'].keys())

            pr_data.loc[pr_data.shape[0]] = pr_row

        self.data_model.insertRows(0, len(raw_data))
        self.data[0:len(raw_data)] = pr_data
        self.peak_tracks = list(sorted(self.peak_tracks.values(), key=lambda x: np.mean(x.cxs)))

        self.dataRowsInserted.emit(0, len(raw_data))
        self.data_model.dataChanged.emit(
            self.data_model.index(0, 0),
            self.data_model.index(len(raw_data), self.data_model.columnCount())
        )
        self.dataActiveChanged.emit(self.data.index.tolist())
        self.dataSorted.emit()
        # self.logger.debug('on_tw_result: Emitting dataRowsInserted(%d, %d)' % (0, len(raw_data)))
        self.peakTracksChanged.emit()
        self.hklPhasesChanged.emit()
        self.hklPeaksChanged.emit()

    def export_spectra_csv(self, ids):
        fd = QFileDialog()
        fd.setOption(fd.ShowDirsOnly, True)
        dirname = fd.getExistingDirectory(None, 'Export spectra as csv',
                                          os.path.join(self.data_dir, '..') if self.data_dir else None)

        if not dirname:
            return

        names = self.data.loc[ids, 'ScreenName'].apply(lambda x: x.replace(':', '_').replace('.', '_') + '.csv')
        overlap = set(os.listdir(dirname)) & set(names)
        ret = QMessageBox.Ok

        if overlap:
            msg = QMessageBox(None)
            msg.setText('Warning! The following files will be overwritten')
            msg.setInformativeText('\n'.join(sorted(overlap)))
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msg.exec()

        if ret == QMessageBox.Ok:
            for ii in ids:
                data = self.data.loc[ii, ['DataX', 'DataY', 'ScreenName']]
                f_name = data['ScreenName'].replace(':', '_').replace('.', '_') + '.csv'
                data = pd.DataFrame(data={'eV': 1E3 * data['DataX'], 'counts': data['DataY']})
                data = data[['eV', 'counts']]
                data.to_csv(os.path.join(dirname, f_name), header=True, index=False)

    def export_fit(self, f_name):
        tracks = self.get_pd_tracks()
        prefixes = ['pv%d' % ii for ii in range(len(tracks))]

        def expand_peaks(row):
            if row['PeakDataList'] is None:
                return row.drop(labels=['PeakDataList'])
            else:
                for track, prefix in zip(tracks, prefixes):
                    if row.name in track.ids:
                        name = row.name
                        row = row.append(pd.Series({'_'.join((prefix, k)): val
                                                    for (k, val) in track[row.name].export_ref_params().items()}))
                        row.name = name
                return row.drop(labels=['PeakDataList'])

        def expand_motors(row):
            if row['Motors'] is None:
                for motor in self.motors_all:
                    row[motor] = None
            else:
                for motor in self.motors_all:
                    row[motor] = row['Motors'][motor]
            return row.drop(labels=['Motors'])

        def add_phase_data(df):
            peak_centers = df.filter(regex='center$', axis=1)
            peak_centers = peak_centers.mean()
            for phase in self.get_hkl_peaks():
                peaks = self.hkl_peaks[phase]
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
        result = result.append(self.data.loc[self.data['Active'],
                                             ['ScreenName', 'Channel', 'DeadTime', 'PeakDataList', 'Motors', 'Chi2']])
        result = result.apply(expand_peaks, axis=1)
        result = result.apply(expand_motors, axis=1)
        result = add_phase_data(result)

        columns = list(sorted(result.columns))
        columns.remove('ScreenName')
        result = result[['ScreenName'] + columns]

        result.to_csv(f_name)
