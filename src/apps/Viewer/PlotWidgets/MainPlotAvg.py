import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtCore import Qt
import logging

from P61App import P61App

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')


class MainPlotAvg(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        pg.GraphicsLayoutWidget.__init__(self, parent=parent, show=True)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self._show_pt_points = False
        self._show_pt_tracks = False
        self._show_known_regions = False
        self._show_fluorescence_lines = False
        self._plot_type = 'mean'
        self._log_y = False

        self._lines = []
        self._hkl_regions = []
        self._fit_scatters = []
        self._pt_scatters = []
        self._pt_tracks = []

        self._fluorescence_lines = []
        for val in self.q_app.fluorescence_lines.values():
            self._fluorescence_lines.append(pg.InfiniteLine(1e3 * val, pen='#7F0000', movable=False))

        self._line_ax = self.addPlot(title="Imported spectra")
        self._line_ax.setLabel('bottom', "Energy", units='eV')
        self._line_ax.setLabel('left', "Intensity", units='counts')
        self._line_ax.showGrid(x=True, y=True)

        self.q_app.dataRowsInserted.connect(self.on_data_rows_appended)
        self.q_app.dataRowsRemoved.connect(self.on_data_rows_removed)
        self.q_app.dataActiveChanged.connect(self.on_data_active_changed)
        self.q_app.dataSorted.connect(self.on_data_sorted)

    @property
    def show_pt_tracks(self):
        return self._show_pt_tracks

    @show_pt_tracks.setter
    def show_pt_tracks(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot2D.show_pt_tracks property should be bool')

        if val and not self._show_pt_tracks:
            self.q_app.peakTracksChanged.connect(self.on_peak_tracks_changed)
            self.on_peak_tracks_changed()
        elif not val and self._show_pt_tracks:
            self.q_app.peakTracksChanged.disconnect(self.on_peak_tracks_changed)
            for ii in reversed(range(len(self._pt_tracks))):
                self._line_ax.removeItem(self._pt_tracks[ii])
                self._pt_tracks.pop(ii)
        else:
            pass

        self._show_pt_tracks = val

    def on_peak_tracks_changed(self):
        self.logger.debug('on_peak_list_changed: Handling peakTracksChanged')

        for ii in reversed(range(len(self._pt_tracks))):
            self._line_ax.removeItem(self._pt_tracks[ii])
            self._pt_tracks.pop(ii)

        tracks = self.q_app.get_pd_tracks()
        ids = self.q_app.get_active_ids()

        for track in tracks:
            track_cys = [track[idx].cy for idx in track.ids if idx in ids]
            track_cxs = [track[idx].cx for idx in track.ids if idx in ids]

            if self._log_y:
                self._pt_tracks.append(
                    self._line_ax.plot(1e3 * np.array(track_cxs), np.log(np.array(track_cys)), pen='#ff0000'))
            else:
                self._pt_tracks.append(self._line_ax.plot(1e3 * np.array(track_cxs), np.array(track_cys), pen='#ff0000'))

    @property
    def show_pt_points(self):
        return self._show_pt_points

    @show_pt_points.setter
    def show_pt_points(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot2D.show_pt_points property should be bool')

        if val and not self._show_pt_points:
            self.q_app.peakListChanged.connect(self.on_peak_list_changed)
            self.on_peak_list_changed(None)
        elif not val and self._show_pt_points:
            self.q_app.peakListChanged.disconnect(self.on_peak_list_changed)
            for ii in reversed(range(len(self._pt_scatters))):
                self._line_ax.removeItem(self._pt_scatters[ii])
                self._pt_scatters.pop(ii)
        else:
            pass

        self._show_pt_points = val

    def on_peak_list_changed(self, ids):
        self.logger.debug('on_peak_list_changed: Handling peakListChanged')

        for ii in reversed(range(len(self._pt_scatters))):
            self._line_ax.removeItem(self._pt_scatters[ii])
            self._pt_scatters.pop(ii)

        for idx in self.q_app.get_active_ids():
            data = self.q_app.get_peak_data_list(idx)
            if data is None:
                continue

            peak_xs, peak_ys = [], []
            for peak in data:
                peak_xs.append(peak.cx)
                peak_ys.append(peak.cy)

            if self._log_y:
                self._pt_scatters.append(pg.ScatterPlotItem(1e3 * np.array(peak_xs), np.log(np.array(peak_ys)), pen='#ff0000',
                                                            brush='#ffffff'))
            else:
                self._pt_scatters.append(pg.ScatterPlotItem(1e3 * np.array(peak_xs), np.array(peak_ys), pen='#ff0000',
                                                            brush='#ffffff'))

            self._line_ax.addItem(self._pt_scatters[-1])

    @property
    def show_known_regions(self):
        return self._show_known_regions

    @show_known_regions.setter
    def show_known_regions(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot2D.show_known_regions property should be bool')

        if val and not self._show_known_regions:
            self.q_app.hklPeaksChanged.connect(self.on_hkl_changed)
            self.on_hkl_changed()
        elif not val and self._show_known_regions:
            self.q_app.hklPeaksChanged.disconnect(self.on_hkl_changed)
            for ii in reversed(range(len(self._hkl_regions))):
                self._line_ax.removeItem(self._hkl_regions[ii])
                self._hkl_regions.pop(ii)
        else:
            pass

        self._show_known_regions = val

    @property
    def show_fluorescence_lines(self):
        return self._show_fluorescence_lines

    @show_fluorescence_lines.setter
    def show_fluorescence_lines(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot2D.show_fluorescence_lines property should be bool')

        if val and not self._show_fluorescence_lines:
            for ii in range(len(self._fluorescence_lines)):
                self._line_ax.addItem(self._fluorescence_lines[ii])
        elif not val and self._show_fluorescence_lines:
            for ii in reversed(range(len(self._fluorescence_lines))):
                self._line_ax.removeItem(self._fluorescence_lines[ii])
        else:
            pass

        self._show_fluorescence_lines = val

    @property
    def plot_type(self):
        return self._plot_type

    @plot_type.setter
    def plot_type(self, val):
        if not isinstance(val, str):
            raise ValueError('MainPlot2D.plot_type property should be str')

        if val != self._plot_type:
            self._plot_type = val
            self.upd_and_redraw(data_changed=False)

    @property
    def logy(self):
        return self._log_y

    @logy.setter
    def logy(self, val):
        if not isinstance(val, bool):
            raise ValueError('MainPlot2D.log_y property should be bool')

        if val != self._log_y:
            self._log_y = val
            self.upd_and_redraw(data_changed=False)
            if self._show_pt_points:
                self.on_peak_list_changed(None)
            if self._show_pt_tracks:
                self.on_peak_tracks_changed()

    def on_hkl_changed(self):
        self.logger.debug('on_hkl_changed: Handling hklPeaksChanged')

        for ii in reversed(range(len(self._hkl_regions))):
            self._line_ax.removeItem(self._hkl_regions[ii])
            self._hkl_regions.pop(ii)

        for phase, color in zip(self.q_app.get_hkl_peaks(), self.q_app.wheels['def_no_red']):
            peaks = self.q_app.hkl_peaks[phase]
            for peak in peaks:
                self._hkl_regions.append(pg.LinearRegionItem([1e3 * (peak['e'] - peak['de']),
                                                              1e3 * (peak['e'] + peak['de'])],
                                                             brush=hex(color * 0x100 + 0x30).replace('0x', '#'),
                                                             pen=hex(color).replace('0x', '#'),
                                                             movable=False))
                self._line_ax.addItem(self._hkl_regions[-1])

    def line_init(self, ii):
        data = self.q_app.data.loc[ii, ['DataX', 'DataY', 'Color']]
        self._lines[ii] = self._line_ax.plot(1E3 * data['DataX'], data['DataY'],
                                             pen=str(hex(data['Color'])).replace('0x', '#'))

    def line_set_visibility(self, ii):
        if self.q_app.data.loc[ii, 'Active']:
            self._lines[ii].setPen(str(hex(self.q_app.data.loc[ii, 'Color'])).replace('0x', '#'))
        else:
            self._lines[ii].setPen(None)

    def plot_data(self):
        self.logger.debug('plot_data: Handling MainPlotAvg.plot_data - ' + self._plot_type)

        data = self.q_app.data.loc[self.q_app.get_active_ids(), ['DataX', 'DataY', 'Channel']]

        e_ticks = np.linspace(0, 200, 4096)

        def interp_ydata(row):
            row['ydata'] = np.interp(e_ticks, row['DataX'], row['DataY'])
            return row

        for ch, color in zip((0, 1), (0xff0000, 0x0000ff)):
            dd = data[data['Channel'] == ch]
            dd = dd.apply(interp_ydata, axis=1)
            if 'ydata' in dd.columns:
                i_values = np.stack(dd['ydata'].to_numpy())
                if self._plot_type == 'mean':
                    i_vals = np.mean(i_values, axis=0)
                elif self._plot_type == 'median':
                    i_vals = np.median(i_values, axis=0)
                elif self._plot_type == 'sum':
                    i_vals = np.sum(i_values, axis=0)
                elif self._plot_type == 'min':
                    i_vals = np.min(i_values, axis=0)
                elif self._plot_type == 'max':
                    i_vals = np.max(i_values, axis=0)
                if self._log_y:
                    self._lines.append(
                        self._line_ax.plot(1E3 * e_ticks, np.log(i_vals), pen=pg.mkPen(color=str(color).replace('0x', '#'))))
                else:
                    self._lines.append(
                        self._line_ax.plot(1E3 * e_ticks, i_vals, pen=pg.mkPen(color=str(color).replace('0x', '#'))))
                # i_mean = np.mean(i_values, axis=0)
                # # i_min = np.min(i_values, axis=0)
                # # i_max = np.max(i_values, axis=0)
                # # self._lines.append(self._line_ax.plot(1E3 * e_ticks, i_min, pen=pg.mkPen(color=str(color).replace('0x', '#'), style=Qt.DotLine)))
                # self._lines.append(self._line_ax.plot(1E3 * e_ticks, i_mean, pen=pg.mkPen(color=str(color).replace('0x', '#'))))
                # # self._lines.append(self._line_ax.plot(1E3 * e_ticks, i_max, pen=pg.mkPen(color=str(color).replace('0x', '#'), style=Qt.DotLine)))

    def on_data_rows_appended(self, pos, n_rows):
        self.logger.debug('on_data_rows_appended: Handling dataRowsInserted(%d, %d)' % (pos, n_rows))
        # self._lines = self._lines[:pos] + [None] * n_rows + self._lines[pos:]
        # for ii in range(pos, pos + n_rows):
        #     self.line_init(ii)

        self.upd_and_redraw()

    def on_data_rows_removed(self, rows):
        self.logger.debug('on_data_rows_removed: Handling dataRowsRemoved(%s)' % (str(rows), ))
        # for ii in sorted(rows, reverse=True):
        #     self._line_ax.removeItem(self._lines[ii])
        #     self._lines.pop(ii)

        self.upd_and_redraw()

    def on_data_active_changed(self, rows):
        self.logger.debug('on_data_active_changed: Handling dataActiveChanged(%s)' % (str(rows),))
        # for ii in rows:
        #     self.line_set_visibility(ii)

        self.upd_and_redraw()

    def on_data_sorted(self):
        self.logger.debug('on_data_sorted: Handling dataSorted')
        # for ii in reversed(range(len(self._lines))):
        #     self._line_ax.removeItem(self._lines[ii])
        #     self._lines.pop(ii)
        #
        # ids = self.q_app.get_all_ids()
        # self._lines = [None] * len(ids)
        #
        # for ii in ids:
        #     self.line_init(ii)
        #     self.line_set_visibility(ii)

        self.upd_and_redraw(redraw=False)

    def upd_and_redraw(self, redraw=True, data_changed=True):
        if redraw:
            for line in self._lines:
                self._line_ax.removeItem(line)
            del self._lines[:]

            self.plot_data()

        if data_changed and self.show_pt_points:
            self.on_peak_list_changed(None)
