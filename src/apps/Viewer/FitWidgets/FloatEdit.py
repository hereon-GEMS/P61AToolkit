from PyQt5.QtWidgets import QLineEdit
import re
import numpy as np
from collections import defaultdict
from PyQt5.QtCore import pyqtSignal


class FloatEdit(QLineEdit):
    """"""
    valueChanged = pyqtSignal(object)
    read_only_style = 'QLineEdit {background-color: rgb(70, 70, 70); color: rgb(200, 200, 200)}'
    regular_style = 'QLineEdit {background-color: rgb(255, 255, 255);}'
    wrong_input_style = 'QLineEdit {background-color: rgb(255, 70, 70);}'

    def __init__(self, parent=None, inf_allowed=True, none_allowed=False, init_val=0.):
        QLineEdit.__init__(self, parent=parent)

        rgx = r'^(?P<main>-?[0-9]+\.?)(?P<decimal>[0-9]+)?([Ee](?P<exp>[+-]{0,1}[0-9]+))?$'
        if inf_allowed:
            rgx += r'|^(?P<inf>\s*INF|inf|-INF|-inf\s*)$'
        if none_allowed:
            rgx += r'|^(?P<none>\s*None|none\s*)$'

        self.float_regexp = re.compile(rgx)
        self._value = init_val
        self._upd()

        self.textChanged.connect(self.on_text_changed)
        self.returnPressed.connect(self.on_text_submitted)
        self.editingFinished.connect(self.on_text_submitted)

    def setReadOnly(self, a0: bool) -> None:
        QLineEdit.setReadOnly(self, a0)

        if a0:
            self.setStyleSheet(self.read_only_style)
        else:
            self.setStyleSheet(self.regular_style)

    def _upd(self, emit=True):
        if self._value is not None:
            self.setText('%.03E' % self._value)
        else:
            self.setText('None')
        if emit:
            self.valueChanged.emit(self._value)

    def on_text_changed(self):
        match = self.float_regexp.match(self.text())
        if not match:
            self.setStyleSheet(self.wrong_input_style)
            return None
        else:
            if self.isReadOnly():
                self.setStyleSheet(self.read_only_style)
            else:
                self.setStyleSheet(self.regular_style)
            return match

    def on_text_submitted(self):
        match = self.on_text_changed()
        if match:
            gd = defaultdict(lambda *args: None, match.groupdict())

            if gd['inf'] is not None:
                self._value = np.float(gd['inf'])
            elif gd['none'] is not None:
                self._value = None
            elif gd['main'] is not None:
                self._value = float(gd['main'])
                if gd['decimal'] is not None:
                    self._value += (float(gd['decimal']) if self._value >= 0
                                    else -float(gd['decimal'])) * 10 ** (-len(gd['decimal']))
                if gd['exp'] is not None:
                    self._value *= 10 ** (int(gd['exp']))
            self._upd()

    def get_value(self):
        return self._value

    def set_value(self, val, emit=True):
        if not isinstance(val, (int, float, np.int, np.float, np.int64, type(None))):
            raise ValueError(str(val) + ' is ' + str(type(val)) + ' and not supported')
        else:
            self._value = val
            self._upd(emit)

    value = property(fget=get_value, fset=set_value)


if __name__ == '__main__':
    from P61App import P61App
    import sys
    q_app = P61App(sys.argv)
    app = FloatEdit()
    app.value = 10
    app.show()
    sys.exit(q_app.exec())