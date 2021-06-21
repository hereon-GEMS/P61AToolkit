"""
src/P61ViewerMain.py
====================
.. _QApplication: https://doc.qt.io/qtforpython/PySide2/QtWidgets/QApplication.html
.. _QMainWindow: https://doc.qt.io/qtforpython/PySide2/QtWidgets/QMainWindow.html

This python file serves as the executable script for the application.

Launches the :code:`P61App` (QApplication_ child class) and a :code:`P61Viewer` (QMainWindow_ child class) instances.
"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget, QTabWidget, QSystemTrayIcon, QMenu, QAction, QFileDialog
from PyQt5.QtGui import QIcon
import sys
from PlotWidgets import MainPlot2DTestWidget, MainPlot3DTestWidget, MainPlotAvgTestWidget
from DatasetManager import DatasetManager
from FitWidgets import GeneralFitWidget
from PeakTrackerWidgets import AutoFindWidget
from PeakTrackerWidgets import PeakTrackList
from PhaseAssignmentWidgets import PhaseConstructor

from P61App import P61App

import logging


class P61Viewer(QMainWindow):
    """
    Main window class for the application. Collects all widgets in the same layout and instantiates them.

    List of widgets:

    - :code:`EditableListWidget` List on the right of the 'View' tab. Allows to add, remove, activate (show on the
      plot and use for fit) and deactivate (stop showing on the plot and using for fit) datasets. All operations can be
      done in groups using multiple selection;
    - :code:`MainPlotWidget` shows all active datasets from the :code:`EditableListWidget`;
    - :code:`FitWidget` shows the model builder, fit parameters, list of datasets to fit and controls;
    - :code:`FitPlotWidget`: plots the fitted data together with the model function and its parts and a difference
      plot;
    """
    def __init__(self, parent=None):
        """
        Initiates all widgets and defines the main window layout.
        :param parent:
        """
        QMainWindow.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        # initiate self
        self.resize(1200, 800)
        self.setWindowTitle(P61App.name + ' ' + P61App.version)

        # initiate widgets
        self.cw = QTabWidget(parent=self)
        self.setCentralWidget(self.cw)
        self.tab1 = QWidget()

        # 1st tab
        self.dsm_w = DatasetManager(parent=self.tab1)

        self.plot_tabs = QTabWidget(parent=self.tab1)
        self.plot_2d = MainPlotAvgTestWidget(parent=self.plot_tabs)
        self.plot_3d = MainPlot3DTestWidget(parent=self.plot_tabs)
        self.plot_tabs.addTab(self.plot_2d, '2D')
        self.plot_tabs.addTab(self.plot_3d, '3D')

        # 2nd tab
        self.peak_af = AutoFindWidget(parent=self.tab1)
        self.peak_tl = PeakTrackList(parent=self.tab1)
        self.phase_ed = PhaseConstructor(parent=self.tab1)

        # menu
        mb = self.menuBar()
        fileMenu = QMenu("&File", self)
        helpMenu = QMenu("&Help", self)
        self._act_open = QAction('Open', self)
        self._act_save = QAction('Save', self)
        self._act_reload = QAction('Reload', self)
        self._act_save_as = QAction('Save as', self)
        self._act_export = QAction('Export spectra', self)
        self._act_tutorial = QAction('Tutorial', self)
        fileMenu.addActions([self._act_open, self._act_reload, self._act_save, self._act_save_as, self._act_export])
        helpMenu.addActions([self._act_tutorial])
        mb.addMenu(fileMenu)
        mb.addMenu(helpMenu)

        tab1_layout = QGridLayout()
        tab1_layout.addWidget(self.peak_af, 1, 1, 1, 1)
        tab1_layout.addWidget(self.peak_tl, 2, 1, 1, 1)
        tab1_layout.addWidget(self.phase_ed, 3, 1, 1, 1)

        tab1_layout.addWidget(self.plot_tabs, 1, 2, 3, 1)
        tab1_layout.addWidget(self.dsm_w, 1, 3, 3, 1)

        tab1_layout.setColumnStretch(1, 1)
        tab1_layout.setColumnStretch(2, 3)
        tab1_layout.setColumnStretch(3, 1)

        self.tab1.setLayout(tab1_layout)
        self.cw.addTab(self.tab1, 'Import and view')

        # 2nd tab
        self.fit_w = GeneralFitWidget(parent=self)
        self.cw.addTab(self.fit_w, 'Peak fit')

        self.logger.debug('Initialization complete')

        self._act_save.triggered.connect(self.on_act_save)
        self._act_save_as.triggered.connect(self.on_act_save_as)
        self._act_reload.triggered.connect(self.on_act_reload)
        self._act_open.triggered.connect(self.on_act_open)

    def on_act_open(self):
        fd = QFileDialog()
        f_name, _ = fd.getOpenFileName(
            self,
            'Open project',
            r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs',
            'All Files (*);;JSON files (*.json)',
            options=QFileDialog.Options()
        )
        if f_name != '':
            self.q_app.load_proj_from(f_name=f_name)

    def on_act_save(self):
        if self.q_app.proj_f_name is None:
            self.on_act_save_as()
        else:
            self.q_app.save_proj_as(f_name=None)

    def on_act_save_as(self):
        fd = QFileDialog()
        f_name, _ = fd.getSaveFileName(
            self,
            'Save project as',
            r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs',
            'All Files (*);;JSON files (*.json)',
            options=QFileDialog.Options()
        )
        if f_name != '':
            self.q_app.save_proj_as(f_name=f_name)

    def on_act_reload(self):
        self.q_app.load_proj_from(f_name=None)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
                        handlers=[logging.FileHandler("debug.log", mode='w'),
                                  logging.StreamHandler()])

    logger = logging.getLogger(__name__)
    logger.info('Starting up...')

    q_app = P61App(sys.argv)

    trayIcon = QSystemTrayIcon(QIcon("../img/icon.png"), q_app)
    trayIcon.show()

    app = P61Viewer()
    app.show()
    sys.exit(q_app.exec_())
