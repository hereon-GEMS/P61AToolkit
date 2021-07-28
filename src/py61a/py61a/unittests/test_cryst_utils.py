from unittest import TestCase
import unittest

import numpy as np
from py61a.cryst_utils import bragg, lattice_planes


class TestBragg(TestCase):
    fe_a = 2.85
    fe_alp = 90.
    tth = 12
    e_range = (1., 200.)

    def test_consistency(self):
        fe_planes = lattice_planes('im-3m',
                                   self.fe_a, self.fe_a, self.fe_a, self.fe_alp, self.fe_alp, self.fe_alp,
                                   self.tth, self.e_range)

        for plane in fe_planes:
            self.assertTrue(np.all(np.isclose(plane['d'], bragg(en=plane['e'], tth=self.tth)['d'], rtol=1e-1)))
            self.assertTrue(np.all(np.isclose(plane['e'], bragg(d=plane['d'], en=plane['e'])['en'], rtol=1e-1)))
            self.assertTrue(np.isclose(self.tth, bragg(d=plane['d'], en=plane['e'])['tth'], rtol=1e-1))


class TestAbsorption(TestCase):
    pass
