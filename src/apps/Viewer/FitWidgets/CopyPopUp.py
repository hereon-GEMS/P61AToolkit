from PyQt5.QtWidgets import QDialog, QAbstractItemView, QGridLayout, QPushButton, QLabel
import copy
import numpy as np
import logging

from P61App import P61App
from DatasetManager import DatasetSelector, DatasetViewer


class CopyPopUp(QDialog):
    """"""
    def __init__(self, parent=None):
        QDialog.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.label_from = QLabel('From: ' + self.q_app.get_selected_screen_name())
        self.label_to = QLabel('To:')
        self.list_to = DatasetSelector(parent=self)
        self.button_ok = QPushButton('Copy')

        self.setWindowTitle('Copy background')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.label_from, 1, 1, 1, 1)
        layout.addWidget(self.label_to, 2, 1, 1, 1)
        layout.addWidget(self.list_to, 3, 1, 1, 1)
        layout.addWidget(self.button_ok, 4, 1, 1, 1)

        self.button_ok.clicked.connect(self.on_button_ok)

    def on_button_ok(self):
        if self.q_app.get_selected_idx() == -1:
            pass
        else:
            idx_to = self.list_to.get_selected()

            bckg_list = self.q_app.get_bckg_data_list(self.q_app.get_selected_idx())
            for idx in idx_to:
                self.q_app.set_bckg_data_list(idx, copy.deepcopy(bckg_list), emit=False)
            self.q_app.bckgListChanged.emit(idx_to)
        self.close()


if __name__ == '__main__':
    import sys
    q_app = P61App(sys.argv)
    app = CopyPopUp()
    app.show()
    sys.exit(q_app.exec())