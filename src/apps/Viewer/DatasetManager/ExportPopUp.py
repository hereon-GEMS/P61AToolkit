from PyQt5.QtWidgets import QDialog, QAbstractItemView, QGridLayout, QPushButton, QLabel, QComboBox
import copy
import numpy as np
import logging

from P61App import P61App
from .DatasetSelector import DatasetSelector


class ExportPopUp(QDialog):
    """"""
    def __init__(self, parent=None):
        QDialog.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.format_lbl = QLabel('Format:', parent=self)
        self.format_cb = QComboBox(parent=self)
        self.format_cb.addItem('CSV')
        self.label_to = QLabel('Spectra:', parent=self)
        self.list_to = DatasetSelector(parent=self)
        self.button_ok = QPushButton('Export', parent=self)

        self.setWindowTitle('Export Spectra')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.format_lbl, 1, 1, 1, 1)
        layout.addWidget(self.format_cb, 1, 2, 1, 1)
        layout.addWidget(self.label_to, 2, 1, 1, 1)
        layout.addWidget(self.list_to, 3, 1, 1, 2)
        layout.addWidget(self.button_ok, 4, 1, 1, 2)

        self.button_ok.clicked.connect(self.on_button_ok)

    def on_button_ok(self):
        self.q_app.export_spectra_csv(self.list_to.get_selected())
        self.close()


if __name__ == '__main__':
    import sys
    q_app = P61App(sys.argv)
    app = ExportPopUp()
    app.show()
    sys.exit(q_app.exec())