
class PhaseData:
    # _lat_supported = 'fcc', 'bcc', 'hcp'
    _name_idx = 1

    def __init__(self):
        self._name = 'Phase %02d' % self.__class__._name_idx
        self.__class__._name_idx += 1

        self._lat = 'bcc'
        self._sgname = 'im-3m'

        self._a = 2.85   # AA
        self._b = 2.85   # AA
        self._c = 2.85   # AA
        self._alp = 90.  # deg
        self._bet = 90.  # deg
        self._gam = 90.  # deg

        self._tth = 12.  # deg

        self._emax = 200.  # keV
        self._de = 1.  # keV

        # self.enforce_lat_constraints = {lat: getattr(self, 'enf_' + lat) for lat in self._lat_supported}

    def to_dict(self):
        return {
            'name': self._name,
            # 'lattice': self._lat,
            'sgname': self._sgname,
            'a': self._a, 'b': self._b, 'c': self._c,
            'alp': self._alp, 'bet': self._bet, 'gam': self._gam,
            'tth': self._tth,
            'emax': self._emax,
            'de': self._de
        }

    @classmethod
    def from_dict(cls, data):
        result = cls()
        result.name = data['name']
        result.c = data['c']
        result.b = data['b']
        result.a = data['a']
        result.tth = data['tth']
        result.emax = data['emax']
        result.de = data['de']

        if 'sgname' in data:
            result._sgname = data['sgname']
        if 'alp' in data:
            result._alp = data['alp']
        if 'bet' in data:
            result._bet = data['bet']
        if 'gam' in data:
            result._gam = data['gam']

        # compatibility with previous version
        if 'lattice' in data:
            if data['lattice'] == 'fcc':
                result._sgname = 'fm-3m'
                result._alp = 90.
                result._bet = 90.
                result._gam = 90.
            elif data['lattice'] == 'bcc':
                result._sgname = 'im-3m'
                result._alp = 90.
                result._bet = 90.
                result._gam = 90.
            elif data['lattice'] == 'hcp':
                result._sgname = 'p63/mmc'
                result._alp = 90.
                result._bet = 90.
                result._gam = 120.
            else:
                raise ValueError('Lattice type %s not recognized' % data['lattice'])

        return result

    def __eq__(self, other):
        return all(getattr(self, attr) == getattr(other, attr) for attr in
                   ('name', 'lat', 'a', 'b', 'c', 'tth', 'emax', 'de'))

    # def enf_fcc(self):
    #     """a == b == c"""
    #     self._b = self._a
    #     self._c = self._a
    #
    # def enf_bcc(self):
    #     """a == b == c"""
    #     self._b = self._a
    #     self._c = self._a
    #
    # def enf_hcp(self):
    #     """a == b"""
    #     self._b = self._a

    # @classmethod
    # def lat_supported(cls):
    #     return cls._lat_supported

    # @property
    # def free_abc(self):
    #     if self._lat == 'fcc':
    #         return [True, False, False]
    #     elif self._lat == 'bcc':
    #         return [True, False, False]
    #     elif self._lat == 'hcp':
    #         return [True, False, True]
    #     else:
    #         raise ValueError('Lattice type %s is not supported' % self._lat)

    @property
    def sgname(self):
        return self._sgname

    @sgname.setter
    def sgname(self, val):
        self._sgname = val

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n_name):
        if not isinstance(n_name, str):
            raise ValueError('Param n_name should be str')
        self._name = n_name

    # @property
    # def lat(self):
    #     return self._lat
    #
    # @lat.setter
    # def lat(self, n_lat):
    #     if not isinstance(n_lat, str):
    #         raise ValueError('Param n_lat should be str')
    #
    #     if n_lat not in self._lat_supported:
    #         raise ValueError('Lattice type %s is not supported' % n_lat)
    #
    #     self._lat = n_lat
    #     self.enforce_lat_constraints[n_lat]()

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, n_a):
        if n_a <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._a = n_a
        # self.enforce_lat_constraints[self.lat]()

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, n_b):
        if n_b <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._b = n_b
        # self.enforce_lat_constraints[self.lat]()

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, n_c):
        if n_c <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._c = n_c
        # self.enforce_lat_constraints[self.lat]()

    @property
    def alp(self):
        return self._alp

    @alp.setter
    def alp(self, n_alp):
        if n_alp <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._alp = n_alp

    @property
    def bet(self):
        return self._bet

    @bet.setter
    def bet(self, n_bet):
        if n_bet <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._bet = n_bet

    @property
    def gam(self):
        return self._gam

    @gam.setter
    def gam(self, n_gam):
        if n_gam <= 0:
            raise ValueError('Cell parameter a should be a positive number')
        self._gam = n_gam

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