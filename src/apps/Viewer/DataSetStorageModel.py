from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor
import logging


class DataSetStorageModel(QAbstractTableModel):
    def __init__(self, parent=None, instance=None):
        QAbstractTableModel.__init__(self, parent)

        self.q_app = instance
        self.logger = logging.getLogger(str(self.__class__))

        self.c_names = ('Name', 'Channel', u'💀⏱', u'χ²')

        self.q_app.genFitResChanged.connect(self.on_gen_fit_changed)

    def on_gen_fit_changed(self, rows):
        self.logger.debug('on_gen_fit_changed: Handling genFitResChanged(%s)' % (str(rows),))
        if rows:
            self.dataChanged.emit(
                self.index(min(rows), 0),
                self.index(max(rows), 4)
            )

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.c_names) + len(self.q_app.motors_cols)

    def rowCount(self, parent=None, *args, **kwargs):
        return self.q_app.data.shape[0]

    def headerData(self, section, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return (self.c_names + self.q_app.motors_cols)[section]

    def data(self, ii: QModelIndex, role=None):
        if not ii.isValid():
            return None

        item_row = self.q_app.data.loc[ii.row()]

        if ii.column() == 0:
            if role == Qt.DisplayRole:
                return item_row['ScreenName']
            elif role == Qt.CheckStateRole:
                return Qt.Checked if item_row['Active'] else Qt.Unchecked
            elif role == Qt.ForegroundRole:
                if item_row['Active']:
                    return QColor(item_row['Color'])
                else:
                    return QColor('Black')
            else:
                return None
        elif ii.column() == 1:
            if role == Qt.DisplayRole:
                return item_row['Channel']
            else:
                return None
        elif ii.column() == 2:
            if role == Qt.DisplayRole:
                return item_row['DeadTime']
            else:
                return None
        elif ii.column() == 3:
            if role == Qt.DisplayRole:
                if item_row['GeneralFitResult'] is not None:
                    if item_row['GeneralFitResult'].chisqr is not None:
                        return '%.01f' % item_row['GeneralFitResult'].chisqr
                    else:
                        return None
                else:
                    return None
            else:
                return None
        elif len(self.c_names) <= ii.column() < len(self.q_app.motors_cols) + len(self.c_names):
            if role == Qt.DisplayRole:
                if item_row['Motors'] is not None:
                    return item_row['Motors'][self.q_app.motors_cols[ii.column() - len(self.c_names)]]
                else:
                    return None
            else:
                return None
        else:
            return None

    def flags(self, ii: QModelIndex):
        if not ii.isValid():
            return 0

        result = super(QAbstractTableModel, self).flags(ii)

        if ii.column() == 0:
            result |= Qt.ItemIsUserCheckable

        return result

    def insertRows(self, position, rows, parent=QModelIndex(), *args, **kwargs):
        self.beginInsertRows(parent, position, position + rows - 1)
        self.q_app.insert_rows(position, rows)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, position, position + rows - 1)
        self.q_app.remove_rows(position, rows)
        self.endRemoveRows()
        return True

    def insertColumns(self, column: int, count: int, parent=QModelIndex(), *args, **kwargs) -> bool:
        self.beginInsertColumns(parent, column, column + count - 1)
        self.q_app.motors_cols = self.q_app.motors_cols[:column - len(self.c_names)] + ('', ) * count + \
                                 self.q_app.motors_cols[column - len(self.c_names):]
        self.endInsertColumns()
        return True

    def removeColumns(self, column: int, count: int, parent=QModelIndex(), *args, **kwargs) -> bool:
        self.beginRemoveColumns(parent, column, column + count - 1)
        self.q_app.motors_cols = self.q_app.motors_cols[:column - len(self.c_names)] + \
                                 self.q_app.motors_cols[column - len(self.c_names) + count:]
        self.endRemoveColumns()
        return True

    def setData(self, ii: QModelIndex, value, role=None):
        if ii.column() == 0 and role == Qt.CheckStateRole:
            self.q_app.set_active_status(ii.row(), bool(value))
            self.dataChanged.emit(ii, ii)
            return True
        else:
            return False

    def sort(self, column: int, order: Qt.SortOrder = ...) -> None:
        tmp = {0: 'ScreenName', 1: 'Channel', 2: 'DeadTime', 3: 'GeneralFitResult'}
        tmp.update({i + len(self.c_names): self.q_app.motors_cols[i] for i in range(len(self.q_app.motors_cols))})

        self.q_app.sort_data(by=tmp[column], inplace=True, ascending=bool(order))
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount(), self.columnCount())
        )