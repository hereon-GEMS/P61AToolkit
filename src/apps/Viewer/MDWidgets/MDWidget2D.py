from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QFileDialog, QTabWidget, QLabel, QComboBox
from PyQt5.QtCore import Qt
import logging

from P61App import P61App
from PlotWidgets import MetaDataPlot2D


class MetaDataWidget2D(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        layout = QGridLayout()

        self.lbl_x = QLabel('Data X', parent=self)
        self.lbl_x.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.lbl_x, 1, 1, 1, 1)

        self.lbl_y = QLabel('Data Y', parent=self)
        self.lbl_y.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.lbl_y, 1, 3, 1, 1)

        self.cb_x = QComboBox(parent=self)
        layout.addWidget(self.cb_x, 1, 2, 1, 1)

        self.cb_y = QComboBox(parent=self)
        layout.addWidget(self.cb_y, 1, 4, 1, 1)

        self.plot = MetaDataPlot2D(parent=self)
        layout.addWidget(self.plot, 2, 1, 1, 5)

        self.setLayout(layout)

        self.upd_cbs()

        self.q_app.motorListUpdated.connect(self.on_mt_list_updated)
        self.q_app.peakTracksChanged.connect(self.on_mt_list_updated)
        self.cb_x.currentIndexChanged.connect(self.on_btn_plot)
        self.cb_y.currentIndexChanged.connect(self.on_btn_plot)

    def upd_cbs(self):
        self.cb_x.clear()
        for mt in sorted(self.q_app.motors_all):
            self.cb_x.addItem(mt)

        self.cb_y.clear()
        for mt in sorted(self.q_app.motors_all):
            self.cb_y.addItem(mt)

        for ii, track in enumerate(self.q_app.get_pd_tracks()):
            for param in ('center', 'amplitude', 'sigma'):
                self.cb_y.addItem('Track ' + str(ii) + ': ' + param)

    def on_mt_list_updated(self, *args, **kwargs):
        self.logger.debug('on_mt_list_updated: Handling motorListUpdated(%s, %s)' % (str(args), str(kwargs)))
        self.upd_cbs()

    def on_btn_plot(self):
        self.plot.set_variables(self.cb_x.currentText(), self.cb_y.currentText())