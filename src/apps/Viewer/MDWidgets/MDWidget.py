from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QFileDialog, QTabWidget
from PyQt5.QtCore import Qt
import logging

from P61App import P61App

from .MDWidget2D import MetaDataWidget2D
from .MDWidget3D import MetaDataWidget3D


class MetaDataWidget(QTabWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.addTab(MetaDataWidget2D(parent=self), '2D')
        self.addTab(MetaDataWidget3D(parent=self), '3D')
