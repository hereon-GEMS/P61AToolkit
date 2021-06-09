import pyqtgraph as pg
from collections import defaultdict
from functools import reduce
import pyqtgraph.opengl as gl
import numpy as np
import pandas as pd
from scipy.interpolate import griddata

from P61App import P61App
from PlotWidgets.GlPlot3DWidget import GlPlot3D, GlPlot3DWidget
from utils import log_ex_time


pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')


class MainPlot3DWidget(GlPlot3DWidget):
    def __init__(self, plot, parent=None):
        GlPlot3DWidget.__init__(self, plot, parent=parent)
        self.q_app = P61App.instance()

        self.q_app.dataRowsInserted.connect(self.on_data_rows_appended)
        self.q_app.dataRowsRemoved.connect(self.on_data_rows_removed)
        self.q_app.dataSorted.connect(self.on_data_sorted)
        self.q_app.dataActiveChanged.connect(self.on_data_active_changed)
        self.q_app.peakListChanged.connect(self.on_peak_list_changed)
        self.q_app.peakTracksChanged.connect(self.on_peak_tracks_changed)
        self.q_app.hklPeaksChanged.connect(self.on_hkl_changed)
        self.q_app.genFitResChanged.connect(self.on_fit_changed)

    def autoscale(self):
        if len(self.q_app.get_active_ids()) > 0:
            emin = self.q_app.data.loc[self.q_app.get_active_ids(), 'DataX'].apply(np.min).min()
            emax = self.q_app.data.loc[self.q_app.get_active_ids(), 'DataX'].apply(np.max).max()
            imax = self.q_app.data.loc[self.q_app.get_active_ids(), 'DataY'].apply(np.max).max()
        else:
            emin, emax, imax = None, None, None
        self._scale_to(emin, emax, imax)

    def on_data_rows_appended(self, *args, **kwargs):
        self.logger.debug('on_data_rows_appended: Handling dataRowsInserted(%s, %s)' % (str(args), str(kwargs)))
        self.plot.upd_and_redraw()
        if self.autoscale_cb.isChecked():
            self.autoscale()

    def on_data_rows_removed(self, *args, **kwargs):
        self.logger.debug('on_data_rows_removed: Handling dataRowsRemoved(%s, %s)' % (str(args), str(kwargs)))
        self.plot.upd_and_redraw()
        if self.autoscale_cb.isChecked():
            self.autoscale()

    def on_data_sorted(self):
        self.logger.debug('on_data_sorted: Handling dataSorted')
        self.plot.upd_and_redraw()

    def on_data_active_changed(self, *args, **kwargs):
        self.logger.debug('on_data_active_changed: Handling dataActiveChanged(%s, %s)' % (str(args), str(kwargs)))
        self.plot.upd_and_redraw()
        if self.autoscale_cb.isChecked():
            self.autoscale()

    def on_peak_list_changed(self, *args, **kwargs):
        self.logger.debug('on_peak_list_changed: Handling peakListChanged(%s, %s)' % (str(args), str(kwargs)))
        self.plot.upd_and_redraw(pt_points=True)

    def on_peak_tracks_changed(self, *args, **kwargs):
        self.logger.debug('on_peak_tracks_changed: Handling peakTracksChanged(%s, %s)' % (str(args), str(kwargs)))
        self.plot.upd_and_redraw(pt_tracks=True)

    def on_hkl_changed(self, *args, **kwargs):
        self.logger.debug('on_hkl_changed: Handling hklPeaksChanged(%s, %s)' % (str(args), str(kwargs)))
        self.plot.upd_and_redraw(hkl=True)

    def on_fit_changed(self, *args, **kwargs):
        self.logger.debug('on_fit_changed: Handling genFitResChanged(%s, %s)' % (str(args), str(kwargs)))
        self.plot.upd_and_redraw(fit=True)


