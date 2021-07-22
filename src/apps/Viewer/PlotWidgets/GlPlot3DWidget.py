from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QCheckBox, QPushButton, QDoubleSpinBox
from PyQt5.Qt import QVector3D
from PyQt5 import QtCore
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from collections.abc import Sequence
import logging

from P61App import P61App

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')


class GlPlot3DWidget(QWidget):
    read_only_style = 'QDoubleSpinBox {background-color: rgb(70, 70, 70); color: rgb(200, 200, 200)}'
    regular_style = 'QDoubleSpinBox {background-color: rgb(255, 255, 255);}'

    def __init__(self, plot, parent=None):

        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.plot = plot
        self.explanation_label = QLabel('[W] [A] [S] [D] move the plot in XY plane, [R] [F] move it along Z axis. '
                                        'Arrow keys or mouse click & drag rotate the camera. '
                                        '[Z] and [X] zoom the camera in and out. ')
        self.explanation_label.setMaximumHeight(20)
        self.zscale_label = QLabel('Intensity scale')
        # self.imax_edit = FloatEdit(init_val=self.plot.imax_default)
        self.imax_edit = QDoubleSpinBox(parent=self, minimum=0., maximum=1e8, singleStep=1e3, decimals=0, suffix=' cts')
        self.imax_edit.setValue(self.plot.imax_default)
        self.erange_label = QLabel('Energy range')
        # self.emin_edit = FloatEdit(init_val=self.plot.emin_default)
        # self.emax_edit = FloatEdit(init_val=self.plot.emax_default)
        self.emin_edit = QDoubleSpinBox(parent=self, minimum=0., maximum=200, singleStep=1, decimals=0, suffix=' keV')
        self.emin_edit.setValue(self.plot.emin_default)
        self.emax_edit = QDoubleSpinBox(parent=self, minimum=0., maximum=200, singleStep=1, decimals=0, suffix=' keV')
        self.emax_edit.setValue(self.plot.emax_default)
        self.autoscale_cb = QCheckBox(text='Autoscale')
        self.autoscale_cb.setChecked(True)
        self.emin_edit.setReadOnly(True)
        self.emax_edit.setReadOnly(True)
        self.imax_edit.setReadOnly(True)
        self.emin_edit.setStyleSheet(self.read_only_style)
        self.emax_edit.setStyleSheet(self.read_only_style)
        self.imax_edit.setStyleSheet(self.read_only_style)
        self._update_scale()
        self.view_to_default = QPushButton(u'👀')
        self.toggle_log = QPushButton('Log Z')

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.explanation_label, 1, 1, 1, 8)
        layout.addWidget(self.plot, 2, 1, 1, 8)
        layout.addWidget(self.view_to_default, 3, 1, 1, 1)
        layout.addWidget(self.toggle_log, 3, 2, 1, 1)
        layout.addWidget(self.autoscale_cb, 3, 3, 1, 1)
        layout.addWidget(self.zscale_label, 3, 4, 1, 1)
        layout.addWidget(self.imax_edit, 3, 5, 1, 1)
        layout.addWidget(self.erange_label, 3, 6, 1, 1)
        layout.addWidget(self.emin_edit, 3, 7, 1, 1)
        layout.addWidget(self.emax_edit, 3, 8, 1, 1)
        layout.setRowStretch(1, 1)
        layout.setRowStretch(2, 5)
        layout.setRowStretch(3, 1)

        self.imax_edit.editingFinished.connect(self._update_scale)
        self.emin_edit.editingFinished.connect(self._update_scale)
        self.emax_edit.editingFinished.connect(self._update_scale)
        self.autoscale_cb.stateChanged.connect(self._on_autoscale_sc)
        self.view_to_default.clicked.connect(self.set_view_to_default)
        self.toggle_log.clicked.connect(self.on_toggle_log)

    def on_toggle_log(self):
        if self.toggle_log.text() == 'Log Z':
            self.toggle_log.setText('Lin Z')
            self.plot.logz = True
        elif self.toggle_log.text() == 'Lin Z':
            self.toggle_log.setText('Log Z')
            self.plot.logz = False
        self.plot.upd_and_redraw()

    def set_view_to_default(self):
        self.plot.translate_scene(-self.plot.lines_origin[0], -self.plot.lines_origin[1], -self.plot.lines_origin[2])
        self.plot.setCameraPosition(**self.plot.cam_default)

    def autoscale(self):
        """
        Function to be overridden in subclasses to change default autoscaling behaviour,
        which is scale to default values
        :return:
        """
        self._scale_to()

    def _on_autoscale_sc(self, state):
        for edit in (self.emin_edit, self.emax_edit, self.imax_edit):
            edit.setReadOnly(bool(state))
            if state:
                edit.setStyleSheet(self.read_only_style)
            else:
                edit.setStyleSheet(self.regular_style)
        if state:
            self.autoscale()

    def _update_scale(self, *args, **kwargs):
        upd = False

        if self.plot.emin != self.emin_edit.value():
            self.plot.emin = self.emin_edit.value()
            upd = True

        if self.plot.emax != self.emax_edit.value():
            self.plot.emax = self.emax_edit.value()
            upd = True

        if self.plot.imax != self.imax_edit.value():
            self.plot.imax = self.imax_edit.value()
            upd = True

        if upd:
            self.plot.upd_and_redraw()

    def _scale_to(self, e_min=None, e_max=None, z_max=None):
        if e_min is not None:
            self.emin_edit.setValue(e_min)
        else:
            self.emin_edit.setValue(self.plot.emin_default)

        if e_max is not None:
            self.emax_edit.setValue(e_max)
        else:
            self.emax_edit.setValue(self.plot.emax_default)

        if z_max is not None:
            self.imax_edit.setValue(z_max)
        else:
            self.imax_edit.setValue(self.plot.imax_default)


