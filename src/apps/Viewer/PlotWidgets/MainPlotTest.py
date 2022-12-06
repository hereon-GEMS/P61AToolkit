from PyQt5.QtWidgets import QWidget, QGridLayout, QTabWidget, QLabel, QCheckBox, QComboBox, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt, QSize
import logging
import numpy as np


from P61App import P61App
from PlotWidgets import MainPlot3D, MainPlot3DWidget, MainPlot2D, MainPlotAvg


class MainPlot3DTestWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.p3d = MainPlot3DWidget(MainPlot3D(parent=self), parent=self)
        self.p3d.plot.metavars = ['DeadTime']
        self.cb_surf = QCheckBox('Surface')
        self.cb_col = QCheckBox('Colored')
        self.cb_p = QCheckBox('Show peaks')
        self.cb_t = QCheckBox('Show tracks')
        self.cb_hkl = QCheckBox('Show hkl')
        self.cb_char = QCheckBox('Show fluorescence (In, W, Pb)')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.cb_surf, 1, 1, 1, 1)
        layout.addWidget(self.cb_col,  1, 2, 1, 1)
        layout.addWidget(self.cb_p,    1, 3, 1, 1)
        layout.addWidget(self.cb_t,    1, 4, 1, 1)
        layout.addWidget(self.cb_hkl,  1, 5, 1, 1)
        layout.addWidget(self.cb_char, 1, 6, 1, 1)
        layout.addWidget(self.p3d,     2, 1, 1, 6)

        self.cb_surf.clicked.connect(self.on_surf_click)
        self.cb_col.clicked.connect(self.on_col_click)
        self.cb_p.clicked.connect(self.on_p_click)
        self.cb_t.clicked.connect(self.on_t_click)
        self.cb_hkl.clicked.connect(self.on_hkl_click)
        self.cb_char.clicked.connect(self.on_char_click)

        self.cb_surf.setChecked(True)
        self.cb_p.setChecked(True)
        self.cb_t.setChecked(True)

        self.on_surf_click()
        self.on_p_click()
        self.on_t_click()

    def on_surf_click(self):
        if self.cb_surf.isChecked():
            self.p3d.plot.surface = True
        else:
            self.p3d.plot.surface = False

    def on_col_click(self):
        if self.cb_col.isChecked():
            self.p3d.plot.colored = True
        else:
            self.p3d.plot.colored = False

    def on_p_click(self):
        if self.cb_p.isChecked():
            self.p3d.plot.show_pt_points = True
        else:
            self.p3d.plot.show_pt_points = False

    def on_t_click(self):
        if self.cb_t.isChecked():
            self.p3d.plot.show_pt_tracks = True
        else:
            self.p3d.plot.show_pt_tracks = False

    def on_hkl_click(self):
        if self.cb_hkl.isChecked():
            self.p3d.plot.show_known_regions = True
        else:
            self.p3d.plot.show_known_regions = False

    def on_char_click(self):
        if self.cb_char.isChecked():
            self.p3d.plot.show_fluorescence_lines = True
        else:
            self.p3d.plot.show_fluorescence_lines = False


class MainPlot2DTestWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.p2d = MainPlot2D(parent=self)
        self.cb_p = QCheckBox('Show peaks')
        self.cb_t = QCheckBox('Show tracks')
        self.cb_hkl = QCheckBox('Show hkl')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.cb_p, 1, 1, 1, 1)
        layout.addWidget(self.cb_t, 1, 2, 1, 1)
        layout.addWidget(self.cb_hkl, 1, 3, 1, 1)
        layout.addWidget(self.p2d, 2, 1, 1, 3)

        self.cb_p.clicked.connect(self.on_p_click)
        self.cb_t.clicked.connect(self.on_t_click)
        self.cb_hkl.clicked.connect(self.on_hkl_click)

        self.cb_p.setChecked(True)
        self.cb_t.setChecked(True)

        self.on_p_click()
        self.on_t_click()

    def on_p_click(self):
        if self.cb_p.isChecked():
            self.p2d.show_pt_points = True
        else:
            self.p2d.show_pt_points = False

    def on_t_click(self):
        if self.cb_t.isChecked():
            self.p2d.show_pt_tracks = True
        else:
            self.p2d.show_pt_tracks = False

    def on_hkl_click(self):
        if self.cb_hkl.isChecked():
            self.p2d.show_known_regions = True
        else:
            self.p2d.show_known_regions = False


class MainPlotAvgTestWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.p2d = MainPlotAvg(parent=self)
        self.cb_p = QCheckBox('Show peaks')
        self.cb_t = QCheckBox('Show tracks')
        self.cb_hkl = QCheckBox('Show hkl')
        self.cb_char = QCheckBox('Show fluorescence (In, W, Pb)')
        self.plotType_lbl = QLabel('Plot type', parent=self)
        self.plotType_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.combo_plotType = QComboBox()
        self.combo_plotType.setFixedWidth(100)
        self.plotType = np.array(['mean', 'median', 'sum', 'min', 'max'])
        self.combo_plotType.addItems(self.plotType)
        self.plotType_lbl.setBuddy(self.combo_plotType)
        self.toggle_log = QPushButton('Log Y')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.cb_p, 1, 1, 1, 1)
        layout.addWidget(self.cb_t, 1, 2, 1, 1)
        layout.addWidget(self.cb_hkl, 1, 3, 1, 1)
        layout.addWidget(self.cb_char, 1, 4, 1, 1)
        layout.addWidget(self.plotType_lbl, 1, 5, 1, 1)
        layout.addWidget(self.combo_plotType, 1, 6, 1, 1)
        layout.addWidget(self.toggle_log, 1, 7, 1, 1)
        layout.addWidget(self.p2d, 2, 1, 1, 7)

        self.cb_p.clicked.connect(self.on_p_click)
        self.cb_t.clicked.connect(self.on_t_click)
        self.cb_hkl.clicked.connect(self.on_hkl_click)
        self.cb_char.clicked.connect(self.on_char_click)
        self.combo_plotType.currentIndexChanged.connect(self.on_combo_plotType_currentIndexChanged)
        self.toggle_log.clicked.connect(self.on_toggle_log)

        self.cb_p.setChecked(True)
        self.cb_t.setChecked(True)

        self.on_p_click()
        self.on_t_click()

    def on_p_click(self):
        if self.cb_p.isChecked():
            self.p2d.show_pt_points = True
        else:
            self.p2d.show_pt_points = False

    def on_t_click(self):
        if self.cb_t.isChecked():
            self.p2d.show_pt_tracks = True
        else:
            self.p2d.show_pt_tracks = False

    def on_hkl_click(self):
        if self.cb_hkl.isChecked():
            self.p2d.show_known_regions = True
        else:
            self.p2d.show_known_regions = False

    def on_char_click(self):
        if self.cb_char.isChecked():
            self.p2d.show_fluorescence_lines = True

        else:
            self.p2d.show_fluorescence_lines = False

    def on_combo_plotType_currentIndexChanged(self, index):
        # self.logger.debug('on_combo_plotType_currentIndexChanged: ' + self.plotType[index])
        self.p2d.plot_type = self.plotType[index]

    def on_toggle_log(self):
        if self.toggle_log.text() == 'Log Y':
            self.toggle_log.setText('Lin Y')
            self.p2d.logy = True
        elif self.toggle_log.text() == 'Lin Y':
            self.toggle_log.setText('Log Y')
            self.p2d.logy = False
