import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtCore import Qt
from PyQt5.Qt import QVector3D
from PyQt5.QtWidgets import QWidget
from scipy.interpolate import griddata
import logging

from P61App import P61App

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')


class MetaDataPlot3D(gl.GLViewWidget):
    cam_default = {'pos': QVector3D(0.5, 0.5, 0.5), 'distance': 2.5, 'azimuth': -90, 'elevation': 20}
    axes_ticks = 7

    def __init__(self, parent=None):
        gl.GLViewWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.setCameraPosition(**self.cam_default)

        self.grid_xy = None
        self.grid_yz = None
        self.grid_xz = None
        self.text_objs = []

        self._scatter = False
        self.logz = False

        self._init_axes()

    def _init_axes(self):
        self.grid_xy = gl.GLGridItem(size=QVector3D(20., 20., 1.))
        self.grid_yz = gl.GLGridItem()
        self.grid_xz = gl.GLGridItem(size=QVector3D(20., 20., 1.))

        self.grid_xy.scale(.05, .05, 1)
        self.grid_xy.translate(.5, .5, 0)
        self.grid_xy.setDepthValue(10)

        self.grid_yz.scale(.05, .05, 1)
        self.grid_yz.rotate(90, 0, 1, 0)
        self.grid_yz.translate(0., 0.5, 0.5)
        self.grid_yz.setDepthValue(10)

        self.grid_xz.scale(.05, .05, 1)
        self.grid_xz.rotate(90, 1, 0, 0)
        self.grid_xz.translate(.5, 1.0, 0.5)
        self.grid_xz.setDepthValue(10)

        self.addItem(self.grid_xy)
        self.addItem(self.grid_yz)
        self.addItem(self.grid_xz)

    def set_variables(self, x_var, y_var, z_var):
        for item in self.items:
            item._setView(None)
        self.items = []
        self.text_objs = []
        self.update()

        self._init_axes()

        xx, _, _ = self.q_app.get_data_by_name(x_var)
        yy, _, _ = self.q_app.get_data_by_name(y_var)
        zz, _, _ = self.q_app.get_data_by_name(z_var)

        if xx.size != yy.size or xx.size != zz.size:
            return

        ids = np.isnan(xx) | np.isnan(yy) | np.isnan(zz)
        xx, yy, zz = xx[~ids], yy[~ids], zz[~ids]

        if xx.size == 0:
            return

        for ii in np.linspace(0, 1, self.axes_ticks):
            self.text_objs.append([ii, 0, -0.05, str(ii * (np.max(xx) - np.min(xx)) + np.min(xx))])
            self.text_objs.append([1, ii, -0.05, str(ii * (np.max(yy) - np.min(yy)) + np.min(yy))])
            z_str = str(ii * (np.max(zz) - np.min(zz)) + np.min(zz))
            self.text_objs.append([-len(z_str) / 75, 0, ii, z_str])

        if np.max(xx) != np.min(xx):
            xx = (xx - np.min(xx)) / (np.max(xx) - np.min(xx))
        else:
            xx = np.array([0.5] * xx.size)
        if np.max(yy) != np.min(yy):
            yy = (yy - np.min(yy)) / (np.max(yy) - np.min(yy))
        else:
            yy = np.array([0.5] * yy.size)
        if np.max(zz) != np.min(zz):
            zz = (zz - np.min(zz)) / (np.max(zz) - np.min(zz))
        else:
            zz = np.array([0.5] * zz.size)

        pos = np.vstack([xx, yy, zz]).transpose()
        if self._scatter:
            self.addItem(gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 1), size=3))
        else:
            grid_xx = np.linspace(0, 1, 1000)
            grid_yy = np.linspace(0, 1, 1000)
            grid_xy = (
                np.array([grid_xx] * grid_yy.shape[0]), np.array([grid_yy] * grid_xx.shape[0]).T
            )
            grid_zz = griddata(pos[:, :2], pos[:, 2], grid_xy, method='nearest')
            grid_zz = grid_zz.reshape(grid_yy.shape[0], grid_xx.shape[0]).T

            self.addItem(
                gl.GLSurfacePlotItem(x=grid_xx, y=grid_yy, z=grid_zz,
                                     colors=self.q_app.apply_cmap(grid_zz, 'turbo', not self.logz),
                                     shader=None, computeNormals=False)
            )
        self.update()

    def paintGL(self, *args, **kwds):
        gl.GLViewWidget.paintGL(self, *args, **kwds)

        self.qglClearColor(Qt.white)
        for to in self.text_objs:
            self.renderText(*to)
