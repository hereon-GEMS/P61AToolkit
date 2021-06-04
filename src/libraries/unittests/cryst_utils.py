from unittest import TestCase
import unittest

import numpy as np
from libraries.cryst_utils import bragg, lattice_planes


class TestBragg(TestCase):
    fe_a = 2.85
    tth = 12
    e_range = (0, 200)

    def test_consistency(self):
        fe_planes = lattice_planes('bcc',
                                   self.fe_a, self.fe_a, self.fe_a,
                                   self.tth, self.e_range)

        for plane in fe_planes:
            self.assertTrue(np.all(np.isclose(plane['d'], bragg(en=plane['e'], tth=self.tth)['d'], rtol=1e-2)))
            self.assertTrue(np.all(np.isclose(plane['e'], bragg(d=plane['d'], en=plane['e'])['en'], rtol=1e-2)))
            self.assertTrue(np.isclose(self.tth, bragg(d=plane['d'], en=plane['e'])['tth'], rtol=1e-2))


if __name__ == '__main__':
    unittest.main()
