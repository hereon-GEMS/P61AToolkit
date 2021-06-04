from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PyQt5.QtWidgets import QWidget, QTableView, QAbstractItemView, QGridLayout, QCheckBox, QHeaderView

from P61App import P61App
import logging


class SelectorProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None, *args):
        QSortFilterProxyModel.__init__(self, parent)
        self.q_app = P61App.instance()
        self.selected = {k: True for k in self.q_app.data[self.q_app.data['Active']].index}

        self.setDynamicSortFilter(True)
        self.q_app.dataSorted.connect(self.on_data_sorted)

    def on_data_sorted(self):
        self.logger.debug('on_data_sorted: Handling dataSorted)')
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent: QModelIndex):
        active = self.q_app.data.loc[source_row, 'Active']
        return True if active is None else active

    def columnCount(self, parent=None, *args, **kwargs):
        return 2

    def headerData(self, section, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ['Select', 'Name'][section]

    def data(self, ii: QModelIndex, role=None):
        if not ii.isValid():
            return None

        if ii.column() == 0:
            if role == Qt.CheckStateRole:
                return Qt.Checked if self.selected[self.mapToSource(ii).row()] else Qt.Unchecked
            else:
                return None
        elif ii.column() == 1:
            if role == Qt.CheckStateRole:
                return None
            else:
                return QSortFilterProxyModel.data(self, self.index(ii.row(), 0), role)

    def flags(self, ii: QModelIndex):
        if not ii.isValid():
            return 0

        result = super(QSortFilterProxyModel, self).flags(ii)
        if ii.column() == 1:
            result ^= Qt.ItemIsUserCheckable
        elif ii.column() == 0:
            result |= Qt.ItemIsUserCheckable

        return result

    def setData(self, ii: QModelIndex, value, role=None):
        if not ii.isValid():
            return False

        if ii.column() == 0 and role == Qt.CheckStateRole:
            sr = self.mapToSource(ii).row()
            self.selected[sr] = bool(value)
            self.dataChanged.emit(ii, ii)
            return True
        else:
            return False


class DatasetSelector(QWidget):
    def __init__(self, parent=None, *args):
        QWidget.__init__(self, parent, *args)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.view = QTableView()
        self.proxy = None
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.view.horizontalHeader().setStretchLastSection(True)

        self.checkbox = QCheckBox('')
        self.checkbox.setTristate(False)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.checkbox, 1, 1, 1, 1)
        layout.addWidget(self.view, 2, 1, 1, 4)

        self.setup_model()

    def setup_model(self):
        self.proxy = SelectorProxyModel()
        self.proxy.setSourceModel(self.q_app.data_model)
        self.view.setModel(self.proxy)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.checkbox.clicked.connect(self.checkbox_onclick)
        self.view.selectionModel().selectionChanged.connect(self.checkbox_update)

    def checkbox_onclick(self):
        self.checkbox.setTristate(False)
        rows = sorted(set([idx.row() for idx in self.view.selectedIndexes()]))
        for row in rows:
            self.proxy.selected[self.proxy.mapToSource(self.proxy.index(row, 0)).row()] = \
                bool(self.checkbox.checkState())
        if rows:
            self.proxy.dataChanged.emit(
                self.proxy.index(min(rows), 0),
                self.proxy.index(max(rows), 0),
            )

    def checkbox_update(self):
        rows = sorted(set([idx.row() for idx in self.view.selectedIndexes()]))
        status = [self.proxy.selected[self.proxy.mapToSource(self.proxy.index(row, 0)).row()] for row in rows]

        if all(status):
            self.checkbox.setCheckState(Qt.Checked)
        elif not any(status):
            self.checkbox.setCheckState(Qt.Unchecked)
        else:
            self.checkbox.setCheckState(Qt.PartiallyChecked)

    def get_selected(self):
        return [k for k in self.proxy.selected if self.proxy.selected[k]]

    def set_selected(self, ids_true):
        for k in self.proxy.selected:
            self.proxy.selected[k] = k in ids_true
        return
