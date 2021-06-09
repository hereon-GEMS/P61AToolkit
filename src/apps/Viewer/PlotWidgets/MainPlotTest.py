from PyQt5.QtWidgets import QWidget, QGridLayout, QTabWidget, QCheckBox
import logging


from P61App import P61App
from PlotWidgets import MainPlot3D, MainPlot3DWidget, MainPlot2D


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

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.cb_surf, 1, 1, 1, 1)
        layout.addWidget(self.cb_col,  1, 2, 1, 1)
        layout.addWidget(self.cb_p,    1, 3, 1, 1)
        layout.addWidget(self.cb_t,    1, 4, 1, 1)
        layout.addWidget(self.cb_hkl,  1, 5, 1, 1)
        layout.addWidget(self.p3d,     2, 1, 1, 5)

        self.cb_surf.clicked.connect(self.on_surf_click)
        self.cb_col.clicked.connect(self.on_col_click)
        self.cb_p.clicked.connect(self.on_p_click)
        self.cb_t.clicked.connect(self.on_t_click)
        self.cb_hkl.clicked.connect(self.on_hkl_click)

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
