import lmfit
import numpy as np
import logging
import json


from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QMenu, QAction, QInputDialog, QTreeView, \
    QStyledItemDelegate, QStyleOptionViewItem, QHeaderView, QFileDialog, QCheckBox
from PyQt5.Qt import QAbstractItemModel, Qt, QModelIndex, QVariant

from FitWidgets.FloatEdit import FloatEdit
from FitWidgets.InitPopUp import InitPopUp
from P61App import P61App
import lmfit_utils


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
        self._upd()

        self.q_app.selectedIndexChanged.connect(self.on_selected_idx_ch)
        self.q_app.dataSorted.connect(self.on_data_sorted)
        self.q_app.genFitResChanged.connect(self.on_gen_fit_res_changed)

    def on_data_sorted(self):
        self.logger.debug('on_data_sorted: Handling dataSorted')
        self._upd()

    def on_selected_idx_ch(self, idx):
        self.logger.debug('on_selected_idx_ch: Handling selectedIndexChanged(%d)' % idx)
        self._upd()

    def on_gen_fit_res_changed(self, ids):
        self.logger.debug('on_gen_fit_res_changed: Handling genFitResChanged(%s)' % str(ids))
        self._upd()

    def _clear_tree(self):
        for item in self.rootItem.childItems:
            del item.childItems[:]
        del self.rootItem.childItems[:]

    def _upd(self, *args, **kwargs):
        idx = self.q_app.get_selected_idx()
        if idx == -1:
            self._fit_res = None
        else:
            self._fit_res = self.q_app.get_general_result(idx)

        self.modelAboutToBeReset.emit()  # so this is private apparently so look for a different way???
        self._clear_tree()

        if self._fit_res is not None:
            # for md in self._fit_res.model.components:
            for md in lmfit_utils.sort_components(self._fit_res):
                self.rootItem.appendChild(TreeNode(md, self.rootItem))

                for par in self._fit_res.params:
                    if md.prefix in par:
                        self.rootItem.childItems[-1].appendChild(
                            TreeNode(self._fit_res.params[par], self.rootItem.childItems[-1]))

        self.endResetModel()
        self.layoutChanged.emit()

    def columnCount(self, parent):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        data = index.internalPointer().itemData

        if role == Qt.DisplayRole:
            if isinstance(data, lmfit.Parameter):
                data = (data.name, '%.03E' % data.value, '± %.03E' % data.stderr
                        if data.stderr is not None else 'None', '%.03E' % data.min, '%.03E' % data.max)
            elif isinstance(data, lmfit.Model):
                if lmfit_utils.is_peak_md(data):
                    center = '%.1f: ' % self._fit_res.params[data.prefix + 'center'].value
                else:
                    center = ''
                data = (center + data.prefix + ' (' + data._name + ')', ) + ('', ) * 4
            return data[index.column()]
        elif role == Qt.CheckStateRole:
            if index.column() == 0 and isinstance(data, lmfit.Parameter):
                if lmfit_utils.is_param_refinable(data):
                    return Qt.Checked if data.vary else Qt.Unchecked
        elif role == Qt.EditRole:
            if isinstance(data, lmfit.Parameter):
                data = (data.name,
                        '%.03E' % data.value,
                        '± %.03E' % data.stderr if data.stderr is not None else 'None',
                        '%.03E' % data.min,
                        '%.03E' % data.max)
                return data[index.column()]

        return QVariant()

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        if index.column() == 0:
            return QAbstractItemModel.flags(self, index) | Qt.ItemIsUserCheckable
        elif index.column() in (1, 3, 4) and isinstance(index.internalPointer().itemData, lmfit.Parameter):
            if lmfit_utils.is_param_editable(index.internalPointer().itemData):
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
        result = self.q_app.get_general_result(self.q_app.get_selected_idx())

        if role == Qt.CheckStateRole and ii.column() == 0:
            result.params[data.name].set(vary=bool(value))
            self.q_app.set_general_result(self.q_app.get_selected_idx(), result)
            return True
        elif role == Qt.EditRole:
            if ii.column() == 1:
                if result.params[data.name].min > value:
                    result.params[data.name].set(min=value)
                if result.params[data.name].max < value:
                    result.params[data.name].set(max=value)

                result.params[data.name].set(value=value)
                self.q_app.set_general_result(self.q_app.get_selected_idx(), result)
                return True
            elif ii.column() == 3:
                result.params[data.name].set(min=value)
                self.q_app.set_general_result(self.q_app.get_selected_idx(), result)
                return True
            elif ii.column() == 4:
                result.params[data.name].set(max=value)
                self.q_app.set_general_result(self.q_app.get_selected_idx(), result)
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

        self.bplus = QPushButton('+')
        self.bminus = QPushButton('-')
        self.bopen = QPushButton('Open')
        self.bsave = QPushButton('Save')
        self.b_from_peaklist = QPushButton('Init from PT')
        # self.b_from_data = QPushButton('Init from data')
        self.treeview_md = LmfitInspectorModel()
        self._delegate = SpinBoxDelegate()
        self.treeview = QTreeView()
        self.treeview.setModel(self.treeview_md)
        self.treeview.setItemDelegate(self._delegate)
        self.treeview.expandAll()
        self.treeview.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.treeview.header().setStretchLastSection(True)

        self.menu = QMenu()

        for k in lmfit_utils.prefixes.keys():
            self.menu.addAction(k)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.b_from_peaklist, 1, 1, 1, 1)
        # layout.addWidget(self.b_from_data, 1, 2, 1, 1)
        layout.addWidget(self.bopen, 1, 3, 1, 1)
        layout.addWidget(self.bplus, 2, 1, 1, 1)
        layout.addWidget(self.bminus, 2, 2, 1, 1)
        layout.addWidget(self.bsave, 2, 3, 1, 1)
        layout.addWidget(self.treeview, 3, 1, 1, 3)

        self.bplus.clicked.connect(self.bplus_onclick)
        self.bminus.clicked.connect(self.bminus_onclick)
        self.bopen.clicked.connect(self.bopen_onclick)
        self.bsave.clicked.connect(self.bsave_onclick)
        self.b_from_peaklist.clicked.connect(self.from_peaklist_onclick)
        # self.b_from_data.clicked.connect(self.from_data_onclick)
        self.treeview_md.modelReset.connect(self.expander)

    def bopen_onclick(self):
        idx = self.q_app.get_selected_idx()
        if idx == -1:
            return

        file, _ = QFileDialog.getOpenFileName(self, "Open lmfit model",  "",
                                              "lmfit.ModelResult (*.mr);;All Files (*)")
        try:
            with open(file, 'r') as f:
                result = lmfit_utils.deserialize_model_result(json.load(f))
        except Exception as e:
            self.logger.error('bopen_onclick: during opening of %s an exception was raised: %s' % (file, str(e)))
            return

        if isinstance(result, lmfit.model.ModelResult):
            self.q_app.set_general_result(idx, result)

    def bsave_onclick(self):
        f_name, _ = QFileDialog.getSaveFileName(self, "Save fit model", "",
                                                "lmfit.ModelResult (*.mr);;All Files (*)")
        if not f_name:
            return

        idx = self.q_app.get_selected_idx()
        if idx == -1:
            return

        result = self.q_app.get_general_result(idx)
        if result is None:
            return

        with open(f_name, 'w') as f:
            json.dump(lmfit_utils.serialize_model_result(result), f)

    def from_peaklist_onclick(self):
        w = InitPopUp(parent=self)
        w.exec_()

    def init_from_peaklist(self, idx=-1, emit=True):
        if idx == -1:
            idx = self.q_app.get_selected_idx()

        if idx == -1:
            return

        tracks = self.q_app.get_pd_tracks()
        if tracks is None:
            return
        if not tracks:
            return

        self.q_app.set_general_result(idx, None, emit=False)
        result = self._add_model('ChebyshevModel', idx,
                                 {'c0': 0., 'c1': 0., 'c2': 0., 'c3': 0., 'c4': 0., 'c5': 0., 'c6': 0., 'c7': 0.},
                                 poly_deg_default=7)
        xx, yy = self.q_app.data.loc[idx, 'DataX'], self.q_app.data.loc[idx, 'DataY']

        min_cx, max_cx, max_base = 200, 0, 0
        for track in tracks:
            min_cx = np.min(track.cxs + [min_cx])
            max_cx = np.max(track.cxs + [max_cx])
            max_base = np.max([r - l for l, r in zip(track.l_bs, track.r_bs)] + [max_base])

            if idx in track.ids:
                result = lmfit_utils.add_peak_md('PseudoVoigtModel', track[idx], result)
            # else:
            #     result = lmfit_utils.add_peak_md('PseudoVoigtModel', track.predict_by_average(idx, xx, yy), result)

        result.params['che0_xmin'].value = min_cx - max_base
        result.params['che0_xmax'].value = max_cx + max_base
        result = lmfit_utils.update_metrics(result, x=xx, data=yy)
        self.q_app.set_general_result(idx, result, emit=emit)

    def from_data_onclick(self):
        idx = self.q_app.get_selected_idx()
        result = self.q_app.get_general_result(idx)
        if result is None:
            return
        # get x and y data
        xx, yy = self.q_app.data.loc[idx, 'DataX'], self.q_app.data.loc[idx, 'DataY']
        # get difference values
        diff = self.fitPlot.get_diff()
        # get current range on x axis
        x_lim = self.fitPlot.get_axes_xlim()
        # select only shown data on screen
        if diff is not None:
            diff = diff[(xx > x_lim[0]) & (xx < x_lim[1])]
        yy = yy[(xx > x_lim[0]) & (xx < x_lim[1])]
        xx = xx[(xx > x_lim[0]) & (xx < x_lim[1])]
        # get current parameters of fit models
        parNamesParts = np.array([name.split('_', 1) for name in result.model.param_names])
        model_parts = np.unique(parNamesParts[:, 0])
        # parNames = np.unique(parNamesParts[:, 1])
        # select only distribution models
        model_parts = model_parts[[name.find('g') >= 0 or name.find('sg') >= 0 or name.find('lor') >= 0 or
                                   name.find('pvii') >= 0 or name.find('pv') >= 0 or name.find('sv') >= 0 or
                                   name.find('spl') >= 0 for name in model_parts]]
        par_vals = np.zeros((len(model_parts), 3))
        for i in range(len(model_parts)):
            par_vals[i, 0] = result.params[model_parts[i] + '_amplitude'].value
            par_vals[i, 1] = result.params[model_parts[i] + '_center'].value
            par_vals[i, 2] = result.params[model_parts[i] + '_sigma'].value
        # check current parameters of fit models
        # test_ind = 5  # distance to maximum value to estimate sigma parameter
        if sum(par_vals[:, 1]) == 0:
            # all centers are not initialized - predetermine all parameters
            x_step = (x_lim[1] - x_lim[0]) / len(model_parts)
            for i in range(len(model_parts)):
                xx_sel = (xx > x_lim[0] + i * x_step) & (xx < x_lim[0] + (i + 1) * x_step)
                if xx_sel.size > 0 and np.any(xx_sel):
                    par_vals[i, :] = self.estimate_pear_params(xx[xx_sel], yy[xx_sel])
        else:
            # some models have an initialization - optimize these parameters first (only if inside current range)
            for i in range(len(model_parts)):
                if (x_lim[0] < par_vals[i, 1]) & (par_vals[i, 1] < x_lim[1]):
                    # this model is inside current value range
                    xx_sel = (0.9 * par_vals[i, 1] < xx) & (xx < 1.1 * par_vals[i, 1])
                    if xx_sel.size > 0 and np.any(xx_sel):
                        par_vals[i, :] = self.estimate_pear_params(xx[xx_sel], yy[xx_sel])
            # now try to get some initial parameters for uninitialized models
            uninit_models = par_vals[:, 1] == 0
            x_step = (x_lim[1] - x_lim[0]) / sum(uninit_models)
            count = 0
            for i in np.where(uninit_models):
                xx_sel = (xx > x_lim[0] + count * x_step) & (xx < x_lim[0] + (count + 1) * x_step)
                count += 1
                if xx_sel.size > 0 and np.any(xx_sel):
                    par_vals[i, :] = self.estimate_pear_params(xx[xx_sel], diff[xx_sel])
        # set adapted values as model parameters
        for i in range(len(model_parts)):
            result.params[model_parts[i] + '_amplitude'].value = par_vals[i, 0]
            result.params[model_parts[i] + '_center'].value = par_vals[i, 1]
            result.params[model_parts[i] + '_sigma'].value = par_vals[i, 2]
        # accept changes and update view
        self.q_app.set_general_result(idx, result)

    def estimate_pear_params(self, xx, yy, test_ind=5):
        max_ind = np.argmax(yy)
        max_val = yy[max_ind]
        l_sigma = 0
        r_sigma = 0
        if max_ind > test_ind:
            l_sigma = np.abs(xx[max_ind - test_ind] - xx[max_ind]) / (
                    2 * (np.log(max_val) - np.log(yy[max_ind - test_ind]))) ** 0.5
            est_sigma = l_sigma
        if max_ind < len(xx):
            r_sigma = np.abs(xx[max_ind + test_ind] - xx[max_ind]) / (2 * (np.log(max_val) - np.log(yy[max_ind + test_ind]))) ** 0.5
            est_sigma = r_sigma
        if l_sigma > 0 and r_sigma > 0:
            est_sigma = np.mean([l_sigma, r_sigma])
        self.logger.debug('estimate_peak_params: amplitude %f, center %f, sigma %f' % (max_val, xx[max_ind], est_sigma))
        return max_val, xx[max_ind], est_sigma

    def expander(self, *args, **kwargs):
        self.treeview.expandAll()

    def bplus_onclick(self):
        name = self.menu.exec(self.mapToGlobal(self.bplus.pos()))
        idx = self.q_app.get_selected_idx()

        if not isinstance(name, QAction) or idx == -1:
            return

        new_md = self._add_model(name.text(), idx, poly_deg_default=False)
        self.q_app.set_general_result(idx, new_md)

    def bminus_onclick(self):
        selected_obj = self.treeview.currentIndex().internalPointer()
        if selected_obj is None:
            return

        if isinstance(selected_obj.itemData, lmfit.Model):
            prefix = selected_obj.itemData.prefix
            result = lmfit_utils.rm_md(prefix, self.q_app.get_general_result(self.q_app.get_selected_idx()))
            self.q_app.set_general_result(self.q_app.get_selected_idx(), result)

    def _add_model(self, name, idx, init_params=dict(), poly_deg_default=7):
        old_res = self.q_app.get_general_result(idx)

        if name == 'ChebyshevModel':
            if not poly_deg_default:
                ii, ok = QInputDialog.getInt(self, 'Polynomial degree', 'Polynomial degree', 7, 2, 11, 1)
                if ok:
                    init_params['degree'] = ii
            else:
                init_params['degree'] = poly_deg_default

            for i in range(init_params['degree'] + 1):
                init_params['c%d' % i] = 0.

        result = lmfit_utils.add_md(name, init_params, old_res)
        return result
