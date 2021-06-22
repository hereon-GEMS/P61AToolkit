from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QTableView, QAbstractItemView, QPushButton, QCheckBox, QGridLayout, QFileDialog, \
    QErrorMessage, QMessageBox, QHeaderView, QProgressDialog, QMenu
import os
import pandas as pd
import logging

from P61App import P61App
from ThreadIO import Worker
from DatasetIO import DatasetReaders


class FileOpenWorker(Worker):
    def __init__(self, files):
        def fn(fs):
            failed, opened = [], pd.DataFrame(columns=self.q_app.data.columns)
            for ii, file in enumerate(fs):
                if self.stop:
                    break
                try:
                    for reader in DatasetReaders:
                        if reader().validate(file):
                            opened = pd.concat((opened, reader().read(file)), ignore_index=True)
                            break
                    else:
                        failed.append(file)
                except Exception as e:
                    self.logger.info(str(e))
                    failed.append(file)

                self.threadWorkerStatus.emit(ii)
            return failed, opened

        self.stop = False

        super(FileOpenWorker, self).__init__(fn, args=[files], kwargs={})

        self.threadWorkerException = self.q_app.foWorkerException
        self.threadWorkerResult = self.q_app.foWorkerResult
        self.threadWorkerFinished = self.q_app.foWorkerFinished
        self.threadWorkerStatus = self.q_app.foWorkerStatus

    def halt(self):
        self.stop = True


