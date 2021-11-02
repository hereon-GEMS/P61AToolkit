import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtCore import Qt
import logging

from P61App import P61App

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')


class MetaDataPlot2D(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        pg.GraphicsLayoutWidget.__init__(self, parent=parent, show=True)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self._line_ax = self.addPlot(title="Metadata")
        self._line_ax.setLabel('bottom', "???")
        self._line_ax.setLabel('left', "???")
        self._line_ax.showGrid(x=True, y=True)

    def set_variables(self, x_var, y_var):
        self._line_ax.clear()

        xx, _, _ = self.q_app.get_data_by_name(x_var)
        yy, yy_mins, yy_maxs = self.q_app.get_data_by_name(y_var)

        if xx.size != yy.size:
            return

        ids = np.argsort(xx)
        xx, yy = xx[ids], yy[ids]

        if yy_mins is not None:
            yy_mins = yy_mins[ids]
            self._line_ax.plot(xx, yy_mins, pen=pg.mkPen(color=(255, 0, 0), width=1, style=Qt.DashLine))

        if yy_maxs is not None:
            yy_maxs = yy_maxs[ids]
            self._line_ax.plot(xx, yy_maxs, pen=pg.mkPen(color=(255, 0, 0), width=1, style=Qt.DashLine))

        self._line_ax.setLabel('bottom', x_var)
        self._line_ax.setLabel('left', y_var)
        self._line_ax.plot(xx, yy, pen='#ff0000', symbolBrush='#ff3f3f')
