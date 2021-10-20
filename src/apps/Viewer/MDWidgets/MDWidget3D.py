from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QFileDialog, QTabWidget
from PyQt5.QtCore import Qt
import logging

from P61App import P61App


class MetaDataWidget3D(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))
