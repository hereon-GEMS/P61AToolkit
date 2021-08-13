from unittest import TestCase

import numpy as np
import pandas as pd
from py61a.beamline_utils import motors_to_angles


class TestM2A(TestCase):
    def setUp(self) -> None:
        self.basic_input = pd.DataFrame(
            {
                'd0.rx':   [0.,  0.,  0.,  0., ],
                'd0.rz':   [10., 10., 10., 10., ],
                'd1.rx':   [10., 10., 10., 10., ],
                'd1.rz':   [0.,  0.,  0.,  0., ],
                'eu.chi':  [0.,  0.,  90., 90.],
                'eu.phi':  [0.,  0.,  0.,  0., ],
                'eu.bet':  [0.,  0.,  0.,  0.],
                'eu.alp':  [5.,  5.,  5.,  5., ],
                'Channel': [0,   1,   0,   1, ]
            }
        )
        # self.basic_output = pd.DataFrame(
        #     {
        #         'phi': [0., 0., 0., 0.],
        #         'chi': [],
        #         'psi': [90., 0., ],
        #         'tth': [10., 10., 10., 10.],
        #     }
        # )

    def test_orthogonal(self):
        self.assertTrue(True)
