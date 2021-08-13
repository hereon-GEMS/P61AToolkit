from xfab.tools import genhkl_unique, genhkl_all
from xfab.sg import sgdic
import numpy as np
from typing import Union, Dict


def en_wl(en: Union[float, np.ndarray, None] = None,
          wl: Union[float, np.ndarray, None] = None
          ) -> Dict[str, Union[float, np.ndarray]]:
    """
    Converts between photon energy in keV and wavelength in AA
    :param en: [keV]
    :param wl: [AA]
    :return: dictionary with keys 'en', 'wl'.
    """
    if en is not None and wl is None:
        return {'en': en, 'wl': 12.39842 / en}
    elif wl is not None and en is None:
        return {'wl': wl, 'en': 12.39842 / wl}
    else:
        raise ValueError('Input kwargs are wl or en.')


def bragg(en: Union[float, np.ndarray, None] = None,
          wl: Union[float, np.ndarray, None] = None,
          k: Union[float, np.ndarray, None] = None,
          tth: Union[float, np.ndarray, None] = None,
          d: Union[float, np.ndarray, None] = None,
          q: Union[float, np.ndarray, None] = None
          ) -> Dict[str, Union[float, np.ndarray]]:
    """
    :param q: inverse lattice parameter [AA^-1]
    :param d: lattice parameter [AA]
    :param tth: 2Theta Bragg angle [deg]
    :param k: photon scattering vector [AA^-1]
    :param wl: photon wavelength [AA]
    :param en: photon energy [keV]
    :return:
    """
    if sum(x is not None for x in [en, wl, k, tth, d, q]) != 2:
        raise ValueError('Too many parameters specified')
    elif sum(x is not None for x in [en, wl, k]) > 1:
        raise ValueError('Too many photon parameters specified')
    elif sum(x is not None for x in [d, q]) > 1:
        raise ValueError('Too many lattice parameters specified')

    if sum(x is not None for x in [en, wl, k]) == 1:
        if k is None:
            tmp = en_wl(en=en, wl=wl)
            en = tmp['en']
            wl = tmp['wl']
            k = 2. * np.pi / wl
        else:
            wl = 2. * np.pi / k
            en = en_wl(wl=wl)['en']
    else:
        if q is not None:
            d = 2. * np.pi / q
        else:
            q = 2. * np.pi / d

        wl = 2. * d * np.sin(np.pi * tth / 360.)
        en = en_wl(wl=wl)['en']
        k = 2. * np.pi / wl

        return {'en': en, 'wl': wl, 'k': k, 'tth': tth, 'd': d, 'q': q}

    if sum(x is not None for x in [d, q]) == 1:
        if q is not None:
            d = 2. * np.pi / q
        else:
            q = 2. * np.pi / d
    else:
        d = wl / (2. * np.sin(np.pi * tth / 360.))
        q = 2. * np.pi / d

        return {'en': en, 'wl': wl, 'k': k, 'tth': tth, 'd': d, 'q': q}

    tth = 360. * np.arcsin(wl / (2. * d)) / np.pi
    return {'en': en, 'wl': wl, 'k': k, 'tth': tth, 'd': d, 'q': q}


def lattice_planes(phase, lat_a, lat_b, lat_c, alp, bet, gam, tth, energy_range=None, all_hkl=False):
    """

    :param all_hkl:
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

    if not all_hkl:
        hkl = genhkl_unique([lat_a, lat_b, lat_c, alp, bet, gam],
                            sgname=phase,
                            sintlmax=np.sin(np.radians(tth / 2.)) / en_wl(en=energy_range[1])['wl'],
                            sintlmin=np.sin(np.radians(tth / 2.)) / en_wl(en=energy_range[0])['wl'],
                            output_stl=True)
    else:
        hkl = genhkl_all([lat_a, lat_b, lat_c, alp, bet, gam],
                         sgname=phase,
                         sintlmax=np.sin(np.radians(tth / 2.)) / en_wl(en=energy_range[1])['wl'],
                         sintlmin=np.sin(np.radians(tth / 2.)) / en_wl(en=energy_range[0])['wl'],
                         output_stl=True)

    bragg_data = bragg(wl=np.sin(np.radians(tth / 2.)) / hkl[:, 3], tth=tth)
    ens = bragg_data['en']
    ds = bragg_data['d']

    if phase in ('fm-3m', 'im-3m'):
        tg = 3 * (hkl[:, 0] ** 2 * hkl[:, 1] ** 2 + hkl[:, 1] ** 2 * hkl[:, 2] ** 2 + hkl[:, 2] ** 2 * hkl[:, 0] ** 2) / \
             (hkl[:, 0] ** 2 + hkl[:, 1] ** 2 + hkl[:, 2] ** 2) ** 2
    elif phase == 'p63/mmc':
        tg = hkl[:, 2] ** 2 / (
                (4. / 3.) * (lat_c / lat_a) ** 2 * (hkl[:, 0] ** 2 + hkl[:, 1] ** 2 + hkl[:, 0] * hkl[:, 1]) + hkl[:,
                                                                                                               2] ** 2
        )
    else:
        tg = np.zeros(shape=hkl.shape[0])

    result = np.hstack((hkl, ds.reshape(-1, 1), ens.reshape(-1, 1), tg.reshape(-1, 1)))
    return [{'h': int(res[0]), 'k': int(res[1]), 'l': int(res[2]), 'd': res[4], 'e': res[5], '3g': res[6]}
            for res in result]


def cs_from_sg(sg_name):
    sg_num = int(sgdic[sg_name][2:])

    if sg_num <= 2:
        return 'triclinic'
    elif sg_num <= 15:
        return 'monoclinic'
    elif sg_num <= 74:
        return 'orthorombic'
    elif sg_num <= 142:
        return 'tetragonal'
    elif sg_num <= 167:
        return 'trigonal'
    elif sg_num <= 194:
        return 'hexagonal'
    elif sg_num <= 230:
        return 'cubic'
    else:
        return 'triclinic'
