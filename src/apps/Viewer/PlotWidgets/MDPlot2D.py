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

        self.x_var = None
        self.y_var = None

        self._line_ax = self.addPlot(title="Metadata")
        self._line_ax.setLabel('bottom', "???")
        self._line_ax.setLabel('left', "???")
        self._line_ax.showGrid(x=True, y=True)

    def set_variables(self, x_var, y_var):
        self.x_var, self.y_var = x_var, y_var
        self._line_ax.clear()

        mds = self.q_app.data.loc[self.q_app.data['Active'], 'Motors'].to_list()

        if x_var in self.q_app.motors_all:
            xx = [md[x_var] if md is not None else None for md in mds]
            xx = np.array([np.nan if x is None else x for x in xx])
            xx_ids = self.q_app.get_active_ids()
        else:
            return

        yy_bounds, yy_ids = None, None
        if y_var in self.q_app.motors_all:
            yy = [md[y_var] if md is not None else None for md in mds]
            yy = np.array([np.nan if y is None else y for y in yy])
        elif y_var[:5] == 'Track':
            track_idx = int(y_var.split(':')[0].replace('Track ', ''))
            param = y_var.split(': ')[1]
            track = self.q_app.get_pd_tracks()[track_idx]
            yy_ids = np.array(track.ids)
            if param == 'center':
                yy = np.array(track.cxs)
                yy_bounds = np.array(track.cx_bounds)
            elif param == 'amplitude':
                yy = np.array(track.amplitudes)
                yy_bounds = np.array(track.amplitude_bounds)
            elif param == 'sigma':
                yy = np.array(track.sigmas)
                yy_bounds = np.array(track.sigma_bounds)
            else:
                return
        else:
            return

        if yy_ids is not None:
            xx = pd.Series(xx, index=xx_ids)
            yy = pd.Series(yy, index=yy_ids)

            if yy_bounds is not None:
                yy_mins = pd.Series(yy_bounds.T[0], index=yy_ids)
                yy_maxs = pd.Series(yy_bounds.T[1], index=yy_ids)
                data = pd.concat((xx, yy, yy_mins, yy_maxs), axis=1)
                xx, yy, yy_mins, yy_maxs = data[0].to_numpy(), data[1].to_numpy(), data[2].to_numpy(), data[3].to_numpy()
            else:
                data = pd.concat((xx, yy), axis=1)
                xx, yy = data[0].to_numpy(), data[1].to_numpy()

        ids = np.argsort(xx)
        xx, yy = xx[ids], yy[ids]
        if yy_bounds is not None:
            yy_mins, yy_maxs = yy_mins[ids], yy_maxs[ids]
            pen = pg.mkPen(color=(255, 0, 0), width=1, style=Qt.DashLine)
            self._line_ax.plot(xx, yy_mins, pen=pen)
            self._line_ax.plot(xx, yy_maxs, pen=pen)

        self._line_ax.setLabel('bottom', x_var)
        self._line_ax.setLabel('left', y_var)
        self._line_ax.plot(xx, yy, pen='#ff0000')
