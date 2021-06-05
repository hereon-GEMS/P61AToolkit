import numpy as np


def gaussian(x, amplitude=1.0, center=0.0, sigma=1.0, **kwargs):
    return (amplitude / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-(x - center) ** 2 / (2. * sigma ** 2))


def lorentzian(x, amplitude=1.0, center=0.0, sigma=1.0, **kwargs):
    return (amplitude / (1 + ((x - center) / sigma) ** 2)) / (np.pi * sigma)


def pseudo_voigt(x, amplitude=1.0, center=0.0, sigma=1.0, fraction=0.5, **kwargs):
    sigma_g = sigma / np.sqrt(2. * np.log(2.))
    return ((1 - fraction) * gaussian(x, amplitude, center, sigma_g) +
            fraction * lorentzian(x, amplitude, center, sigma))


models = {
    'Gaussian': gaussian,
    'Lorentzian': lorentzian,
    'PseudoVoigt': pseudo_voigt
}
