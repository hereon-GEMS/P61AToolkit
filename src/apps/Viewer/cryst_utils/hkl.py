import numpy as np
from cryst_utils.absorption import absorption, density


def sind(x):
    return np.sin(np.radians(x))


def cosd(x):
    return np.cos(np.radians(x))


def a_vals2lattice_dists(a_val, h, k, l):
    return a_val / (h ** 2 + k ** 2 + l ** 2) ** 0.5


def hkl_generator2(phase, lat_a, lat_b, lat_c, tth, energy_range=None, unique=False):
    """
    provided by Guilherme and adapted

    :param phase:
    :param lat_a:
    :param lat_b:
    :param lat_c:
    :param tth:
    :param energy_range:
    :param unique:
    :return:
    """
    if phase.lower() not in ('hcp', 'fcc', 'bcc'):
        return

    hkl = np.array([[h, k, ll] for h in range(0, 10) for k in range(0, 10) for ll in range(0, 10)])
    if phase.lower() == 'hcp':
        hkl = hkl[(np.sum(hkl, axis=1) > 0) &
                  (hkl[:, 1] <= hkl[:, 0]) &
                  ((hkl[:, 2] % 2 == 0) |
                   ((hkl[:, 0] + 2 * hkl[:, 1]) % 3 != 0))]
    elif phase.lower() == 'fcc':
        hkl = hkl[(np.sum(hkl, axis=1) > 0) &
                  (hkl[:, 1] <= hkl[:, 0]) &
                  (hkl[:, 2] <= hkl[:, 1]) &
                  (np.all(hkl % 2 != 0, axis=1) |
                   np.all(hkl % 2 == 0, axis=1))]
    elif phase.lower() == 'bcc':
        hkl = hkl[(np.sum(hkl, axis=1) > 0) &
                  (hkl[:, 1] <= hkl[:, 0]) &
                  (hkl[:, 2] <= hkl[:, 1]) &
                  (np.sum(hkl, axis=1) % 2 == 0)]

    if phase.lower() == 'hcp':
        d_val = (1. / ((4. / 3. * (hkl[:, 0] ** 2 + hkl[:, 0] * hkl[:, 1] + hkl[:, 1] ** 2) / lat_a ** 2) +
                       (hkl[:, 2] ** 2 / lat_c ** 2))) ** 0.5
    elif phase.lower() in ('fcc', 'bcc'):
        d_val = lat_a / np.sum(hkl ** 2, axis=1) ** 0.5
    else:
        d_val = np.zeros(shape=hkl.shape[0])

    if unique:
        counts = np.array([sum((d_val <= 1.001 * d_val[ii]) & (d_val >= 0.999 * d_val[ii]))
                           for ii in range(len(d_val))])
        hkl, d_val = hkl[counts < 2], d_val[counts < 2]

    ens = 12.39842 / (2. * d_val * np.sin(np.radians(tth / 2)))

    if phase.lower() in ('fcc', 'bcc'):
        tg = 3 * (hkl[:, 0] ** 2 * hkl[:, 1] ** 2 + hkl[:, 1] ** 2 * hkl[:, 2] ** 2 + hkl[:, 2] ** 2 * hkl[:, 0] ** 2) / \
             (hkl[:, 0] ** 2 + hkl[:, 1] ** 2 + hkl[:, 2] ** 2) ** 2
    elif phase.lower() == 'hcp':
        tg = hkl[:, 2] ** 2 / (
            (4./3.) * (lat_c / lat_a) ** 2 * (hkl[:, 0] ** 2 + hkl[:, 1] ** 2 + hkl[:, 0] * hkl[:, 1]) + hkl[:, 2] ** 2
        )
    else:
        tg = np.zeros(shape=hkl.shape[0])

    result = np.hstack((hkl, d_val.reshape((d_val.shape[0], -1)),
                        ens.reshape((ens.shape[0], -1)), tg.reshape((tg.shape[0], -1))))

    result = result[(result[:, 4] > energy_range[0]) & (result[:, 4] < energy_range[1])]
    result = [
        {'h': int(ref[0]), 'k': int(ref[1]), 'l': int(ref[2]), 'd': ref[3], 'e': ref[4], '3g': ref[5]}
        for ref in result
    ]
    return result


