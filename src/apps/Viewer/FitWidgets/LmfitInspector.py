import lmfit
import numpy as np
import logging
import json
from uncertainties import ufloat


from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QMenu, QAction, QTreeView, \
    QStyledItemDelegate, QStyleOptionViewItem, QHeaderView
from PyQt5.Qt import QAbstractItemModel, Qt, QModelIndex, QVariant

from FitWidgets.CopyPopUp import CopyPopUp
from FitWidgets.FloatEdit import FloatEdit
from P61App import P61App
from peak_fit_utils import background_models, BckgData


class TreeNode(object):
    """"""
    def __init__(self, data, parent=None, lvl=0):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


class LmfitInspectorModel(QAbstractItemModel):
    """"""

    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.rootItem = TreeNode(('Name', 'Value', 'STD', 'Min', 'Max'))
        self._fit_res = None
        self._peak_list = None
        self._upd()

        self.q_app.selectedIndexChanged.connect(self.on_selected_idx_ch)
        self.q_app.dataSorted.connect(self.on_data_sorted)
        self.q_app.peakListChanged.connect(self.on_pl_changed)
        self.q_app.peakTracksChanged.connect(self.on_pt_changed)
        self.q_app.bckgListChanged.connect(self.on_bckg_changed)

    def on_data_sorted(self):
        self.logger.debug('on_data_sorted: Handling dataSorted')
        self._upd()

    def on_selected_idx_ch(self, idx):
        self.logger.debug('on_selected_idx_ch: Handling selectedIndexChanged(%d)' % idx)
        self._upd()

    def on_pl_changed(self, ids):
        self.logger.debug('on_pl_changed: Handling peakListChanged(%s)' % str(ids))
        self._upd()

    def on_pt_changed(self):
        self.logger.debug('on_pt_changed: Handling peakTracksChanged')
        self._upd()

    def on_bckg_changed(self, ids):
        self.logger.debug('on_bckg_changed: Handling bckgListChanged(%s)' % str(ids))
        self._upd()

    def _clear_tree(self):
        for item in self.rootItem.childItems:
            del item.childItems[:]
        del self.rootItem.childItems[:]

    def _upd(self, *args, **kwargs):
        idx = self.q_app.get_selected_idx()
        if idx == -1:
            self._bckg_list = None
            self._peak_list = None
        else:
            self._bckg_list = self.q_app.get_bckg_data_list(idx)
            self._peak_list = self.q_app.get_peak_data_list(idx)

        self._peak_list = self._peak_list if self._peak_list is not None else []
        self._bckg_list = self._bckg_list if self._bckg_list is not None else []

        self.modelAboutToBeReset.emit()  # so this is private apparently so look for a different way???
        self._clear_tree()

        if self._bckg_list is not None:
            for b_md in self._bckg_list:
                self.rootItem.appendChild(TreeNode('[{}, {}]: {}'.format(b_md.md_params['xmin'].n,
                                                                         b_md.md_params['xmax'].n,
                                                                         b_md.md_name),
                                                   self.rootItem))
                for par in b_md.md_params.keys():
                    self.rootItem.childItems[-1].appendChild(
                        TreeNode((None, par,
                                  '%.03E' % b_md.md_params[par].nominal_value,
                                  '%.03E' % b_md.md_params[par].std_dev,
                                  '%.03E' % b_md.md_p_bounds[par][0],
                                  '%.03E' % b_md.md_p_bounds[par][1]), self.rootItem.childItems[-1]))

        if self._peak_list is not None:
            for peak in self._peak_list:
                self.rootItem.appendChild(TreeNode('{:0.1f}: {}'.format(peak.md_params['center'], peak.md_name),
                                                   self.rootItem))
                for par in peak.md_param_keys():
                    self.rootItem.childItems[-1].appendChild(
                                        TreeNode((peak.md_p_refine[par] if par in peak.md_p_refine else None, par,
                                                  '%.03E' % peak.md_params[par].nominal_value,
                                                  '%.03E' % peak.md_params[par].std_dev,
                                                  '%.03E' % peak.md_p_bounds[par][0],
                                                  '%.03E' % peak.md_p_bounds[par][1]), self.rootItem.childItems[-1]))

        self.endResetModel()
        self.layoutChanged.emit()

    def columnCount(self, parent):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        data = index.internalPointer().itemData

        if role == Qt.DisplayRole:
            if isinstance(data, tuple):
                data = data[1:]
            elif isinstance(data, str):
                data = (data, ) + ('', ) * 4
            return data[index.column()]
        elif role == Qt.CheckStateRole:
            if index.column() == 0 and isinstance(data, tuple):
                if data[0] is not None:
                    return Qt.Checked if data[0] else Qt.Unchecked
        elif role == Qt.EditRole:
            if isinstance(data, tuple):
                return data[index.column() + 1]

        return QVariant()

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        data = index.internalPointer().itemData

        if index.column() == 0 and data[0] is not None:
            return QAbstractItemModel.flags(self, index) | Qt.ItemIsUserCheckable
        elif index.column() == 1 and isinstance(index.internalPointer().itemData, tuple):
            if data[1] not in ('width', 'height', 'rwp2', 'chi2'):
                return QAbstractItemModel.flags(self, index) | Qt.ItemIsEditable
            else:
                return QAbstractItemModel.flags(self, index)
        elif index.column() in (3, 4) and isinstance(index.internalPointer().itemData, tuple):
            if data[1] not in ('width', 'height', 'rwp2', 'chi2') and index.parent().row() >= len(self._bckg_list):
                return QAbstractItemModel.flags(self, index) | Qt.ItemIsEditable
            else:
                return QAbstractItemModel.flags(self, index)
        else:
            return QAbstractItemModel.flags(self, index)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.itemData[section]

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setData(self, ii: QModelIndex, value, role=None):
        if not ii.isValid():
            return False

        item = ii.internalPointer()
        data = item.itemData
        peak_list = self.q_app.get_peak_data_list(self.q_app.get_selected_idx())
        bckg_list = self.q_app.get_bckg_data_list(self.q_app.get_selected_idx())

        peak_list = peak_list if peak_list is not None else []
        bckg_list = bckg_list if bckg_list is not None else []

        if ii.parent().row() >= len(bckg_list):
            parent_row = ii.parent().row() - len(bckg_list)

            if role == Qt.CheckStateRole and ii.column() == 0:
                peak_list[parent_row].md_p_refine[data[1]] = bool(value)
                self.q_app.set_peak_data_list(self.q_app.get_selected_idx(), peak_list)
                return True
            elif role == Qt.EditRole:
                if ii.column() == 1:
                    # updating min and max bounds
                    if peak_list[parent_row].md_p_bounds[data[1]][0] > value:
                        peak_list[parent_row].md_p_bounds[data[1]] = \
                            (value, peak_list[parent_row].md_p_bounds[data[1]][1])
                    if peak_list[parent_row].md_p_bounds[data[1]][1] < value:
                        peak_list[parent_row].md_p_bounds[data[1]] = \
                            (peak_list[parent_row].md_p_bounds[data[1]][0], value)

                    peak_list[parent_row].md_params[data[1]] = ufloat(value, np.nan)
                    peak_list[parent_row].upd_nref_params()

                    if data[1] == 'center':
                        peak_list = list(sorted(peak_list, key=lambda item: item.md_params['center']))

                    self.q_app.set_peak_data_list(self.q_app.get_selected_idx(), peak_list)
                    return True
                elif ii.column() == 3:
                    peak_list[parent_row].md_p_bounds[data[1]] = \
                        (value, peak_list[parent_row].md_p_bounds[data[1]][1])
                    peak_list[parent_row].upd_nref_params()
                    self.q_app.set_peak_data_list(self.q_app.get_selected_idx(), peak_list)
                    return True
                elif ii.column() == 4:
                    peak_list[parent_row].md_p_bounds[data[1]] = \
                        (peak_list[parent_row].md_p_bounds[data[1]][0], value)
                    peak_list[parent_row].upd_nref_params()
                    self.q_app.set_peak_data_list(self.q_app.get_selected_idx(), peak_list)
                    return True
        else:
            if role == Qt.EditRole and ii.column() == 1:

                if bckg_list[ii.parent().row()].md_p_bounds[data[1]][0] > value:
                    value = bckg_list[ii.parent().row()].md_p_bounds[data[1]][0]
                if bckg_list[ii.parent().row()].md_p_bounds[data[1]][1] < value:
                    value = bckg_list[ii.parent().row()].md_p_bounds[data[1]][1]

                bckg_list[ii.parent().row()].md_params[data[1]] = ufloat(value, np.nan)
                bckg_list = list(sorted(bckg_list, key=lambda item: item.md_params['xmin'] + item.md_params['xmax']))

                self.q_app.set_bckg_data_list(self.q_app.get_selected_idx(), bckg_list)
                return True
        return False