class GlPlot3D(gl.GLViewWidget):
    emin_default = 0
    emax_default = 200
    imax_default = 1E3  # default values for shown energy and intensity range (min intensity is always 0)
    x_ratio = 16. / 9.  # shows how much longer the x axis is on the plot compared to y and z
    cam_default = {'pos': QVector3D(0.5 * x_ratio, 0.5, 0.5), 'distance': 2.5, 'azimuth': -90, 'elevation': 20}

    def __init__(self, parent=None):
        gl.GLViewWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self.lines_origin = [0., 0., 0.]
        self.emin = self.emin_default
        self.emax = self.emax_default
        self.imax = self.imax_default
        self.logz = False
        self._metavars = []
        self.setCameraPosition(**self.cam_default)

        self.grid_xy = gl.GLGridItem(size=QVector3D(20. * self.x_ratio, 20., 1.))
        self.grid_yz = gl.GLGridItem()
        self.grid_xz = gl.GLGridItem(size=QVector3D(20. * self.x_ratio, 20., 1.))
        self.text_objs = []
        self.x_ticks = 11
        self.z_ticks = 7
        self._init_axes()

    @property
    def metavars(self):
        return self._metavars

    @metavars.setter
    def metavars(self, val):
        if not isinstance(val, (list, tuple)):
            raise ValueError('metavars parameter should be a list or tuple of strings')
        self._metavars = val

    def redraw_data(self, *args, **kwargs):
        """
        Function that generates lines and adds them to the plot.
        Base class behaviour is to do nothing.

        :return:
        """
        pass

    def _update_text_objs(self):
        for ii, ee in enumerate(np.linspace(self.emin, self.emax, self.x_ticks)):
            self.text_objs[ii][3] = '%.01f' % ee

        if self.logz:
            for ii, zz in enumerate(np.logspace(0, np.log(self.imax), self.z_ticks, base=np.e)):
                self.text_objs[ii + self.x_ticks][3] = '%.0f' % zz
        else:
            for ii, zz in enumerate(np.linspace(0, self.imax, self.z_ticks)):
                self.text_objs[ii + self.x_ticks][3] = '%.0f' % zz

    def upd_and_redraw(self, *args, **kwargs):
        # clear the scene
        for item in self.items:
            item._setView(None)
        self.items = []
        self.update()

        # draw the axes
        self.addItem(self.grid_xy)
        self.addItem(self.grid_yz)
        self.addItem(self.grid_xz)
        self._update_text_objs()

        # delete old and create + draw new lines
        self.redraw_data(*args, **kwargs)

    def keyPressEvent(self, ev):
        dx, dy, dz, dr = 0., 0., 0., 0.
        if ev.key() == QtCore.Qt.Key_W:
            dy = 0.1
        elif ev.key() == QtCore.Qt.Key_S:
            dy = -0.1
        elif ev.key() == QtCore.Qt.Key_A:
            dx = -0.1
        elif ev.key() == QtCore.Qt.Key_D:
            dx = +0.1
        elif ev.key() == QtCore.Qt.Key_R:
            dz = 0.1
        elif ev.key() == QtCore.Qt.Key_F:
            dz = -0.1
        elif ev.key() == QtCore.Qt.Key_Z:
            dr = -0.1
        elif ev.key() == QtCore.Qt.Key_X:
            dr = 0.1

        self.setCameraPosition(distance=self.opts['distance'] + dr)
        self.translate_scene(dx, dy, dz)

        gl.GLViewWidget.keyPressEvent(self, ev)

    def translate_scene(self, dx, dy, dz):
        for item in self.items:
            item.translate(dx, dy, dz)

        for to in self.text_objs:
            to[0] += dx
            to[1] += dy
            to[2] += dz

        self.lines_origin[0] += dx
        self.lines_origin[1] += dy
        self.lines_origin[2] += dz

    def transform_xz(self, energy, intensity):
        """
        Turns energy and intensity vectors as stored in P61App.data to stacked XYZ values to plot on the 3D plot.
        Fills the Y values with 0s (relative to the plot axes origin), because after new lines are added / removed
        a restacking of Y axis is needed for every line anyway to put all lines at the equal distance from one another
        and restacking behaviour is subclass-specific.

        :param energy:
        :param intensity:
        :param index:
        :return:
        """
        xx = np.array(1E3 * energy, dtype=np.float)
        zz = np.array(intensity, dtype=np.float)
        yy = np.array([0.0] * zz.shape[0], dtype=np.float)

        yy = yy[(xx < self.emax * 1E3) & (xx > self.emin * 1E3)]
        zz = zz[(xx < self.emax * 1E3) & (xx > self.emin * 1E3)]
        xx = xx[(xx < self.emax * 1E3) & (xx > self.emin * 1E3)]

        xx = self.x_ratio * (xx - self.emin * 1E3) / (self.emax * 1E3 - self.emin * 1E3)
        if self.logz:
            xx, yy, zz = xx[zz >= 1], yy[zz >= 1], zz[zz >= 1]
            zz = np.log(zz) / np.log(self.imax)
        else:
            zz /= self.imax

        xx += self.lines_origin[0]
        yy += self.lines_origin[1]
        zz += self.lines_origin[2]

        return np.vstack([xx, yy, zz]).transpose()

    def transform_xyz(self, energy, y_pos, intensity):
        xx = np.array(1E3 * energy, dtype=np.float)
        yy = np.array(y_pos, dtype=np.float)
        zz = np.array(intensity, dtype=np.float)

        yy = yy[(xx < self.emax * 1E3) & (xx > self.emin * 1E3)]
        zz = zz[(xx < self.emax * 1E3) & (xx > self.emin * 1E3)]
        xx = xx[(xx < self.emax * 1E3) & (xx > self.emin * 1E3)]

        xx = self.x_ratio * (xx - self.emin * 1E3) / (self.emax * 1E3 - self.emin * 1E3)
        if self.logz:
            xx, yy, zz = xx[zz >= 1], yy[zz >= 1], zz[zz >= 1]
            zz = np.log(zz) / np.log(self.imax)
        else:
            zz /= self.imax

        xx += self.lines_origin[0]
        yy += self.lines_origin[1]
        zz += self.lines_origin[2]

        return np.vstack([xx, yy, zz]).transpose()

    def _init_axes(self):
        self.grid_xy.scale(.05, .05, 1)
        self.grid_xy.translate(.5 * self.x_ratio, .5, 0)
        self.grid_xy.setDepthValue(10)

        self.grid_yz.scale(.05, .05, 1)
        self.grid_yz.rotate(90, 0, 1, 0)
        self.grid_yz.translate(0., 0.5, 0.5)
        self.grid_yz.setDepthValue(10)

        self.grid_xz.scale(.05, .05, 1)
        self.grid_xz.rotate(90, 1, 0, 0)
        self.grid_xz.translate(.5 * self.x_ratio, 1.0, 0.5)
        self.grid_xz.setDepthValue(10)

        for xx in np.linspace(0., self.x_ratio, self.x_ticks):
            self.text_objs.append([xx, 0., -0.05, ''])

        for zz in np.linspace(0., 1., self.z_ticks):
            self.text_objs.append([0., -0.05, zz, ''])

        self.text_objs.append([.5 * self.x_ratio, 0., -0.1, 'keV'])

    def paintGL(self, *args, **kwds):
        gl.GLViewWidget.paintGL(self, *args, **kwds)

        self.qglClearColor(QtCore.Qt.white)
        for to in self.text_objs:
            self.renderText(*to)


if __name__ == '__main__':
    from DatasetManager import DatasetManager
    import sys
    q_app = P61App(sys.argv)
    app = GlPlot3DWidget()
    app2 = DatasetManager()
    app.show()
    app2.show()
    sys.exit(q_app.exec_())
