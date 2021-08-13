import numpy as np
import pandas as pd
import h5py
from matplotlib import pyplot as plt
from xfab.tools import genhkl_all, genhkl_unique
from xfab.structure import int_intensity, StructureFactor, build_atomlist
from py61a.cryst_utils import en_wl, tau, mu, p_voigt, bragg
from py61a.stress import tensor_projection, inv_hooke
from utils import read_fio, write_fio
from itertools import permutations
import os

ch0 = ('entry', 'instrument', 'xspress3', 'channel00')
ch1 = ('entry', 'instrument', 'xspress3', 'channel01')
hist = ('histogram',)


def sigma_at_tau(tau_):
    s11 = -50. / ((tau_ + 50) / 500)
    s11[tau_ < 10.] = -50. / ((10. + 50) / 500)
    s22 = 20. / ((tau_ + 20) / 500)
    s22[tau_ < 10.] = 20. / ((10. + 20) / 500)
    s33 = np.zeros(tau_.shape)

    s13 = 30. * np.ones(tau_.shape)
    s12 = 130. * np.ones(tau_.shape)
    s23 = 20. * np.ones(tau_.shape)

    return np.array([
        [s11, s12, s13],
        [s12, s22, s23],
        [s13, s23, s33]
    ], dtype=np.double)


