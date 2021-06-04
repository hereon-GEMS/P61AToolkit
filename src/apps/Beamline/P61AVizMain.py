import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QLabel, QLineEdit, QDesktopWidget, QFrame
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np
from scipy.spatial.transform import Rotation as R


class QHLine(QFrame):
    def __init__(self, *args, **kwargs):
        super(QHLine, self).__init__(*args, **kwargs)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QVLine(QFrame):
    def __init__(self, *args, **kwargs):
        super(QVLine, self).__init__(*args, **kwargs)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


class P61AVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.glw = gl.GLViewWidget()
        self.glw.setCameraPosition(distance=10)
        self.scene = {
            'sample': {
                'g1': None,
                'g2': None,
                'g3': None,
                'g4': None,
                'g5': None,
                'g6': None,
            },
            'beam': {
                'inc': None,
                'inc_cont': None,
                'diff00': None,
                'diff01': None,
            },
        }

        self.plot = pg.PlotWidget()

        self.scene_controls = {
            'Ch 0 Tth': QLineEdit('7', parent=self),
            'Ch 1 Tth': QLineEdit('7', parent=self),
            'SD-dist': QLineEdit('500', parent=self),
            'Sample XR': QLineEdit('0', parent=self),
            'Sample YR': QLineEdit('0', parent=self),
            'Sample ZR': QLineEdit('0', parent=self),
        }
        self.scene_controls['Ch 0 Tth'].setValidator(QDoubleValidator(0, 20, 2))
        self.scene_controls['Ch 1 Tth'].setValidator(QDoubleValidator(0, 20, 2))
        self.scene_controls['SD-dist'].setValidator(QDoubleValidator(0, 1500, 2))
        self.scene_controls['Sample XR'].setValidator(QDoubleValidator(-10, 10, 2))
        self.scene_controls['Sample YR'].setValidator(QDoubleValidator(0, 180, 2))
        self.scene_controls['Sample ZR'].setValidator(QDoubleValidator(-180, 180, 2))

        self.scene_readouts = {
            'Ch O Z': QLabel('', parent=self),
            'Ch 1 X': QLabel('', parent=self),
            'Ch O Psi': QLabel('', parent=self),
            'Ch O Phi': QLabel('', parent=self),
            'Ch O Eta': QLabel('', parent=self),
            'Ch 1 Psi': QLabel('', parent=self),
            'Ch 1 Phi': QLabel('', parent=self),
            'Ch 1 Eta': QLabel('', parent=self),
        }

        lt = QGridLayout()
        cw = QWidget(parent=self)
        lt.addWidget(self.glw, 1, 1, 10, 1)
        #
        lt.addWidget(QLabel('Sample orientation:', parent=self), 1, 2, 1, 12)

        lt.addWidget(QLabel('XR', parent=self), 2, 2, 1, 2)
        lt.addWidget(QLabel('YR', parent=self), 2, 6, 1, 2)
        lt.addWidget(QLabel('ZR', parent=self), 2, 10, 1, 2)
        lt.addWidget(self.scene_controls['Sample XR'], 2, 4, 1, 2)
        lt.addWidget(self.scene_controls['Sample YR'], 2, 8, 1, 2)
        lt.addWidget(self.scene_controls['Sample ZR'], 2, 12, 1, 2)

        lt.addWidget(QHLine(parent=self), 3, 2, 1, 12)

        lt.addWidget(QLabel('SD distance', parent=self), 4, 2, 1, 3)
        lt.addWidget(self.scene_controls['SD-dist'], 4, 5, 1, 3)

        lt.addWidget(QLabel('Channel 0', parent=self), 5, 2, 1, 6)
        lt.addWidget(QLabel('Channel 1', parent=self), 5, 8, 1, 6)

        lt.addWidget(QLabel('2Θ', parent=self), 6, 2, 1, 3)
        lt.addWidget(QLabel('2Θ', parent=self), 6, 8, 1, 3)
        lt.addWidget(self.scene_controls['Ch 0 Tth'], 6, 5, 1, 3)
        lt.addWidget(self.scene_controls['Ch 1 Tth'], 6, 11, 1, 3)

        lt.addWidget(self.scene_readouts['Ch O Z'], 7, 2, 1, 6)
        lt.addWidget(self.scene_readouts['Ch 1 X'], 7, 8, 1, 6)

        lt.addWidget(self.scene_readouts['Ch O Phi'], 8, 2, 1, 6)
        lt.addWidget(self.scene_readouts['Ch 1 Phi'], 8, 8, 1, 6)

        lt.addWidget(self.scene_readouts['Ch O Psi'], 9, 2, 1, 6)
        lt.addWidget(self.scene_readouts['Ch 1 Psi'], 9, 8, 1, 6)

        lt.addWidget(self.scene_readouts['Ch O Eta'], 10, 2, 1, 6)
        lt.addWidget(self.scene_readouts['Ch 1 Eta'], 10, 8, 1, 6)
        #
        lt.addWidget(self.plot, 1, 14, 10, 1)

        lt.setColumnStretch(1, 24)
        lt.setColumnStretch(2, 1)
        lt.setColumnStretch(3, 1)
        lt.setColumnStretch(4, 1)
        lt.setColumnStretch(5, 1)
        lt.setColumnStretch(6, 1)
        lt.setColumnStretch(7, 1)
        lt.setColumnStretch(8, 1)
        lt.setColumnStretch(9, 1)
        lt.setColumnStretch(10, 1)
        lt.setColumnStretch(11, 1)
        lt.setColumnStretch(12, 1)
        lt.setColumnStretch(13, 1)
        lt.setColumnStretch(14, 24)

        lt.setRowStretch(1, 1)
        lt.setRowStretch(2, 1)
        lt.setRowStretch(3, 1)
        lt.setRowStretch(4, 1)
        lt.setRowStretch(5, 1)
        lt.setRowStretch(6, 1)
        lt.setRowStretch(7, 1)
        lt.setRowStretch(8, 1)
        lt.setRowStretch(9, 1)

        cw.setLayout(lt)

        self.setCentralWidget(cw)
        self.resize(QDesktopWidget().availableGeometry(self).size() * 0.7)
        self.setWindowTitle('P61A calculator')

        self.init_glw_scene()

        for ctrl in self.scene_controls:
            self.scene_controls[ctrl].editingFinished.connect(self.update_glw_scene)
            self.scene_controls[ctrl].returnPressed.connect(self.update_glw_scene)

    def init_glw_scene(self, pos=(0, 0, 0), rot=(0, 0, 0), size=(1, 2, 0.1), d0_ang=7, d1_ang=7, sd_dist=500):
        self.scene['sample']['g1'] = gl.GLGridItem()
        self.scene['sample']['g1'].scale(size[0] / 20., size[1] / 20, 1 / 20)
        self.scene['sample']['g1'].translate(0, 0, 0 + 0.5 * size[2])

        self.scene['sample']['g2'] = gl.GLGridItem()
        self.scene['sample']['g2'].scale(size[0] / 20., size[1] / 20., 1 / 20.)
        self.scene['sample']['g2'].translate(0, 0, 0 - 0.5 * size[2])

        self.scene['sample']['g3'] = gl.GLGridItem()
        self.scene['sample']['g3'].scale(size[2] / 20., size[1] / 20., 1 / 20.)
        self.scene['sample']['g3'].rotate(90, 0, 1, 0)
        self.scene['sample']['g3'].translate(0 - 0.5 * size[0], 0, 0)

        self.scene['sample']['g4'] = gl.GLGridItem()
        self.scene['sample']['g4'].scale(size[2] / 20., size[1] / 20., 1 / 20.)
        self.scene['sample']['g4'].rotate(90, 0, 1, 0)
        self.scene['sample']['g4'].translate(0 + 0.5 * size[0], 0, 0)

        self.scene['sample']['g5'] = gl.GLGridItem()
        self.scene['sample']['g5'].scale(size[0] / 20., size[2] / 20., 1 / 20.)
        self.scene['sample']['g5'].rotate(90, 1, 0, 0)
        self.scene['sample']['g5'].translate(0, 0 + 0.5 * size[1], 0)

        self.scene['sample']['g6'] = gl.GLGridItem()
        self.scene['sample']['g6'].scale(size[0] / 20., size[2] / 20., 1 / 20.)
        self.scene['sample']['g6'].rotate(90, 1, 0, 0)
        self.scene['sample']['g6'].translate(0, 0 - 0.5 * size[1], 0)

        sample_coord = {
            'x': np.array([1, 0, 0]).T,
            'y': np.array([0, 1, 0]).T,
            'z': np.array([0, 0, 1]).T
        }

        for s_c in sample_coord:
            r1 = R.from_rotvec(-np.pi * rot[0] * np.array([1, 0, 0]) / 180.)
            sample_coord[s_c] = np.matmul(sample_coord[s_c], r1.as_matrix())
            r2 = R.from_rotvec(-np.pi * rot[1] * np.array([0, 1, 0]) / 180.)
            sample_coord[s_c] = np.matmul(sample_coord[s_c], r2.as_matrix())
            r3 = R.from_rotvec(-np.pi * rot[2] * np.array([0, 0, 1]) / 180.)
            sample_coord[s_c] = np.matmul(sample_coord[s_c], r3.as_matrix())

        g_ch0 = np.array([0, 0, 1]).T
        g_ch0_rot = R.from_rotvec(np.pi * d0_ang * np.array([1, 0, 0]) / 180.)
        g_ch0 = np.matmul(g_ch0, g_ch0_rot.as_matrix())
        g_ch1 = np.array([-1, 0, 0]).T
        g_ch1_rot = R.from_rotvec(np.pi * d1_ang * np.array([0, 0, 1]) / 180.)
        g_ch1 = np.matmul(g_ch1, g_ch1_rot.as_matrix())

        d0_y = sd_dist * np.cos(d0_ang * np.pi / 180.)
        d0_z = sd_dist * np.sin(d0_ang * np.pi / 180.)
        d1_y = sd_dist * np.cos(d1_ang * np.pi / 180.)
        d1_x = sd_dist * np.sin(d1_ang * np.pi / 180.)

        self.scene_readouts['Ch O Z'].setText('Detector Z = %.02f' % d0_z)
        self.scene_readouts['Ch 1 X'].setText('Detector X = %.02f' % d1_x)

        self.scene_readouts['Ch O Phi'].setText('φ = %.02f')
        self.scene_readouts['Ch O Psi'].setText('ψ = %.02f' % (np.arccos(np.dot(sample_coord['z'], g_ch0)) * 180. / np.pi))
        self.scene_readouts['Ch O Eta'].setText('η = %.02f')

        self.scene_readouts['Ch 1 Phi'].setText('φ = %.02f')
        self.scene_readouts['Ch 1 Psi'].setText('ψ = %.02f' % (np.arccos(np.dot(sample_coord['z'], g_ch1)) * 180. / np.pi))
        self.scene_readouts['Ch 1 Eta'].setText('η = %.02f')

        for gg in self.scene['sample'].values():
            gg.translate(0, 0, -size[2] / 2)
            gg.rotate(rot[0], 1, 0, 0)
            gg.rotate(rot[1], 0, 1, 0)
            gg.rotate(rot[2], 0, 0, 1)
            gg.translate(*pos)
            self.glw.addItem(gg)

        self.scene['beam']['inc'] = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 100, 0]]))
        self.glw.addItem(self.scene['beam']['inc'])
        self.scene['beam']['inc_cont'] = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, -100, 0]]), width=0.1)
        self.glw.addItem(self.scene['beam']['inc_cont'])
        self.scene['beam']['diff00'] = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, -d0_y * 1e-1, d0_z * 1e-1]]))
        self.glw.addItem(self.scene['beam']['diff00'])
        self.scene['beam']['diff01'] = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [-d1_x * 1e-1, -d1_y * 1e-1, 0]]))
        self.glw.addItem(self.scene['beam']['diff01'])

        self.glw.addItem(gl.GLLinePlotItem(pos=np.array([[0, 0, 0], sample_coord['z']])))
        self.glw.addItem(gl.GLLinePlotItem(pos=np.array([[0, 0, 0], g_ch0])))
        self.glw.addItem(gl.GLLinePlotItem(pos=np.array([[0, 0, 0], g_ch1])))

    def update_glw_scene(self, *args, **kwargs):
        self.glw.clear()

        self.init_glw_scene(rot=(-float(self.scene_controls['Sample XR'].text()),
                                 -float(self.scene_controls['Sample YR'].text()),
                                 float(self.scene_controls['Sample ZR'].text())),
                            sd_dist=float(self.scene_controls['SD-dist'].text()),
                            d0_ang=float(self.scene_controls['Ch 0 Tth'].text()),
                            d1_ang=float(self.scene_controls['Ch 1 Tth'].text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = P61AVisualizer()
    mw.show()
    app.exec_()
