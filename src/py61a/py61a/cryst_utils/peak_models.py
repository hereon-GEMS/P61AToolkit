import numpy as np


def p_voigt(xx_, a, x0, n, s, g):
    return a * (n * np.exp((xx_ - x0) ** 2 / (-2. * s ** 2)) + (1. - n) * (g ** 2) /
                ((xx_ - x0) ** 2 + g ** 2))