if __name__ == '__main__':
    psis = np.linspace(0., 45., 100, dtype=np.double)
    phis = np.array([0., 90., 180., 270.], dtype=np.double)
    eta = 90.
    tth = 15.

    wd = r'Z:\p61\2021\commissioning\c20210624_000_P61ADetP\raw\DetShieldingExp\experiments'
    dd = r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs\tut02_00001'
    air_f_name = os.path.join(wd, 'Empty_withoutPbCollimator_32343.nxs')
    dec_path = r'/dec/bccFe.csv'

    # initialising metadata variables
    fio_header = {'eu.chi': 0.0, 'eu.phi': 0.0, 'eu.bet': 0, 'eu.alp': -0.5 * tth,
                  'eu.x': 0.0, 'eu.y': 0.0, 'eu.z': 0.0}
    fio_data = pd.DataFrame(columns=['eu.chi', 'eu.phi', 'xspress3_index'])

    # reading the background from a real measurement
    bckg_frames = np.array([])
    with h5py.File(air_f_name, 'r') as f:
        for ii, channel in enumerate((ch1,)):
            if '/'.join(channel + hist) not in f:
                continue

            bckg_frames = np.array(f['/'.join(channel + hist)])

    # ticks for the channel 1 energy histogram
    kev = np.arange(bckg_frames.shape[1]) * 0.04995786201326 + 0.106286326963684  # channel 1

    # reading DECs
    dec = pd.read_csv(dec_path, index_col=None, comment='#')
    dec['hkl'] = dec.apply(lambda row: '%d%d%d' % (row['h'], row['k'], row['l']), axis=1)

    # reading CIF file and preparing HKLs
    al = build_atomlist()
    al.CIFread(r'Fe.cif')
    abs_element = 'Fe'

    hkls = genhkl_unique(al.atomlist.cell,
                      sgname=al.atomlist.sgname,
                      sintlmax=np.sin(np.radians(tth / 2.)) / en_wl(en=200.)['wl'],
                      sintlmin=np.sin(np.radians(tth / 2.)) / en_wl(en=5.)['wl'],
                      output_stl=True)

    # hkls[:, 3] is sin(th)/lambda, so to calculate wavelengths and energies:
    wls = np.sin(np.radians(tth / 2.)) / hkls[:, 3]
    ens = en_wl(wl=wls)['en']
    cell_v = float(al.cifblk['_cell_volume'].split('(')[0])
    idx = 0

    peak_ens, peak_ints, peak_hkls = [], [], []
    for hkl, en, wl in zip(hkls, ens, wls):
        (Fr, Fi) = StructureFactor(hkl[:3], al.atomlist.cell,
                                   al.atomlist.sgname,
                                   al.atomlist.atom,
                                   al.atomlist.dispersion)

        for ii, en_ in enumerate(peak_ens):
            if np.isclose(en_, en, rtol=1e-3):
                peak_ints[ii] += int_intensity(Fr ** 2 + Fi ** 2, 1., 1., 1., wl, cell_v, 1.)
                break
        else:
            # only taking the peaks that we have DECs for
            # (because we can not generate positions for the others)
            if any('%d%d%d' % x in dec['hkl'].values for x in permutations(np.abs(hkl[:3]).astype(np.int))):
                for x in permutations(np.abs(hkl[:3]).astype(np.int)):
                    if '%d%d%d' % x in dec['hkl'].values:
                        peak_ints.append(int_intensity(Fr ** 2 + Fi ** 2, 1., 1., 1., wl, cell_v, 1.))
                        peak_ens.append(en)
                        peak_hkls.append(x)
                        break

    peak_ens, peak_ints, peak_hkls = np.array(peak_ens), np.array(peak_ints), np.array(peak_hkls)
    peak_ints /= peak_ints.max()

    print('Relaxed lattice at 2θ = %.01f°:' % tth)
    for pe, pi, phkl in zip(peak_ens, peak_ints, peak_hkls):
        print('    %s: E = %.01f keV, I = %.0f cts' % (str(phkl), pe, 1000. * pi))

    true_peaks = pd.DataFrame(columns=sum(
        (('pv%d_h' % ii, 'pv%d_k' % ii, 'pv%d_l' % ii, 'pv%d_3gamma' % ii, 'pv%d_phase' % ii,
          'pv%d_amplitude' % ii, 'pv%d_amplitude_std' % ii,
          'pv%d_center' % ii, 'pv%d_center_std' % ii,
          'pv%d_sigma' % ii, 'pv%d_sigma_std' % ii,
          'pv%d_rwp2' % ii, 'pv%d_chi2' % ii,) for ii, phkl in enumerate(peak_hkls)),
        ('eu.chi', 'eu.phi', 'eu.bet', 'eu.alp', 'eu.x', 'eu.y', 'eu.z', 'xspress3_index', 'rwp2', 'chi2')
    ))

    taus = []
    for phi in phis:
        print('φ = %.01f°' % phi)

        for psi in psis:
            print('    ψ = %.02f°' % psi)

            true_peaks.loc[idx] = {col: None for col in true_peaks.columns}
            signal = np.zeros(kev.shape)
            for ii, (pe, pi, phkl) in enumerate(zip(peak_ens, peak_ints, peak_hkls)):
                taus.append(tau(mu=mu(abs_element, pe), tth=tth, psi=psi, eta=eta))
                s_tensor = sigma_at_tau(np.array([taus[-1]]))

                s1 = dec[dec['hkl'] == '%d%d%d' % tuple(phkl.tolist())].s1
                hs2 = dec[dec['hkl'] == '%d%d%d' % tuple(phkl.tolist())].hs2

                e_tensor = inv_hooke(s_tensor, s1.iloc[0], hs2.iloc[0])
                e_proj = tensor_projection(e_tensor.reshape((3, 3)), phi, psi)

                d = bragg(en=pe, tth=tth)['d']
                d *= 1. + e_proj
                pe = bragg(d=d, tth=tth)['en']

                signal += p_voigt(kev, a=2e6 * pi, x0=pe, n=0.7, s=3e-1 / np.sqrt(2. * np.log(2.)), g=3e-1)

                true_peaks.loc[idx, 'pv%d_h' % ii] = phkl[0]
                true_peaks.loc[idx, 'pv%d_k' % ii] = phkl[1]
                true_peaks.loc[idx, 'pv%d_l' % ii] = phkl[2]

                true_peaks.loc[idx, 'pv%d_amplitude' % ii] = 2e6 * pi
                true_peaks.loc[idx, 'pv%d_amplitude_std' % ii] = 0.

                true_peaks.loc[idx, 'pv%d_center' % ii] = pe
                true_peaks.loc[idx, 'pv%d_center_std' % ii] = 0.

                true_peaks.loc[idx, 'pv%d_sigma' % ii] = 3e-1 / np.sqrt(2. * np.log(2.))
                true_peaks.loc[idx, 'pv%d_sigma_std' % ii] = 0.

                true_peaks.loc[idx, 'pv%d_width' % ii] = 2. * 3e-1
                true_peaks.loc[idx, 'pv%d_width_std' % ii] = 0.

                true_peaks.loc[idx, 'pv%d_rwp2' % ii] = 0.
                true_peaks.loc[idx, 'pv%d_chi2' % ii] = 0.

                true_peaks.loc[idx, 'pv%d_phase' % ii] = 'cubic Fe'
                true_peaks.loc[idx, 'pv%d_3gamma' % ii] = 3 * (
                        phkl[0] ** 2 * phkl[1] ** 2 + phkl[1] ** 2 * phkl[2] ** 2 + phkl[2] ** 2 * phkl[0] ** 2) / (
                                                                  phkl[0] ** 2 + phkl[1] ** 2 + phkl[2] ** 2) ** 2

                true_peaks.loc[idx, 'pv%d_height' % ii] = (((1 - 0.7) * 2e6 * pi) / (
                    (3e-1 / np.sqrt(2. * np.log(2.)) * np.sqrt(np.pi / np.log(2.)))) + (
                                                                   0.7 * 2e6 * pi) / (
                                                               (np.pi * 3e-1 / np.sqrt(2. * np.log(2.)))))
                true_peaks.loc[idx, 'pv%d_height_std' % ii] = 0.

                true_peaks.loc[idx, 'eu.chi'] = psi
                true_peaks.loc[idx, 'eu.phi'] = phi
                true_peaks.loc[idx, 'eu.bet'] = 0.
                true_peaks.loc[idx, 'eu.alp'] = -0.5 * tth
                true_peaks.loc[idx, 'eu.x'] = 0.
                true_peaks.loc[idx, 'eu.y'] = 0.
                true_peaks.loc[idx, 'eu.z'] = 0.
                true_peaks.loc[idx, 'xspress3_index'] = idx
                true_peaks.loc[idx, 'rwp2'] = 0.
                true_peaks.loc[idx, 'chi2'] = 0.

            signal = signal.astype(np.int)

            # bckg = np.diag(bckg_frames[np.random.randint(0, 4, bckg_frames.shape[1]), :])
            bckg = np.zeros(shape=signal.shape)

            with h5py.File(os.path.join(dd, 'tut02_%05d.nxs' % idx), 'w') as f:
                f.create_dataset('entry/instrument/xspress3/channel01/histogram', data=(bckg + signal).reshape((1, -1)))
                fio_data.loc[fio_data.shape[0]] = {
                    'eu.chi': psi, 'eu.phi': phi, 'xspress3_index': idx
                }
                idx += 1

    write_fio(fio_header, fio_data, dd + '.fio')
    true_peaks.to_csv(dd + '_true.csv')

    taus = np.sort(np.array(taus))
    stress_tensor_md = sigma_at_tau(taus)

    # taus = np.linspace(0.1, 150, 200)
    # stress_tensor_md = sigma_at_tau(taus)

    plt.figure()

    ax1 = plt.subplot(121)
    ax1_2 = ax1.twinx()
    ax1_2.hist(taus, bins=psis.size, fc=(0, 0, 0, 0.2))
    ax1.set_title(r'$\sigma_{11}$, $\sigma_{22}$, $\sigma_{33}$')
    ax1.set_xlabel(r'Depth, [mcm]')
    ax1.set_ylabel(r'$\sigma$, [MPa]')
    ax1_2.set_ylabel(r'Points measured, [cts]')
    ax1.plot(taus, stress_tensor_md[0, 0], '--', color='r', label=r'$\sigma_{11}$')
    ax1.plot(taus, stress_tensor_md[1, 1], '--', color='g', label=r'$\sigma_{22}$')
    ax1.plot(taus, stress_tensor_md[2, 2], '--', color='b', label=r'$\sigma_{33}$')
    ax1.legend()

    ax2 = plt.subplot(122)
    ax2_2 = ax2.twinx()
    ax2_2.hist(taus, bins=psis.size, fc=(0, 0, 0, 0.2))
    ax2.set_title(r'$\sigma_{12}$, $\sigma_{13}$, $\sigma_{23}$')
    ax2.set_xlabel(r'Depth, [mcm]')
    ax2.set_ylabel(r'$\sigma$, [MPa]')
    ax2_2.set_ylabel(r'Points measured, [cts]')
    ax2.plot(taus, stress_tensor_md[0, 1], '--', color='r', label=r'$\sigma_{12}$')
    ax2.plot(taus, stress_tensor_md[0, 2], '--', color='g', label=r'$\sigma_{13}$')
    ax2.plot(taus, stress_tensor_md[1, 2], '--', color='b', label=r'$\sigma_{23}$')
    ax2.legend()
    plt.tight_layout()
    plt.show()
