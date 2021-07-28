import pandas as pd
import numpy as np
import os

density = \
    {  # g/cm3
        'Al': 2.7,
        'Cr': 7.19,
        'Fe': 7.874,
        'Mg': 1.738,
        'Ni': 8.9,
        'Ti': 4.506,
        'W': 19.28,
    }

_wd = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'NIST_abs')
absorption = {el: pd.read_csv(os.path.join(_wd, el + '.csv'), comment='#') for el in density.keys()}


def mu(el, en):
    """
    :param el: element name as string: 'Fe', 'Cr', ...
    :param en: energy in [keV]
    :return: linear attenuation coefficient mu [cm^-1]
    """
    lmi = np.interp(np.log(en), np.log(absorption[el]['E'] * 1e3), np.log(absorption[el]['att']))
    return np.exp(lmi) * density[el]


def tau(mu, tth, psi, eta):
    """

    :param mu: linear attenuation coefficient [cm^-1]
    :param tth: 2Theta angle [deg]
    :param psi: psi angle [deg]
    :param eta: eta angle [deg]
    :return: information depth [mcm]
    """

    return 10000 * ((np.sin(np.radians(tth / 2.)) ** 2) - (np.sin(np.radians(psi)) ** 2) +
                    (np.cos(np.radians(tth / 2.)) ** 2) * (np.sin(np.radians(psi)) ** 2) *
                    (np.sin(np.radians(eta)) ** 2)) / (2 * mu * np.sin(np.radians(tth / 2.)) * np.cos(np.radians(psi)))
