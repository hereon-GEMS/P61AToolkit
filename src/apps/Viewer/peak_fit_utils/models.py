import numpy as np


def gaussian(x, amplitude=1.0, center=0.0, sigma=1.0, **kwargs):
    return (amplitude / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-(x - center) ** 2 / (2. * sigma ** 2))


def lorentzian(x, amplitude=1.0, center=0.0, sigma=1.0, **kwargs):
    return (amplitude / (1 + ((x - center) / sigma) ** 2)) / (np.pi * sigma)


def pseudo_voigt(x, amplitude=1.0, center=0.0, sigma=1.0, fraction=0.5, **kwargs):
    sigma_g = sigma / np.sqrt(2. * np.log(2.))
    return ((1 - fraction) * gaussian(x, amplitude, center, sigma_g) +
            fraction * lorentzian(x, amplitude, center, sigma))


def ch_polyval(args, x):
    return args[0] + x * args[1] + \
           (2. * x ** 2 - 1) * args[2] + \
           (4. * x ** 3 - 3. * x) * args[3] + \
           (8. * x ** 4 - 8. * x ** 2 + 1) * args[4] + \
           (16. * x ** 5 - 20. * x ** 3 + 5. * x) * args[5] + \
           (32. * x ** 6 - 48. * x ** 4 + 18. * x ** 2 - 1.) * args[6] + \
           (64. * x ** 7 - 112. * x ** 5 + 56 * x ** 3 - 7. * x) * args[7] + \
           (128. * x ** 8 - 256. * x ** 6 + 160. * x ** 4 - 32. * x ** 2 + 1.) * args[8] + \
           (256. * x ** 9 - 576. * x ** 7 + 432. * x ** 5 - 120. * x ** 3 + 9. * x) * args[9] + \
           (512. * x ** 10 - 1280. * x ** 8 + 1120. * x ** 6 - 400. * x ** 4 + 50. * x ** 2 - 1.) * args[10] + \
           (1024. * x ** 11 - 2816. * x ** 9 + 2816. * x ** 7 - 1232. * x ** 5 + 220. * x ** 3 - 11. * x) * args[11]


def polynomial(x, xmin=0, xmax=200, c0=0, c1=0, c2=0, c3=0, c4=0, c5=0, c6=0, c7=0, c8=0, c9=0, c10=0, c11=0):
    y = np.zeros(x.shape)
    x2 = np.copy(x) - xmin
    x2 /= (xmax - xmin)
    y[(x2 > 0.) & (x2 < 1.)] = ch_polyval([c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11],
                                          x2[(x2 > 0.) & (x2 < 1.)])
    y[y < 0] = 0
    return y


peak_models = {
    'Gaussian': gaussian,
    'Lorentzian': lorentzian,
    'PseudoVoigt': pseudo_voigt
}

background_models = {
    'Chebyshev': polynomial,
    # 'Interpolation': lambda x, *args, **kwargs: np.zeros(x.shape)
    'Interpolation': lambda x, *args, **kwargs: kwargs['func'](x)
}