class DatasetManager(QWidget):
    def __init__(self, parent=None, *args):
        QWidget.__init__(self, parent, *args)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))
        self.progress = None
        self._hold_md = None

        self.view = QTableView()
        self.view.setModel(self.q_app.data_model)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSortingEnabled(True)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.view.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.horizontalHeader().customContextMenuRequested.connect(self.show_header_menu)
        self.view.horizontalHeader().setSectionsMovable(True)
        self.context_menu = None
        self.cm_actions = []
        # self.view.horizontalHeader().setStretchLastSection(True)

        # buttons and checkbox
        self.bplus = QPushButton('+')
        self.bminus = QPushButton('-')
        self.checkbox = QCheckBox('')
        self.ch0_checkbox = QCheckBox('Ch0')
        self.ch1_checkbox = QCheckBox('Ch1')
        self.bexport = QPushButton('Export')
        self.checkbox.setTristate(False)
        self.bplus.setFixedSize(QSize(51, 32))
        self.bminus.setFixedSize(QSize(51, 32))
        self.bplus.clicked.connect(self.bplus_onclick)
        self.bminus.clicked.connect(self.bminus_onclick)
        self.bexport.clicked.connect(self.bexport_onclick)
        self.checkbox.clicked.connect(self.checkbox_onclick)
        self.ch0_checkbox.clicked.connect(self.ch0_cb_onclick)
        self.ch1_checkbox.clicked.connect(self.ch1_cb_onclick)

        # layouts
        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.checkbox, 1, 1, 1, 1)
        layout.addWidget(self.ch0_checkbox, 1, 2, 1, 1)
        layout.addWidget(self.ch1_checkbox, 1, 3, 1, 1)
        layout.addWidget(self.bplus, 1, 5, 1, 1)
        layout.addWidget(self.bminus, 1, 6, 1, 1)
        layout.addWidget(self.view, 2, 1, 1, 6)
        layout.addWidget(self.bexport, 3, 3, 1, 2)

        # signals and handlers
        self.view.selectionModel().selectionChanged.connect(self.checkbox_update)
        self.q_app.dataActiveChanged.connect(self.on_data_ac)
        self.q_app.foWorkerException.connect(self.on_tw_exception)
        self.q_app.foWorkerResult.connect(self.on_tw_result)
        self.q_app.foWorkerFinished.connect(self.on_tw_finished)

    def show_header_menu(self, point):
        self.context_menu = None
        del self.cm_actions[:]

        self.context_menu = QMenu(self)
        self.context_menu.triggered.connect(self.on_cm_triggered)

        for mt in self.q_app.motors_all:
            self.cm_actions.append(self.context_menu.addAction(mt))
            self.cm_actions[-1].setCheckable(True)
            self.cm_actions[-1].setChecked(mt in self.q_app.motors_cols)

        self.context_menu.popup(self.view.horizontalHeader().mapToGlobal(point))

    def on_cm_triggered(self, action):
        if not action.isChecked():
            action.setChecked(False)
            self.q_app.data_model.removeColumns(
                self.q_app.motors_cols.index(action.text()) + len(self.q_app.data_model.c_names), 1
            )
        else:
            action.setChecked(True)
            self.q_app.data_model.insertColumns(len(self.q_app.motors_cols) + len(self.q_app.data_model.c_names), 1)
            self.q_app.motors_cols = self.q_app.motors_cols[:-1] + (action.text(), )

            self.q_app.data_model.dataChanged.emit(
                self.q_app.data_model.index(0, self.q_app.data_model.columnCount()),
                self.q_app.data_model.index(self.q_app.data_model.rowCount(), self.q_app.data_model.columnCount())
            )

    def ch_cb_update(self):
        status = (self.q_app.data.loc[self.q_app.data['Channel'] == 0, 'Active'],
                  self.q_app.data.loc[self.q_app.data['Channel'] == 1, 'Active'])
        cb = (self.ch0_checkbox, self.ch1_checkbox)

        for status, cb in zip(status, cb):
            if all(status):
                cb.setCheckState(Qt.Checked)
            elif not any(status):
                cb.setCheckState(Qt.Unchecked)
            else:
                cb.setCheckState(Qt.PartiallyChecked)

    def on_data_ac(self, rows):
        self.logger.debug('on_data_ac: Handling dataActiveChanged(%s)' % (str(rows), ))
        self.checkbox_update()
        self.ch_cb_update()

    def bplus_onclick(self, *args, files=None):
        if self.progress is not None:
            return

        if files is None:
            fd = QFileDialog()
            files, _ = fd.getOpenFileNames(
                self,
                'Add spectra',
                self.q_app.data_dir,
                'FIO Files (*.fio);;NEXUS files (*.nxs);;All files (*)',
                options=QFileDialog.Options()
            )

        if not files:
            return

        self.q_app.data_dir = os.path.commonpath(files)
        if files[-1][-4:] == '.fio':
            self.q_app.proj_f_name_hint = os.path.basename(files[-1]).replace('.fio', '.json')

        self.progress = QProgressDialog("Opening files", "Cancel", 0, len(files))
        fw = FileOpenWorker(files)
        self.q_app.foWorkerStatus.connect(self.progress.setValue)

        cb = QPushButton('Cancel')
        cb.clicked.connect(lambda *args: fw.halt())
        self.progress.setCancelButton(cb)
        self.progress.show()

        if self.q_app.config['use_threads']:
            self.q_app.thread_pool.start(fw)
        else:
            fw.run()

    def on_tw_finished(self):
        self.logger.debug('on_tw_finished: Handling FileOpenWorker.threadWorkerFinished')
        if self.progress is not None:
            self.progress.close()
            self.progress = None

        if self._hold_md is not None:
            self.bplus_onclick(files=list(self._hold_md.keys()))

    def on_tw_exception(self, e):
        self.logger.debug('on_tw_exception: Handling FileOpenWorker.threadWorkerException')
        if self.progress is not None:
            self.progress.close()
            self.progress = None

    def on_tw_result(self, result):
        self.logger.debug('on_tw_result: Handling FileOpenWorker.threadWorkerResult')
        failed, opened = result

        if set(opened.columns) == set(self.q_app.data.columns):
            if self._hold_md is not None:
                opened['Motors'] = opened.apply(lambda rw: self._hold_md[':'.join(rw['DataID'].split(':')[:-1])], axis=1)
                self._hold_md = None

            self.q_app.data_model.insertRows(0, opened.shape[0])
            self.q_app.data[0:opened.shape[0]] = opened
            self.q_app.data_model.dataChanged.emit(
                self.q_app.data_model.index(0, 0),
                self.q_app.data_model.index(opened.shape[0], self.q_app.data_model.columnCount())
            )

            self.logger.debug('on_tw_result: Emitting dataRowsInserted(%d, %d)' % (0, opened.shape[0]))
            self.q_app.dataRowsInserted.emit(0, opened.shape[0])

            self.ch_cb_update()

            if failed:
                msg = QErrorMessage()
                msg.showMessage('Could not open files:\n' + '\n'.join(failed))
                msg.exec_()
        elif 'FNames' in opened.columns:
            for _, row in opened.iterrows():
                if row['Motors'] is not None:
                    self.q_app.motors_all.update(row['Motors'].keys())
            self._hold_md = {row['FNames']: row['Motors'] for _, row in opened.iterrows()}
            self.logger.info('Metadata extracted successfully, proceeding to open NeXuS files')
        else:
            self._hold_md = None

    @staticmethod
    def to_consecutive(lst):
        """
        Transforms a list of indices to a list of pairs (index, amount of consecutive indices after it)
        :param lst:
        :return:
        """
        if len(lst) == 1:
            return [(lst[0], 1), ]

        i1, i2 = 0, 1
        result = []
        while i2 < len(lst):
            if lst[i2] - lst[i1] == i2 - i1:
                i2 += 1
            else:
                result.append((lst[i1], i2 - i1))
                i1 = i2
                i2 += 1
        result.append((lst[i1], i2 - i1))
        return reversed(result)

    def bminus_onclick(self):
        if self.progress is not None:
            return
        rows = list(set(idx.row() for idx in self.view.selectedIndexes()))
        if len(rows) == 0:
            return

        for position, amount in self.to_consecutive(sorted(rows)):
            self.q_app.data_model.removeRows(position, amount)
        self.logger.debug('bminus_onclick: Emitting dataRowsRemoved(%s)' % (str(rows), ))
        self.q_app.dataRowsRemoved.emit(rows)

        self.ch_cb_update()

    def bexport_onclick(self):
        if self.progress is not None:
            return
        fd = QFileDialog()
        fd.setOption(fd.ShowDirsOnly, True)
        dirname = fd.getExistingDirectory(self, 'Export spectra as csv', os.path.join(self.q_app.data_dir, '..'))

        if not dirname:
            return

        rows = [idx.row() for idx in self.view.selectedIndexes()]
        rows = sorted(set(rows))

        names = self.q_app.data.loc[rows, 'ScreenName'].apply(lambda x: x.replace(':', '_').replace('.', '_') + '.csv')
        overlap = set(os.listdir(dirname)) & set(names)
        ret = QMessageBox.Ok

        if overlap:
            msg = QMessageBox(self)
            msg.setText('Warning! The following files will be overwritten')
            msg.setInformativeText('\n'.join(sorted(overlap)))
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msg.exec()

        if ret == QMessageBox.Ok:
            for ii in rows:
                data = self.q_app.data.loc[ii, ['DataX', 'DataY', 'ScreenName']]
                f_name = data['ScreenName'].replace(':', '_').replace('.', '_') + '.csv'
                data = pd.DataFrame(data={'eV': 1E3 * data['DataX'], 'counts': data['DataY']})
                data = data[['eV', 'counts']]
                data.to_csv(os.path.join(dirname, f_name), header=True, index=False)

    def checkbox_onclick(self):
        self.checkbox.setTristate(False)
        rows = sorted(set([idx.row() for idx in self.view.selectedIndexes()]))
        if len(rows) == 0:
            return

        for row in rows:
            self.q_app.set_active_status(row, bool(self.checkbox.checkState()), emit=False)

        self.q_app.data_model.dataChanged.emit(
            self.q_app.data_model.index(min(rows), 0),
            self.q_app.data_model.index(max(rows), 0),
        )

        self.logger.debug('checkbox_onclick: Emitting dataActiveChanged(%s)' % (str(rows),))
        self.q_app.dataActiveChanged.emit(rows)

    def ch0_cb_onclick(self, *args, **kwargs):
        self.ch_cb_onclick(self.ch0_checkbox, 0)

    def ch1_cb_onclick(self, *args, **kwargs):
        self.ch_cb_onclick(self.ch1_checkbox, 1)

    def ch_cb_onclick(self, cb, ch):
        cb.setTristate(False)

        rows = self.q_app.data.loc[self.q_app.data['Channel'] == ch].index.tolist()
        if len(rows) == 0:
            return

        for row in rows:
            self.q_app.set_active_status(row, bool(cb.checkState()), emit=False)

        self.q_app.data_model.dataChanged.emit(
            self.q_app.data_model.index(min(rows), 0),
            self.q_app.data_model.index(max(rows), 0),
        )

        self.logger.debug('ch_cb_onclick: Emitting dataActiveChanged(%s)' % (str(rows),))
        self.q_app.dataActiveChanged.emit(rows)

    def checkbox_update(self):
        rows = [idx.row() for idx in self.view.selectedIndexes()]
        status = self.q_app.get_active_status()
        status = status[rows]

        if all(status):
            self.checkbox.setCheckState(Qt.Checked)
        elif not any(status):
            self.checkbox.setCheckState(Qt.Unchecked)
        else:
            self.checkbox.setCheckState(Qt.PartiallyChecked)
