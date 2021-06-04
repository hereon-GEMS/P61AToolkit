from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMenu, QAction
import logging

from P61App import P61App
from PlotWidgets import FitPlot


class PhasesAndElementsWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.bplus = QPushButton('+')
        self.bminus = QPushButton('-')

        self.bplus.clicked.connect(self.bplus_onclick)
        self.bminus.clicked.connect(self.bminus_onclick)

        self.menu = QMenu()
        self.menu.addAction('Element')
        self.menu.addAction('Phase')

        self.q_app.dataRowsInserted.connect(self.on_data_rows_appended)
        self.q_app.dataRowsRemoved.connect(self.on_data_rows_removed)
        self.q_app.dataActiveChanged.connect(self.on_data_active_changed)

        self.constrain_btn = QPushButton('Constrain parameters')
        self.bckg_fit_btn = QPushButton('Fit Background')
        self.peaks_fit_btn = QPushButton('Fit peaks')
        self.fit_all_btn = QPushButton('Fit multiple')
        self.copy_btn = QPushButton('Copy params')
        self.export_btn = QPushButton('Export')
        self.plot_w = FitPlot(parent=self)

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.bplus, 2, 1, 1, 1)
        layout.addWidget(self.bminus, 2, 3, 1, 1)

        layout.addWidget(self.constrain_btn, 4, 1, 1, 1)
        layout.addWidget(self.bckg_fit_btn, 5, 1, 1, 1)
        layout.addWidget(self.peaks_fit_btn, 6, 1, 1, 1)
        layout.addWidget(self.copy_btn, 7, 1, 1, 1)
        layout.addWidget(self.fit_all_btn, 8, 1, 1, 1)
        layout.addWidget(self.export_btn, 9, 1, 1, 1)
        layout.addWidget(self.plot_w, 1, 4, 8, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(4, 6)

    def bplus_onclick(self):
        name = self.menu.exec(self.mapToGlobal(self.bplus.pos()))
        idx = self.q_app.get_selected_idx()

        if not isinstance(name, QAction) or idx == -1:
            return

        self._add_model(name.text(), idx, poly_deg_default=False)

    def bminus_onclick(self):
        selected_obj = self.treeview.currentIndex().internalPointer()
        if selected_obj is None:
            return

    def line_init(self, ii):
        data = self.q_app.data.loc[ii, ['DataX', 'DataY', 'Color']]
        self._lines[ii] = self._line_ax.plot(1E3 * data['DataX'], data['DataY'],
            pen=str(hex(data['Color'])).replace('0x', '#'))

    def line_remove(self, ii):
        self._line_ax.removeItem(self._lines[ii])
        self._lines.pop(ii)

    def line_set_visibility(self, ii):
        if self.q_app.data.loc[ii, 'Active']:
            self._lines[ii].setPen(str(hex(self.q_app.data.loc[ii, 'Color'])).replace('0x', '#'))
        else:
            self._lines[ii].setPen(None)

    def on_data_rows_appended(self, pos, n_rows):
        self.logger.debug('on_data_rows_appended: Handling dataRowsInserted(%d, %d)' % (pos, n_rows))
        self._lines = self._lines[:pos] + [None] * n_rows + self._lines[pos:]
        for ii in range(pos, pos + n_rows):
            self.line_init(ii)

    def on_data_rows_removed(self, rows):
        self.logger.debug('on_data_rows_removed: Handling dataRowsRemoved(%s)' % (str(rows),))
        for ii in sorted(rows, reverse=True):
            self.line_remove(ii)

    def on_data_active_changed(self, rows):
        self.logger.debug('on_data_active_changed: Handling dataActiveChanged(%s)' % (str(rows),))
        for ii in rows:
            self.line_set_visibility(ii)


if __name__ == '__main__':
    import sys
    q_app = P61App(sys.argv)
    app = PhasesAndElementsWidget()
    app.show()
    sys.exit(q_app.exec())