def hkl_generator(phase, lattice_par, tth, energy_range=None):
    """
    provided by Guilherme and adapted

    :param phase:
    :param lattice_par:
    :param tth:
    :param energy_range:
    :return:
    """
    hkl_table = np.array([])
    if phase.lower() == 'hcp':
        if lattice_par.size > 2:
            a = lattice_par[0]
            c = lattice_par[2]
        else:
            a = lattice_par[0]
            c = lattice_par[1]
        for h in np.arange(0, 10, 1):
            for k in np.arange(0, h, 1):
                for l in np.arange(0, 10, 1):
                    # hkl: l = even or h+2k ~= 3n
                    if (h + k + l) > 0 and ((l % 2) == 0 or ((h + 2 * k) % 3) * ((h + 2 * k) % 3) != 0):
                        dVal = (1 / ((4 / 3 * (h ** 2 + h * k + k ** 2) / a ** 2) + (l ** 2 / c ** 2))) ** 0.5
                        energy = 12.39842 / (2 * dVal * sind(tth / 2))
                        if energy_range is not None:
                            if energy > energy_range[0] and energy < energy_range[1]:
                                if len(hkl_table) > 0:
                                    hkl_table = np.vstack([hkl_table, [h, k, l, dVal, energy]])
                                else:
                                    hkl_table = np.hstack([hkl_table, [h, k, l, dVal, energy]])
    elif phase.lower() == 'fcc':
        if lattice_par.size > 1:
            a = lattice_par[0]
        else:
            a = lattice_par
        for h in np.arange(0, 10, 1):
            for k in np.arange(0, h, 1):
                for l in np.arange(0, k, 1):
                    # hkl: h,k,l = odd or h,k,l = even
                    if (h + k + l) > 0 and ((h % 2) * (k % 2) * (l % 2) != 0 or (h % 2) + (k % 2) + (l % 2) == 0):
                        dVal = a_vals2lattice_dists(a, h, k, l)
                        energy = 12.39842 / (2 * dVal * sind(tth / 2))
                        if energy_range is not None:
                            if energy > energy_range[0] and energy < energy_range[1]:
                                if len(hkl_table) > 0:
                                    hkl_table = np.vstack([hkl_table, [h, k, l, dVal, energy]])
                                else:
                                    hkl_table = np.hstack([hkl_table, [h, k, l, dVal, energy]])
    elif phase.lower() == 'bcc':
        if lattice_par.size > 1:
            a = lattice_par[0]
        else:
            a = lattice_par
        for h in np.arange(0, 10, 1):
            for k in np.arange(0, h, 1):
                for l in np.arange(0, k, 1):
                    # hkl: h+k+l = even
                    if (h + k + l) > 0 and (h + k + l) % 2 == 0:
                        dVal = a_vals2lattice_dists(a, h, k, l)
                        energy = 12.39842 / (2 * dVal * sind(tth / 2))
                        if energy_range is not None:
                            if energy > energy_range[0] and energy < energy_range[1]:
                                if len(hkl_table) > 0:
                                    hkl_table = np.vstack([hkl_table, [h, k, l, dVal, energy]])
                                else:
                                    hkl_table = np.hstack([hkl_table, [h, k, l, dVal, energy]])
    # sort hkl table
    if hkl_table.size > 0:
        hkl_table = hkl_table[hkl_table[:, 4].argsort()]
    return hkl_table


def tau(psi, th, eta, energy, element):
    """
    provided by Guilherme and adapted

    :param psi:
    :param th:
    :param eta:
    :param energy:
    :param element:
    :return:
    """

    if element not in absorption.keys() or element not in density.keys():
        return
    else:
        lmi = np.interp(np.log(energy), np.log(absorption[element]['E'] * 1e3), absorption[element]['abs'])
        mi = np.exp(lmi) * density[element]

    return 10000 * ((sind(th) ** 2) - (sind(psi) ** 2) + (cosd(th) ** 2) * (sind(psi) ** 2) * (sind(eta) ** 2)) / \
        (2 * mi * sind(th) * cosd(psi))


def three_gamma(h, k=None, l=None):
    if k is None and l is None:
        h, k, l = h // 100, (h // 10) % 10, h % 10
    return 3 * (h ** 2 * k ** 2 + k ** 2 * l ** 2 + l ** 2 * h ** 2) / (h ** 2 + k ** 2 + l ** 2) ** 2


def elastic_const(phase, hkl):
    """
    provided by Guilherme and adapted

    :param phase:
    :param hkl:
    :return:
    """
    if phase.lower() == 'bcc':
        if hkl == 110 or hkl == 211 or hkl == 220 or hkl == 321 or hkl == 330:
            return np.array([-1.232104E-6, 5.688224E-6])
        elif hkl == 200 or hkl == 400:
            return np.array([-1.856303E-6, 7.560821E-6])
        elif hkl == 310:
            return np.array([-1.631592E-6, 6.886686E-6])
        elif hkl == 222:
            return np.array([-1.024038E-6, 5.064025E-6])
        elif hkl == 420:
            return np.array([-1.456816E-6, 6.362359E-6])
        elif hkl == 411:
            return np.array([-1.602000E-6, 6.797910E-6])
        elif hkl == 332:
            return np.array([-1.067027E-6, 5.192992E-6])
        elif hkl == 521:
            return np.array([-1.498429E-6, 6.487199E-6])
        else:
            return


def stress_fac(phi, psi, phase, hkl):
    """
    provided by Guilherme and adapted

    :param phi:
    :param psi:
    :param phase:
    :param hkl:
    :return:
    """
    s1, hs2 = elastic_const(phase, hkl)
    f11 = hs2 * (cosd(phi) ** 2 * sind(psi) ** 2) + s1
    f12 = hs2 * (sind(2 * phi) * sind(psi) ** 2)
    f13 = hs2 * (cosd(phi) * sind(2 * psi))
    f21 = f12
    f22 = hs2 * (sind(phi) ** 2 * sind(psi) ** 2) + s1
    f23 = hs2 * (sind(phi) * sind(2 * psi))
    f31 = f13
    f32 = f23
    f33 = hs2 * (cosd(psi) ** 2) + s1
    return np.array([f11, f12, f13, f21, f22, f23, f31, f32, f33])
