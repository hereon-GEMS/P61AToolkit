from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QLineEdit, QComboBox
from PyQt5.QtCore import pyqtSignal
import logging


from P61App import P61App
from FitWidgets import FloatEdit
from cryst_utils import hkl_generator2


class PhaseData:
    _lat_supported = 'fcc', 'bcc', 'hcp'
    _name_idx = 1

    def __init__(self):
        self._name = 'Phase %02d' % self.__class__._name_idx
        self.__class__._name_idx += 1

        self._lat = 'bcc'

        self._a = 2.85  # AA
        self._b = 2.85  # AA
        self._c = 2.85  # AA

        self._tth = 12.0  # deg

        self._emax = 200.0  # keV
        self._de = 1.0  # keV

        self.enforce_lat_constraints = {lat: getattr(self, 'enf_' + lat) for lat in self._lat_supported}

    def __eq__(self, other):
        return all(getattr(self, attr) == getattr(other, attr) for attr in
                   ('name', 'lat', 'a', 'b', 'c', 'tth', 'emax', 'de'))

    def enf_fcc(self):
        """a == b == c"""
        self._b = self._a
        self._c = self._a

    def enf_bcc(self):
        """a == b == c"""
        self._b = self._a
        self._c = self._a

    def enf_hcp(self):
        """a == b"""
        self._b = self._a

    @classmethod
    def lat_supported(cls):
        return cls._lat_supported

    @property
    def free_abc(self):
        if self._lat == 'fcc':
            return [True, False, False]
        elif self._lat == 'bcc':
            return [True, False, False]
        elif self._lat == 'hcp':
            return [True, False, True]
        else:
            raise ValueError('Lattice type %s is not supported' % self._lat)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n_name):
        if not isinstance(n_name, str):
            raise ValueError('Param n_name should be str')
        self._name = n_name

    @property
    def lat(self):
        return self._lat

    @lat.setter
    def lat(self, n_lat):
        if not isinstance(n_lat, str):
            raise ValueError('Param n_lat should be str')

        if n_lat not in self._lat_supported:
            raise ValueError('Lattice type %s is not supported' % n_lat)

        self._lat = n_lat
        self.enforce_lat_constraints[n_lat]()

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, n_a):
        if n_a <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._a = n_a
        self.enforce_lat_constraints[self.lat]()

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, n_b):
        if n_b <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._b = n_b
        self.enforce_lat_constraints[self.lat]()

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, n_c):
        if n_c <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._c = n_c
        self.enforce_lat_constraints[self.lat]()

    @property
    def tth(self):
        return self._tth

    @tth.setter
    def tth(self, n_tth):
        if n_tth <= 0:
            raise ValueError('2Theta angle should be a positive number')
        self._tth = n_tth

    @property
    def emax(self):
        return self._emax

    @emax.setter
    def emax(self, n_emax):
        if n_emax <= 0:
            raise ValueError('Max energy should be a positive number')
        self._emax = n_emax

    @property
    def de(self):
        return self._de

    @de.setter
    def de(self, n_de):
        if n_de <= 0:
            raise ValueError('dE should be a positive number')
        self._de = n_de


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

        self.lat_lbl = QLabel('Lattice', parent=self)
        self.a_lbl = QLabel('a', parent=self)
        self.b_lbl = QLabel('b', parent=self)
        self.c_lbl = QLabel('c', parent=self)
        self.tth_lbl = QLabel('2Θ', parent=self)
        self.emax_lbl = QLabel('Max E', parent=self)
        self.de_lbl = QLabel('ΔE', parent=self)

        self.a_edt = FloatEdit(init_val=self.phases[self.ph_idx].a, inf_allowed=False, parent=self)
        self.b_edt = FloatEdit(init_val=self.phases[self.ph_idx].b, inf_allowed=False, parent=self)
        self.c_edt = FloatEdit(init_val=self.phases[self.ph_idx].c, inf_allowed=False, parent=self)
        self.tth_edt = FloatEdit(init_val=self.phases[self.ph_idx].tth, inf_allowed=False, parent=self)
        self.emax_edt = FloatEdit(init_val=self.phases[self.ph_idx].emax, inf_allowed=False, parent=self)
        self.de_edt = FloatEdit(init_val=self.phases[self.ph_idx].de, inf_allowed=False, parent=self)

        self.lat_cmb = QComboBox(parent=self)
        self.lat_cmb.addItems(PhaseData.lat_supported())
        self.lat_cmb.setCurrentText(self.phases[self.ph_idx].lat)

        self.btn_next = QPushButton(self.txt_add, parent=self)
        self.btn_prev = QPushButton(self.txt_back, parent=self)
        self.btn_prev.setDisabled(True)
        self.btn_del = QPushButton('Delete', parent=self)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.btn_prev, 1, 1, 1, 1)
        layout.addWidget(self.name_edt, 1, 2, 1, 2)
        layout.addWidget(self.btn_next, 1, 4, 1, 1)

        layout.addWidget(self.lat_lbl, 2, 1, 1, 2)
        layout.addWidget(self.lat_cmb, 2, 3, 1, 2)

        layout.addWidget(self.a_lbl, 3, 1, 1, 2)
        layout.addWidget(self.a_edt, 3, 3, 1, 2)

        layout.addWidget(self.b_lbl, 4, 1, 1, 2)
        layout.addWidget(self.b_edt, 4, 3, 1, 2)

        layout.addWidget(self.c_lbl, 5, 1, 1, 2)
        layout.addWidget(self.c_edt, 5, 3, 1, 2)

        layout.addWidget(self.tth_lbl, 6, 1, 1, 2)
        layout.addWidget(self.tth_edt, 6, 3, 1, 2)

        layout.addWidget(self.emax_lbl, 7, 1, 1, 2)
        layout.addWidget(self.emax_edt, 7, 3, 1, 2)

        layout.addWidget(self.de_lbl, 8, 1, 1, 2)
        layout.addWidget(self.de_edt, 8, 3, 1, 2)

        layout.addWidget(self.btn_del, 9, 3, 1, 2)

        self.btn_prev.clicked.connect(self.on_btn_prev)
        self.btn_next.clicked.connect(self.on_btn_next)
        self.btn_del.clicked.connect(self.on_btn_del)
        self.name_edt.editingFinished.connect(self.on_name_ed_f)
        self.lat_cmb.currentIndexChanged.connect(self.on_lat_cmb_changed)
        self.a_edt.valueChanged.connect(self.on_a_changed)
        self.b_edt.valueChanged.connect(self.on_b_changed)
        self.c_edt.valueChanged.connect(self.on_c_changed)
        self.tth_edt.valueChanged.connect(self.on_tth_changed)
        self.emax_edt.valueChanged.connect(self.on_emax_changed)
        self.de_edt.valueChanged.connect(self.on_de_changed)
        self.q_app.hklPhasesChanged.connect(self.on_hklph_changed)

        self._upd_ui()
        self._upd_data()

    def on_hklph_changed(self):
        self.logger.debug('on_hklph_changed: handling hklPhasesChanged')
        self.phases = self.q_app.get_hkl_phases()
        self._upd_ui()

    def on_a_changed(self):
        if self.phases[self.ph_idx].a != self.a_edt.get_value():
            self.phases[self.ph_idx].a = self.a_edt.get_value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_b_changed(self):
        if self.phases[self.ph_idx].b != self.b_edt.get_value():
            self.phases[self.ph_idx].b = self.b_edt.get_value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_c_changed(self):
        if self.phases[self.ph_idx].c != self.c_edt.get_value():
            self.phases[self.ph_idx].c = self.c_edt.get_value()
            self._upd_ui()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_tth_changed(self):
        if self.phases[self.ph_idx].tth != self.tth_edt.get_value():
            self.phases[self.ph_idx].tth = self.tth_edt.get_value()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_emax_changed(self):
        if self.phases[self.ph_idx].emax != self.emax_edt.get_value():
            self.phases[self.ph_idx].emax = self.emax_edt.get_value()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_de_changed(self):
        if self.phases[self.ph_idx].de != self.de_edt.get_value():
            self.phases[self.ph_idx].de = self.de_edt.get_value()
            self._upd_data()
            self.q_app.set_hkl_phases(self.phases)

    def on_lat_cmb_changed(self):
        if self.phases[self.ph_idx].lat != self.lat_cmb.currentText():
            self.phases[self.ph_idx].lat = self.lat_cmb.currentText()
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

        self.lat_cmb.setCurrentText(self.phases[self.ph_idx].lat)
        self.a_edt.set_value(self.phases[self.ph_idx].a, emit=False)
        self.b_edt.set_value(self.phases[self.ph_idx].b, emit=False)
        self.c_edt.set_value(self.phases[self.ph_idx].c, emit=False)
        self.tth_edt.set_value(self.phases[self.ph_idx].tth, emit=False)
        self.emax_edt.set_value(self.phases[self.ph_idx].emax, emit=False)
        self.de_edt.set_value(self.phases[self.ph_idx].de, emit=False)

        free = self.phases[self.ph_idx].free_abc
        self.a_edt.setReadOnly(not free[0])
        self.b_edt.setReadOnly(not free[1])
        self.c_edt.setReadOnly(not free[2])

    def _upd_data(self):
        self.q_app.hkl_peaks = {
            phase.name: list(map(lambda x: dict(x, **{'de': phase.de}),
                                 hkl_generator2(phase.lat, phase.a, phase.b, phase.c, phase.tth, (5, phase.emax))))
            for phase in self.phases}
        self.q_app.hklPeaksChanged.emit()