class SpinBoxDelegate(QStyledItemDelegate):
    """

    """
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, w: QWidget, s: QStyleOptionViewItem, ii: QModelIndex):
        editor = FloatEdit(parent=w)
        return editor

    def setEditorData(self, w: QWidget, ii: QModelIndex):
        w.value = float(ii.model().data(ii, Qt.EditRole))

    def setModelData(self, w: QWidget, model: QAbstractItemModel, ii: QModelIndex):
        model.setData(ii, w.value, Qt.EditRole)

    def updateEditorGeometry(self, w: QWidget, s: QStyleOptionViewItem, ii: QModelIndex):
        w.setGeometry(s.rect)


class LmfitInspector(QWidget):
    """

    """
    def __init__(self, parent=None, fitPlot=None):
        QWidget.__init__(self, parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))
        self.fitPlot = fitPlot

        self.btn_add_bckg = QPushButton('+ background')
        self.btn_rm_bckg = QPushButton('- background')
        self.btn_cp_bckg = QPushButton('Copy background')

        self.treeview_md = LmfitInspectorModel()
        self._delegate = SpinBoxDelegate()
        self.treeview = QTreeView()
        self.treeview.setModel(self.treeview_md)
        self.treeview.setItemDelegate(self._delegate)
        self.treeview.expandAll()
        self.treeview.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.treeview.header().setStretchLastSection(True)

        self.menu = QMenu()
        for k in background_models.keys():
            self.menu.addAction(k)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.btn_add_bckg, 1, 1, 1, 1)
        layout.addWidget(self.btn_rm_bckg, 1, 2, 1, 1)
        layout.addWidget(self.btn_cp_bckg, 1, 3, 1, 1)
        layout.addWidget(self.treeview, 2, 1, 1, 3)

        self.treeview_md.modelReset.connect(self.expander)
        self.btn_add_bckg.clicked.connect(self.btn_add_onclick)
        self.btn_cp_bckg.clicked.connect(self.btn_copy_onclick)
        self.btn_rm_bckg.clicked.connect(self.btn_rm_onclick)

    def expander(self, *args, **kwargs):
        self.treeview.expandAll()

    def btn_add_onclick(self):
        name = self.menu.exec(self.mapToGlobal(self.btn_add_bckg.pos()))
        idx = self.q_app.get_selected_idx()

        if not isinstance(name, QAction) or idx == -1:
            return

        bckg_model_list = self.q_app.get_bckg_data_list(idx)
        new_md = BckgData(model=name.text())

        if bckg_model_list is None:
            self.q_app.set_bckg_data_list(idx, [new_md])
        else:
            bckg_model_list.append(new_md)
            self.q_app.set_bckg_data_list(idx, bckg_model_list)

    def btn_copy_onclick(self):
        w = CopyPopUp(parent=self)
        w.exec_()

    def btn_rm_onclick(self):
        selected_obj = self.treeview.currentIndex().internalPointer()
        if selected_obj is None:
            return
        if isinstance(selected_obj.itemData, str):
            row = selected_obj.row()

            bckg_list = self.q_app.get_bckg_data_list(self.q_app.get_selected_idx())
            if bckg_list is None:
                return

            if row < len(bckg_list):
                bckg_list = bckg_list[:row] + bckg_list[row + 1:]
                self.q_app.set_bckg_data_list(self.q_app.get_selected_idx(), bckg_list)