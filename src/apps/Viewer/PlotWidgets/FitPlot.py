from PyQt5.Qt import Qt
import pyqtgraph as pg
import logging

from P61App import P61App
from utils import log_ex_time
from peak_fit_utils import models


class FitPlot(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        pg.GraphicsLayoutWidget.__init__(self, parent=parent, show=True)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        pg.setConfigOptions(antialias=True)
        pg.setConfigOption('background', 'w')

        self._line_ax = self.addPlot(title="Fit")
        self._line_ax.setLabel('bottom', "Energy", units='eV')
        self._line_ax.setLabel('left', "Intensity", units='counts')
        self._line_ax.showGrid(x=True, y=True)
        self.nextRow()
        self._diff_ax = self.addPlot(title="Difference plot")
        self._diff_ax.setLabel('bottom', "Energy", units='eV')
        self._diff_ax.setLabel('left', "Intensity", units='counts')
        self._diff_ax.showGrid(x=True, y=True)
        self._diff_ax.setXLink(self._line_ax)

        self._diff = None

        self.ci.layout.setRowStretchFactor(0, 4)
        self.ci.layout.setRowStretchFactor(1, 1)

        self.q_app.selectedIndexChanged.connect(self.on_selected_idx_ch)
        self.q_app.peakTracksChanged.connect(self.on_pt_changed)
        self.q_app.peakListChanged.connect(self.on_peaks_changed)
        self.q_app.dataSorted.connect(self.on_data_sorted)

    def on_data_sorted(self):
        self.logger.debug('on_data_sorted: Handling dataSorted')
        self.redraw_data()

    def on_selected_idx_ch(self, idx):
        self.logger.debug('on_selected_idx_ch: Handling selectedIndexChanged(%d)' % (idx,))
        self.redraw_data()

    def on_peaks_changed(self, idxs):
        self.logger.debug('on_peaks_changed: Handling peakListChanged(%s)' % (str(idxs),))
        if self.q_app.get_selected_idx() in idxs:
            self.redraw_data()

    def on_pt_changed(self):
        self.logger.debug('on_pt_changed: Handling peakTracksChanged')
        self.redraw_data()

    @log_ex_time
    def redraw_data(self):
        self.clear_axes()
        self._line_ax.addLegend()
        idx = self.q_app.get_selected_idx()
        if idx != -1:
            data = self.q_app.data.loc[idx, ['DataX', 'DataY', 'Color', 'PeakDataList']]

            self._line_ax.plot(1E3 * data['DataX'], data['DataY'],
                               pen=pg.mkPen(color='#000000', style=Qt.DotLine), name='Data')

            if data['PeakDataList'] is not None:
                xx = data['DataX']
                yy = data['DataY']
                # difference calculation
                # self._diff = yy - data['GeneralFitResult'].eval(data['GeneralFitResult'].params, x=xx)

                for peak in data['PeakDataList']:
                    yy_peak = models[peak.md_name](xx, **{name: peak.md_params[name].n for name in peak.md_params})
                    self._line_ax.plot(1E3 * xx, yy_peak,
                                       pen=pg.mkPen(color=str(hex(next(self.q_app.params['ColorWheel2']))).replace('0x', '#')),
                                       name='%.01f' % peak.md_params['center'].n)

                # cmps = data['GeneralFitResult'].eval_components(x=xx)
                # for cmp in cmps:
                #     if cmp not in self.q_app.params['LmFitModelColors'].keys():
                #         self.q_app.params['LmFitModelColors'][cmp] = next(self.q_app.params['ColorWheel2'])
                #     self._line_ax.plot(1E3 * xx, cmps[cmp], pen=pg.mkPen(
                #         color=str(hex(self.q_app.params['LmFitModelColors'][cmp])).replace('0x', '#')),
                #                        name=cmp)
                #
                #     if cmp + 'center' in data['GeneralFitResult'].params:
                #         xc = data['GeneralFitResult'].params[cmp + 'center'].value
                #         xb = data['GeneralFitResult'].params[cmp + 'sigma'].value * \
                #              data['GeneralFitResult'].params[cmp + 'base'].value
                #         xob = data['GeneralFitResult'].params[cmp + 'sigma'].value * \
                #              data['GeneralFitResult'].params[cmp + 'overlap_base'].value
                #
                #         self._line_ax.plot([1E3 * (xc - xob), 1E3 * (xc + xob)],
                #                            [1.1 * max(cmps[cmp]), 1.1 * max(cmps[cmp])],
                #                            pen=pg.mkPen(
                #                                width=4,
                #                                color=str(hex(self.q_app.params['LmFitModelColors'][cmp])).replace('0x',
                #                                                                                                   '#')),
                #                            name=None)
                #         self._line_ax.plot([1E3 * (xc - xb), 1E3 * (xc + xb)],
                #                            [1.1 * max(cmps[cmp]), 1.1 * max(cmps[cmp])],
                #                            pen=pg.mkPen(
                #                                color=str(hex(self.q_app.params['LmFitModelColors'][cmp])).replace('0x',
                #                                                                                                   '#')),
                #                            name=None)
                #         # text = pg.TextItem(cmp[:-1],
                #         #                    color=str(hex(self.q_app.params['LmFitModelColors'][cmp])).replace('0x',
                #         #                                                                                           '#'))
                #         # self._line_ax.addItem(text)
                #         # text.setPos(1E3 * xc, 1.1 * max(cmps[cmp]))
                #
                # self._line_ax.plot(1E3 * xx, data['GeneralFitResult'].eval(data['GeneralFitResult'].params, x=xx),
                #                    pen=pg.mkPen(color='#d62728'), name='Fit')
                # self._diff_ax.plot(1E3 * xx, self._diff, pen=pg.mkPen(color='#d62728'))

    def clear_axes(self):
        self._line_ax.clear()
        self._diff_ax.clear()

    def get_axes_xlim(self):
        return tuple(map(lambda x: x * 1E-3, self._line_ax.viewRange()[0]))

    def get_diff(self):
        return self._diff


if __name__ == '__main__':
    from DatasetManager import DatasetManager, DatasetViewer
    import sys

    q_app = P61App(sys.argv)
    app = FitPlot()
    app2 = DatasetManager()
    app3 = DatasetViewer()
    app.show()
    app2.show()
    app3.show()
    sys.exit(q_app.exec_())
