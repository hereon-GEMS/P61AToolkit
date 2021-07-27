from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QDoubleSpinBox
from PyQt5.QtCore import pyqtSignal, Qt, QSize
import logging
import pandas as pd
from scipy.optimize import least_squares


from P61App import P61App
from utils import PhaseData
from py61a.cryst_utils import lattice_planes, cs_from_sg


class PhaseConstructor(QWidget):
    dataChanged = pyqtSignal()

    txt_back = '<'
    txt_forw = '>'
    txt_add = '+'

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        phases = self.q_app.get_hkl_phases()
        if phases is not None:
            self.phases = phases
        else:
            self.phases = [PhaseData()]
            self.q_app.set_hkl_phases(self.phases)
        self.ph_idx = 0
        self.peak_positions = None

        self.name_edt = QLineEdit(self.phases[self.ph_idx].name, parent=self)

        self.sg_lbl = QLabel('Space group', parent=self)
        self.cs_lbl = QLabel('(%s)' % cs_from_sg(self.phases[0].sgname), parent=self)
        self.a_lbl = QLabel('a', parent=self)
        self.b_lbl = QLabel('b', parent=self)
        self.c_lbl = QLabel('c', parent=self)
        self.alp_lbl = QLabel('α', parent=self)
        self.bet_lbl = QLabel('β', parent=self)
        self.gam_lbl = QLabel('γ', parent=self)
        self.tth_lbl = QLabel('2Θ', parent=self)
        self.emax_lbl = QLabel('Max E', parent=self)
        self.de_lbl = QLabel('ΔE', parent=self)

        self.sg_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.a_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.b_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.c_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.alp_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.bet_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.gam_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tth_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.emax_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.de_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.a_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=10., singleStep=0.1, decimals=3, suffix=' Å')
        self.b_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=10., singleStep=0.1, decimals=3, suffix=' Å')
        self.c_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=10., singleStep=0.1, decimals=3, suffix=' Å')
        self.alp_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=180., decimals=3, suffix='°')
        self.bet_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=180., decimals=3, suffix='°')
        self.gam_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=180., decimals=3, suffix='°')
        self.tth_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=20., singleStep=1., decimals=3, suffix='°')
        self.emax_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=200., decimals=0, suffix=' keV')
        self.de_edt = QDoubleSpinBox(parent=self, minimum=0., maximum=2., singleStep=0.01, decimals=2, suffix=' keV')

        self.a_edt.setValue(self.phases[self.ph_idx].a)
        self.b_edt.setValue(self.phases[self.ph_idx].b)
        self.c_edt.setValue(self.phases[self.ph_idx].c)
        self.alp_edt.setValue(self.phases[self.ph_idx].alp)
        self.bet_edt.setValue(self.phases[self.ph_idx].bet)
        self.gam_edt.setValue(self.phases[self.ph_idx].gam)
        self.tth_edt.setValue(self.phases[self.ph_idx].tth)
        self.emax_edt.setValue(self.phases[self.ph_idx].emax)
        self.de_edt.setValue(self.phases[self.ph_idx].de)
        self.sg_edt = QLineEdit(self.phases[self.ph_idx].sgname)

        self.btn_next = QPushButton(self.txt_add, parent=self)
        self.btn_prev = QPushButton(self.txt_back, parent=self)
        self.btn_prev.setDisabled(True)
        self.btn_del = QPushButton('Delete', parent=self)

        layout = QVBoxLayout()
        self.setLayout(layout)

        l1 = QHBoxLayout()
        l1.addWidget(self.btn_prev)
        l1.addWidget(self.name_edt)
        l1.addWidget(self.btn_next)
        layout.addLayout(l1)

        l2 = QHBoxLayout()
        l2.addWidget(self.sg_lbl, alignment=Qt.AlignRight, stretch=8)
        l2.addWidget(self.sg_edt, alignment=Qt.AlignRight, stretch=2)
        l2.addWidget(self.cs_lbl, alignment=Qt.AlignRight, stretch=2)
        l2.addWidget(self.tth_lbl, alignment=Qt.AlignLeft, stretch=1)
        l2.addWidget(self.tth_edt, alignment=Qt.AlignLeft, stretch=8)
        layout.addLayout(l2)

        l3 = QHBoxLayout()
        l3.addWidget(self.a_lbl)
        l3.addWidget(self.a_edt)
        l3.addWidget(self.b_lbl)
        l3.addWidget(self.b_edt)
        l3.addWidget(self.c_lbl)
        l3.addWidget(self.c_edt)
        layout.addLayout(l3)

        l4 = QHBoxLayout()
        l4.addWidget(self.alp_lbl)
        l4.addWidget(self.alp_edt)
        l4.addWidget(self.bet_lbl)
        l4.addWidget(self.bet_edt)
        l4.addWidget(self.gam_lbl)
        l4.addWidget(self.gam_edt)
        layout.addLayout(l4)

        l5 = QHBoxLayout()
        l5.addWidget(self.emax_lbl, alignment=Qt.AlignRight, stretch=5)
        l5.addWidget(self.emax_edt, alignment=Qt.AlignRight, stretch=3)
        l5.addWidget(self.de_lbl, alignment=Qt.AlignLeft, stretch=1)
        l5.addWidget(self.de_edt, alignment=Qt.AlignLeft, stretch=7)
        layout.addLayout(l5)

        l6 = QHBoxLayout()
        l6.addWidget(self.btn_del)
        layout.addLayout(l6)

        self.btn_prev.clicked.connect(self.on_btn_prev)
        self.btn_next.clicked.connect(self.on_btn_next)
        self.btn_del.clicked.connect(self.on_btn_del)
        self.name_edt.editingFinished.connect(self.on_name_ed_f)
        self.sg_edt.editingFinished.connect(self.on_sg_edt_changed)
        self.a_edt.editingFinished.connect(self.on_a_changed)
        self.b_edt.editingFinished.connect(self.on_b_changed)
        self.c_edt.editingFinished.connect(self.on_c_changed)
        self.alp_edt.editingFinished.connect(self.on_alp_changed)
        self.bet_edt.editingFinished.connect(self.on_bet_changed)
        self.gam_edt.editingFinished.connect(self.on_gam_changed)
        self.tth_edt.editingFinished.connect(self.on_tth_changed)
        self.emax_edt.editingFinished.connect(self.on_emax_changed)
        self.de_edt.editingFinished.connect(self.on_de_changed)
        self.q_app.hklPhasesChanged.connect(self.on_hklph_changed)

        self._upd_ui()
        self._upd_data()

    def on_hklph_changed(self):
        self.logger.debug('on_hklph_changed: handling hklPhasesChanged')
        self.phases = self.q_app.get_hkl_phases()
        if self.phases is None:
            self.phases = [PhaseData()]
            self.q_app.set_hkl_phases(self.phases)
        self._upd_ui()

    def on_a_changed(self):
        if self.phases[self.ph_idx].a != self.a_edt.value():
            self.phases[self.ph_idx].a = self.a_edt.value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_b_changed(self):
        if self.phases[self.ph_idx].b != self.b_edt.value():
            self.phases[self.ph_idx].b = self.b_edt.value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_c_changed(self):
        if self.phases[self.ph_idx].c != self.c_edt.value():
            self.phases[self.ph_idx].c = self.c_edt.value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_alp_changed(self):
        if self.phases[self.ph_idx].alp != self.alp_edt.value():
            self.phases[self.ph_idx].alp = self.alp_edt.value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_bet_changed(self):
        if self.phases[self.ph_idx].bet != self.bet_edt.value():
            self.phases[self.ph_idx].bet = self.bet_edt.value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_gam_changed(self):
        if self.phases[self.ph_idx].gam != self.gam_edt.value():
            self.phases[self.ph_idx].gam = self.gam_edt.value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_tth_changed(self):
        if self.phases[self.ph_idx].tth != self.tth_edt.value():
            self.phases[self.ph_idx].tth = self.tth_edt.value()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_emax_changed(self):
        if self.phases[self.ph_idx].emax != self.emax_edt.value():
            self.phases[self.ph_idx].emax = self.emax_edt.value()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_de_changed(self):
        if self.phases[self.ph_idx].de != self.de_edt.value():
            self.phases[self.ph_idx].de = self.de_edt.value()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_sg_edt_changed(self):
        txt = self.sg_edt.text().lower().replace(' ', '')

        if self.phases[self.ph_idx].sgname != txt:
            self.phases[self.ph_idx].sgname = txt
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_name_ed_f(self):
        if self.phases[self.ph_idx].name != self.name_edt.text():
            self.phases[self.ph_idx].name = self.name_edt.text()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_btn_prev(self):
        self.ph_idx -= 1
        self._upd_ui()

    def on_btn_next(self):
        self.ph_idx += 1
        if self.btn_next.text() == self.txt_add:
            self.phases.append(PhaseData())
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)
        self._upd_ui()

    def on_btn_del(self):
        self.phases = self.phases[:self.ph_idx] + self.phases[self.ph_idx + 1:]
        self.ph_idx = min(self.ph_idx, len(self.phases) - 1)
        self._upd_ui()
        self._upd_data()

    def enforce_cs(self, sg):
        cs = cs_from_sg(sg)

        if cs == 'triclinic':
            self.a_edt.setDisabled(False)
            self.b_edt.setDisabled(False)
            self.c_edt.setDisabled(False)
            self.alp_edt.setDisabled(False)
            self.bet_edt.setDisabled(False)
            self.gam_edt.setDisabled(False)
        elif cs == 'monoclinic':
            self.phases[self.ph_idx].alp = 90.
            self.phases[self.ph_idx].gam = 90.
            self.a_edt.setDisabled(False)
            self.b_edt.setDisabled(False)
            self.c_edt.setDisabled(False)
            self.alp_edt.setDisabled(True)
            self.bet_edt.setDisabled(False)
            self.gam_edt.setDisabled(True)
        elif cs == 'orthorombic':
            self.phases[self.ph_idx].alp = 90.
            self.phases[self.ph_idx].bet = 90.
            self.phases[self.ph_idx].gam = 90.
            self.a_edt.setDisabled(False)
            self.b_edt.setDisabled(False)
            self.c_edt.setDisabled(False)
            self.alp_edt.setDisabled(True)
            self.bet_edt.setDisabled(True)
            self.gam_edt.setDisabled(True)
        elif cs == 'tetragonal':
            self.phases[self.ph_idx].b = self.phases[self.ph_idx].a
            self.phases[self.ph_idx].alp = 90.
            self.phases[self.ph_idx].bet = 90.
            self.phases[self.ph_idx].gam = 90.
            self.a_edt.setDisabled(False)
            self.b_edt.setDisabled(True)
            self.c_edt.setDisabled(False)
            self.alp_edt.setDisabled(True)
            self.bet_edt.setDisabled(True)
            self.gam_edt.setDisabled(True)
        elif cs in ('trigonal', 'hexagonal'):
            self.phases[self.ph_idx].b = self.phases[self.ph_idx].a
            self.phases[self.ph_idx].alp = 90.
            self.phases[self.ph_idx].bet = 90.
            self.phases[self.ph_idx].gam = 120.
            self.a_edt.setDisabled(False)
            self.b_edt.setDisabled(True)
            self.c_edt.setDisabled(False)
            self.alp_edt.setDisabled(True)
            self.bet_edt.setDisabled(True)
            self.gam_edt.setDisabled(True)
        elif cs == 'cubic':
            self.phases[self.ph_idx].b = self.phases[self.ph_idx].a
            self.phases[self.ph_idx].c = self.phases[self.ph_idx].a
            self.phases[self.ph_idx].alp = 90.
            self.phases[self.ph_idx].bet = 90.
            self.phases[self.ph_idx].gam = 90.
            self.a_edt.setDisabled(False)
            self.b_edt.setDisabled(True)
            self.c_edt.setDisabled(True)
            self.alp_edt.setDisabled(True)
            self.bet_edt.setDisabled(True)
            self.gam_edt.setDisabled(True)

    def _upd_ui(self):
        if self.ph_idx >= len(self.phases):
            self.ph_idx = 0

        if self.ph_idx == 0:
            self.btn_prev.setDisabled(True)
        else:
            self.btn_prev.setDisabled(False)

        if self.ph_idx == len(self.phases) - 1:
            self.btn_next.setText(self.txt_add)
        else:
            self.btn_next.setText(self.txt_forw)

        if len(self.phases) <= 1:
            self.btn_del.setDisabled(True)
        else:
            self.btn_del.setDisabled(False)

        self.name_edt.setText(self.phases[self.ph_idx].name)
        self.name_edt.setStyleSheet("QLineEdit{border : 2px solid; border-color : %s;}" %
                                    hex(self.q_app.wheels['def_no_red'][self.ph_idx % len(self.q_app.wheels['def_no_red'])]).replace('0x', '#'))

        self.sg_edt.setText(self.phases[self.ph_idx].sgname)
        self.cs_lbl.setText('(%s)' % cs_from_sg(self.phases[self.ph_idx].sgname))
        self.a_edt.setValue(self.phases[self.ph_idx].a)
        self.b_edt.setValue(self.phases[self.ph_idx].b)
        self.c_edt.setValue(self.phases[self.ph_idx].c)
        self.alp_edt.setValue(self.phases[self.ph_idx].alp)
        self.bet_edt.setValue(self.phases[self.ph_idx].bet)
        self.gam_edt.setValue(self.phases[self.ph_idx].gam)
        self.tth_edt.setValue(self.phases[self.ph_idx].tth)
        self.emax_edt.setValue(self.phases[self.ph_idx].emax)
        self.de_edt.setValue(self.phases[self.ph_idx].de)

    def _upd_data(self):
        self.enforce_cs(self.phases[self.ph_idx].sgname)

        self.q_app.hkl_peaks = {
            phase.name: list(map(lambda x: dict(x, **{'de': phase.de}),
                                 lattice_planes(phase.sgname, phase.a, phase.b, phase.c, phase.alp, phase.bet, phase.gam, phase.tth, (1, phase.emax))))
            for phase in self.phases}
        self.q_app.hklPeaksChanged.emit()

    def refine_tth(self):
        peaks_data = pd.DataFrame()
        peaks_data = peaks_data.append(self.q_app.data.loc[self.q_app.data['Active'], ['ScreenName', 'PeakDataList']])
        peaks_data = peaks_data.apply(self.q_app.expand_peaks, axis=1)
        peaks_data = self.q_app.add_phase_data(peaks_data)
        peaks_data = peaks_data.drop(['ScreenName'], axis=1).mean(axis=0)

        tracks = self.q_app.get_pd_tracks()
        prefixes = ['pv%d' % ii for ii in range(len(tracks))]

        observed = dict()
        for prefix in prefixes:
            if '_'.join((prefix, 'h')) in peaks_data.index:
                observed['%d%d%d' % (peaks_data['_'.join((prefix, 'h'))],
                                     peaks_data['_'.join((prefix, 'k'))],
                                     peaks_data['_'.join((prefix, 'l'))])] = peaks_data['_'.join((prefix, 'center'))]

        phase = self.phases[self.ph_idx]

        def residuals(x, *args, **kwargs):
            calc = lattice_planes(phase.sgname, phase.a, phase.b, phase.c, phase.alp, phase.bet, phase.gam, x[0],
                           (1, phase.emax))
            calc = {'%d%d%d' % (peak['h'], peak['k'], peak['l']): peak['e'] for peak in calc}

            return sum([abs(observed[k] - calc[k]) for k in observed.keys() & calc.keys()])

        try:
            new_tth = least_squares(residuals, [phase.tth], bounds=(0., 15.)).x[0]
            self.phases[self.ph_idx].tth = new_tth
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

        except Exception as e:
            self.logger.error('Could not reach convergence: %s' % str(e))

