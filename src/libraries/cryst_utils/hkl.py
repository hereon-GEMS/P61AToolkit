import numpy as np


def en_wl(**kwargs):
    """
    Converts between photon energy in keV and wavelength in AA
    :param kwargs: 'en' [keV] or 'wl' [AA]
    :return: dictionary with keys 'en', 'wl'.
    """
    if 'en' in kwargs and 'wl' not in kwargs:
        return {'en': kwargs['en'], 'wl': 12.39842 / kwargs['en']}
    elif 'wl' in kwargs and 'en' not in kwargs:
        return {'wl': kwargs['wl'], 'en': 12.39842 / kwargs['wl']}
    else:
        raise ValueError('Input kwargs are wl or en.')


def bragg(**kwargs):
    """
    'en' [keV] or 'wl' [AA] or 'k' [AA^-1] describing the photons
    'tth' [deg] describing the setup geometry
    'd' [AA] or 'q' [AA^-1] describing the sample
    :param kwargs:
    :return:
    """
    if 'en' in kwargs or 'wl' in kwargs:
        wl = en_wl(**kwargs)['wl']
    else:
        wl = None

    if wl is None and 'k' in kwargs:
        wl = en_wl(wl=2. * np.pi / kwargs['k'])['wl']
    elif wl is not None and 'k' in kwargs:
        raise ValueError('Too much data: use one of three keywords: \'en\', \'wl\', \'k\'')

    if 'tth' in kwargs:
        tth = kwargs['tth']
    else:
        tth = None

    if 'd' in kwargs and 'q' not in kwargs:
        d = kwargs['d']
    elif 'q' in kwargs and 'd' not in kwargs:
        d = 2. * np.pi / kwargs['q']
    elif 'd' not in kwargs and 'q' not in kwargs:
        d = None
    else:
        raise ValueError('Too much data: use one of two keywords: \'d\', \'q\'')

    if [wl is None, tth is None, d is None].count(True) != 1:
        raise ValueError()

    if d is None:
        d = wl / (2. * np.sin(np.pi * tth / 360.))
    elif tth is None:
        tth = 360. * np.arcsin(wl / (2. * d)) / np.pi
    elif wl is None:
        wl = 2. * d * np.sin(np.pi * tth / 360.)

    result = en_wl(wl=wl)
    result.update({'k': 2. * np.pi / wl, 'tth': tth, 'd': d, 'q': 2. * np.pi / d})
    return result


def lattice_planes(phase, lat_a, lat_b, lat_c, tth, energy_range=None):
    """

    :param phase:
    :param lat_a:
    :param lat_b:
    :param lat_c:
    :param tth:
    :param energy_range:
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

    ens = 12.39842 / (2. * d_val * np.sin(np.radians(tth / 2)))

    result = np.hstack((hkl, d_val.reshape((d_val.shape[0], -1)), ens.reshape((ens.shape[0], -1))))
    result = result[(result[:, 4] > energy_range[0]) & (result[:, 4] < energy_range[1])]
    result = [{'h': int(ref[0]), 'k': int(ref[1]), 'l': int(ref[2]), 'd': ref[3], 'e': ref[4]} for ref in result]
    return result
