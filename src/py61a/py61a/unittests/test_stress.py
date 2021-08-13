from unittest import TestCase
import unittest
from scipy.stats import linregress

import numpy as np
import pandas as pd
from py61a.stress import hooke, inv_hooke, Sin2Psi, MultiWaveLength, tensor_projection
from py61a.cryst_utils import bragg, tau, mu, lattice_planes
from itertools import permutations


class TestHooke(TestCase):
    taus = np.linspace(1, 150, 1000)  # mcm
    # taus = np.array([0.1])

    @staticmethod
    def sigma_at_tau(tau_):
        s11 = -1000. * (tau_ ** 2 + 0.8 * tau_ + 0.06) / (tau_ + 0.4) ** 3
        s22 = -500. * np.ones(tau_.shape)
        s33 = (120. * tau_ ** 3) / (0.4 * tau_ + 1.) ** 4

        s13 = (-0.01372 - 1.698 * tau_ - 44.4 * tau_ ** 2 - 340. * tau_ ** 3) / (tau_ * (0.07 + tau_) ** 3)
        # s13 = np.zeros(tau_.shape)
        s12 = np.zeros(tau_.shape)
        s23 = np.zeros(tau_.shape)

        return np.array([
            [s11, s12, s13],
            [s12, s22, s23],
            [s13, s23, s33]
        ])

    def test_consistency(self):
        s_tensor = np.random.random(900).reshape((3, 3, -1))
        s1, hs2 = np.random.random(1), np.random.random(1)

        e_tensor = inv_hooke(s_tensor, s1, hs2)
        s_tensor_ = hooke(e_tensor, s1, hs2)

        self.assertTrue(np.all(np.isclose(s_tensor, s_tensor_)))


class TestTensorProjection(TestCase):
    def test_sin2psi(self):
        psis = np.linspace(0., 85., 100)
        strain = np.random.rand(9).reshape((3, 3))
        strain += strain.T

        e_proj1 = np.array([tensor_projection(strain, 0, psi) for psi in psis])
        e_proj2 = np.array([tensor_projection(strain, 180, psi) for psi in psis])
        e_proj3 = np.array([tensor_projection(strain, 90, psi) for psi in psis])
        e_proj4 = np.array([tensor_projection(strain, 270, psi) for psi in psis])

        slope1, intercept1, _, _, _ = linregress(np.sin(np.radians(psis)) ** 2, 0.5 * (e_proj1 + e_proj2))
        slope2, intercept2, _, _, _ = linregress(np.sin(np.radians(2. * psis)), 0.5 * (e_proj1 - e_proj2))
        slope3, intercept3, _, _, _ = linregress(np.sin(np.radians(psis)) ** 2, 0.5 * (e_proj3 + e_proj4))
        slope4, intercept4, _, _, _ = linregress(np.sin(np.radians(2. * psis)), 0.5 * (e_proj3 - e_proj4))

        diff = (strain - np.array([
            [slope1 + intercept1, np.nan, slope2],
            [np.nan, slope3 + intercept3, slope4],
            [slope2, slope4, np.mean((intercept1, intercept3))]
        ])) / strain

        self.assertTrue(np.any(~np.isnan(diff)))
        self.assertTrue(np.all(np.isclose(diff[~np.isnan(diff)], 0.)))


class TestMultiWavelength(TestCase):
    def test_fe_peaks(self):
        d0 = 2.84034
        psis = np.linspace(0., 45., 10)
        phis = [0., 90., 180., 270.]
        eta = 90.
        tth = 5. + 10. * np.random.rand()

        stress_tensor = ((np.random.rand(9) - 0.5) * 100.).reshape((3, 3))
        stress_tensor += stress_tensor.T
        stress_tensor = stress_tensor.reshape((3, 3, 1))

        # f_name_out = r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs\tut02_00001_true.csv'
        dec_path = r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\dec\bccFe.csv'

        # reading DECs
        dec = pd.read_csv(dec_path, index_col=None, comment='#')
        dec = {(row['h'], row['k'], row['l']): (row['s1'], row['hs2']) for ii, row in dec.iterrows()}

        # generating peak positions and filtering out ones that we don't have DECs for
        peaks = []
        for peak in lattice_planes('im-3m', d0, d0, d0, 90., 90., 90., tth, (5., 200.)):
            for hkl in permutations((peak['h'], peak['k'], peak['l'])):
                if hkl in dec.keys():
                    peak.update({'s1': dec[hkl][0], 'hs2': dec[hkl][1]})
                    peaks.append(peak)
                    break

        # creating the dataset for sin2psi analysis
        peaks_dataset = pd.DataFrame(
            columns=pd.MultiIndex.from_tuples(
                list(sum(((('pv' + str(ii), 'h'), ('pv' + str(ii), 'k'), ('pv' + str(ii), 'l'),
                           ('pv' + str(ii), 'phase'),
                           ('pv' + str(ii), 's1'), ('pv' + str(ii), 'hs2'),
                           ('pv' + str(ii), 'depth'), ('pv' + str(ii), 'd0'),
                           ('pv' + str(ii), 'd')) for ii, peak in enumerate(peaks)),
                         (('md', 'eu.phi'), ('md', 'eu.chi'))))))

        # filling up the dataset for sin2psi
        for phi in phis:
            for psi in psis:
                row = {('md', 'eu.phi'): phi, ('md', 'eu.chi'): psi}
                for ii, peak in enumerate(peaks):
                    depth = tau(mu('Fe', peak['e']), tth, psi, eta)
                    strain = tensor_projection(
                        inv_hooke(
                            stress_tensor,
                            peak['s1'], peak['hs2']).reshape((3, 3)),
                        phi, psi)
                    row[('pv' + str(ii), 'h')] = peak['h']
                    row[('pv' + str(ii), 'k')] = peak['k']
                    row[('pv' + str(ii), 'l')] = peak['l']
                    row[('pv' + str(ii), 'phase')] = 'Fe'
                    row[('pv' + str(ii), 's1')] = peak['s1']
                    row[('pv' + str(ii), 'hs2')] = peak['hs2']
                    row[('pv' + str(ii), 'd')] = peak['d'] * (1. + strain)
                    row[('pv' + str(ii), 'd0')] = peak['d']
                    row[('pv' + str(ii), 'depth')] = depth
                peaks_dataset.loc[peaks_dataset.shape[0]] = row

        analysis = Sin2Psi(dataset=peaks_dataset, phi_atol=1., psi_atol=.1, psi_max=np.max(psis))
        analysis = MultiWaveLength(analysis)
        for ii in range(analysis.stress_tensor.shape[2]):
            diff = (analysis.stress_tensor[:, :, ii] - stress_tensor.reshape((3, 3))) / stress_tensor.reshape((3, 3))
            self.assertTrue(np.any(~np.isnan(diff)))
            self.assertTrue(np.all(np.isclose(diff[~np.isnan(diff)], 0.)))