class MainPlot3D(GlPlot3D):
    def __init__(self, parent=None):
        GlPlot3D.__init__(self, parent=parent)
        self.q_app = P61App.instance()

        self._surface = False
        self._colored = False
        self._show_pt_points = False
        self._show_pt_tracks = False
        self._show_known_regions = False
        self._show_fit_centers = False

        self._surf_data = []
        self._lines = []
        self._peak_scatters = []
        self._peak_tracks = []
        self._fit_tracks = []
        self._hkl_lines = []

    @property
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot3D.surface property should be bool')
        self._surface = val
        self.upd_and_redraw(spectra=True)

    @property
    def colored(self):
        return self._colored

    @colored.setter
    def colored(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot3D.compact property should be bool')
        self._colored = val
        self.upd_and_redraw(spectra=True)

    @property
    def show_pt_points(self):
        return self._show_pt_points

    @show_pt_points.setter
    def show_pt_points(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot3D.show_pt_points property should be bool')
        self._show_pt_points = val
        self.upd_and_redraw(pt_points=True)

    @property
    def show_pt_tracks(self):
        return self._show_pt_tracks

    @show_pt_tracks.setter
    def show_pt_tracks(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot3D.show_pt_tracks property should be bool')
        self._show_pt_tracks = val
        self.upd_and_redraw(pt_tracks=True)

    @property
    def show_known_regions(self):
        return self._show_known_regions

    @show_known_regions.setter
    def show_known_regions(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot3D.show_known_regions property should be bool')
        self._show_known_regions = val
        self.upd_and_redraw(hkl=True)

    @property
    def show_fit_centers(self):
        return self._show_fit_centers

    @show_fit_centers.setter
    def show_fit_centers(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot3D.show_fit_centers property should be bool')
        self._show_fit_centers = val
        self.upd_and_redraw(fit=True)

    def redraw_spectra(self, ys, ymap):
        del self._lines[:]
        del self._surf_data[:]

        if ys.shape[0] == 0:
            return

        if self._surface:
            surf_xx, surf_yy, surf_zz = [], [], []

            for idx in ymap:
                data = self.q_app.data.loc[idx, ['DataX', 'DataY']]
                pos = self.transform_xz(data['DataX'], data['DataY'])
                surf_xx.append(pos[:, 0].copy())
                surf_zz.append(pos[:, 2].copy())
                surf_yy.append(np.array([ymap[idx]] * surf_zz[-1].shape[0]))
            surf_xx, surf_yy, surf_zz = np.concatenate(surf_xx), np.concatenate(surf_yy), np.concatenate(surf_zz)
            # surf_xx, surf_yy, surf_zz = np.array(surf_xx), np.array(surf_yy), np.array(surf_zz)
            # surf_xx, surf_yy, surf_zz = surf_xx.flatten(), surf_yy.flatten(), surf_zz.flatten()

            surf_data = np.array([surf_xx, surf_yy]).T
            grid_xx = np.linspace(np.min(surf_xx), np.max(surf_xx), 4096)
            grid_yy = ys.copy()
            grid_xy = (
                np.array([grid_xx] * grid_yy.shape[0]), np.array([grid_yy] * grid_xx.shape[0]).T
            )
            grid_zz = griddata(surf_data, surf_zz, grid_xy, method='nearest')
            grid_zz = grid_zz.reshape(grid_yy.shape[0], grid_xx.shape[0]).T

            if self._colored:
                colors = np.array(self.q_app.data.loc[self.q_app.get_active_ids(), 'Color']).reshape(-1, 1)
                colors = np.apply_along_axis(
                    lambda row: [row[0] // 0x10000, (row[0] // 0x100) % 0x100, row[0] % 0x100, 0x100],
                    1, colors) / 0x100

                self._surf_data.append(
                    gl.GLSurfacePlotItem(x=grid_xx, y=grid_yy, z=grid_zz,
                                         colors=np.array([colors] * grid_zz.shape[0]),
                                         shader=None, computeNormals=False))
            else:
                self._surf_data.append(
                    gl.GLSurfacePlotItem(x=grid_xx, y=grid_yy, z=grid_zz,
                                         colors=self.q_app.apply_cmap(grid_zz, 'turbo', not self.logz),
                                         shader=None, computeNormals=False))
        else:
            for idx in ymap:
                self._lines.append(self._init_line(idx))
                pos = self._lines[-1].pos
                pos[:, 1] = ymap[idx]
                self._lines[-1].setData(pos=pos, antialias=True)

    def redraw_pt(self, ymap):
        del self._peak_scatters[:]

        if self._show_pt_points:
            for idx in ymap:
                self._peak_scatters.append(self._init_peak_scatter(idx))
                if self._peak_scatters[-1] is not None:
                    pos = self._peak_scatters[-1].pos
                    pos[:, 1] = ymap[idx]
                    self._peak_scatters[-1].setData(pos=pos)

    def redraw_pt_tracks(self, ymap):
        del self._peak_tracks[:]

        if self._show_pt_tracks:
            tracks = self.q_app.get_pd_tracks()
            for track in tracks:
                tr_yy = np.array([ymap[idx] for idx in track.ids])
                tr_zz = np.array(track.cys)
                tr_xx = np.array(track.cxs)

                tr_xx, tr_yy, tr_zz = tr_xx[~np.isnan(tr_yy)], tr_yy[~np.isnan(tr_yy)], tr_zz[~np.isnan(tr_yy)]

                pos = self.transform_xyz(tr_xx, tr_yy, tr_zz)
                self._peak_tracks.append(
                    gl.GLLinePlotItem(pos=pos, color='#ffffff', width=2, antialias=True))

    def redraw_known_regions(self):
        del self._hkl_lines[:]

        if self._show_known_regions:
            for phase, color in zip(self.q_app.hkl_peaks, self.q_app.wheels['def_no_red']):
                peaks = self.q_app.hkl_peaks[phase]
                for peak in peaks:
                    xx = np.array([peak['e'] + peak['de'], peak['e'] + peak['de'], peak['e'] + peak['de'],
                                   peak['e'] - peak['de'], peak['e'] - peak['de'], peak['e'] - peak['de'],
                                   peak['e'] + peak['de']])
                    yy = np.array([0., 1., 1.,
                                   1., 1., 0.,
                                   0.])
                    zz = np.array([1., 1., self.imax,
                                   self.imax, 1., 1.,
                                   1.])
                    pos = self.transform_xyz(xx, yy, zz)
                    self._hkl_lines.append(
                        gl.GLLinePlotItem(pos=pos, color=hex(color).replace('0x', '#'), width=2, antialias=True))

    def redraw_fit_centers(self, ys):
        del self._fit_tracks[:]

    @log_ex_time()
    def redraw_data(self, *args, **kwargs):
        ids = self.q_app.get_active_ids()
        ys = np.linspace(0., 1., len(ids)) + self.lines_origin[1]
        ymap = defaultdict(lambda: np.NAN)
        for k, v in zip(ids, ys):
            ymap[k] = v

        if not kwargs:
            self.redraw_spectra(ys, ymap)
            self.redraw_pt(ymap)
            self.redraw_pt_tracks(ymap)
            self.redraw_known_regions()
            self.redraw_fit_centers(ys)
        else:
            if 'spectra' in kwargs:
                if kwargs['spectra']:
                    self.redraw_spectra(ys, ymap)
            if 'pt_points' in kwargs:
                if kwargs['pt_points']:
                    self.redraw_pt(ymap)
            if 'pt_tracks' in kwargs:
                if kwargs['pt_tracks']:
                    self.redraw_pt_tracks(ymap)
            if 'hkl' in kwargs:
                if kwargs['hkl']:
                    self.redraw_known_regions()
            if 'fit' in kwargs:
                if kwargs['fit']:
                    self.redraw_fit_centers(ys)

        for item in self._surf_data + self._lines + self._peak_scatters + \
                    self._peak_tracks + self._fit_tracks + self._hkl_lines:
            if item is not None:
                self.addItem(item)

    def _init_line(self, idx):
        data = self.q_app.data.loc[idx, ['DataX', 'DataY', 'Color', 'Active']]
        pos = self.transform_xz(data['DataX'], data['DataY'])
        if self._colored:
            result = gl.GLLinePlotItem(pos=pos,
                                       color=str(hex(data['Color'])).replace('0x', '#'),
                                       antialias=True)
        else:
            result = gl.GLLinePlotItem(pos=pos, color='#ffffff', antialias=True)
        result.setVisible(data['Active'])
        return result

    def _init_peak_scatter(self, idx):
        data = self.q_app.get_peak_data_list(idx)
        if data is None:
            return None

        peak_xs, peak_ys = [], []
        for peak in data:
            peak_xs.append(peak.cx)
            peak_ys.append(peak.cy)

        peak_xs = np.array(peak_xs)
        peak_ys = np.array(peak_ys)

        pos = self.transform_xz(peak_xs, peak_ys)
        result = gl.GLScatterPlotItem(pos=pos, color=(1, 1, 1, 1), size=3)
        return result