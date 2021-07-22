from xfab.tools import genhkl_unique
from xfab.sg import sgdic
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


def lattice_planes(phase, lat_a, lat_b, lat_c, alp, bet, gam, tth, energy_range=None):
    """

    :param phase:
    :param lat_a:
    :param lat_b:
    :param lat_c:
    :param alp:
    :param bet:
    :param gam:
    :param tth:
    :param energy_range:
    :return:
    """
    if phase not in sgdic.keys():
        raise ValueError('Incorrect lattice type: %s' % phase)

    if energy_range is None:
        energy_range = (5., 200.)

    hkl = genhkl_unique([lat_a, lat_b, lat_c, alp, bet, gam],
                        sgname=phase,
                        sintlmax=np.sin(np.radians(tth / 2.)) / en_wl(en=energy_range[1])['wl'],
                        sintlmin=np.sin(np.radians(tth / 2.)) / en_wl(en=energy_range[0])['wl'],
                        output_stl=True)

    bragg_data = bragg(wl=np.sin(np.radians(tth / 2.)) / hkl[:, 3], tth=tth)
    ens = bragg_data['en']
    ds = bragg_data['d']

    result = np.hstack((hkl, ds.reshape(-1, 1), ens.reshape(-1, 1)))
    return [{'h': int(res[0]), 'k': int(res[1]), 'l': int(res[2]), 'd': res[4], 'e': res[5]} for res in result]
