from multiprocessing import Pool, cpu_count
from scipy.optimize import least_squares
import numpy as np
from matplotlib import pyplot as plt


def gauss(x, x0, sigma, amplitude):
    return amplitude * np.exp(-(x - x0) ** 2 / (2. * sigma ** 2))


class IntervalOptimizer:
    def __init__(self, func, xdata, ydata, optimizer):
        self.func = func
        self.xdata = xdata
        self.ydata = ydata
        self.opt = optimizer

    def __call__(self, interval):
        ll, rr = interval
        iy = self.ydata[(self.xdata > ll) & (self.xdata < rr)]
        ix = self.xdata[(self.xdata > ll) & (self.xdata < rr)]

        def residuals(x, *args, **kwargs):
            return np.sum((iy - gauss(ix, *x)) ** 2)

        x0 = (np.min(ix), 2., 1.)
        opt_result = least_squares(residuals, x0=x0)

        return opt_result.x


if __name__ == '__main__':
    xx = np.linspace(0, 100, 1000)
    centers = (10., 27., 34., 46., 50., 71., 80., 92.)

    yy = np.random.rand(xx.size).reshape(xx.shape)
    for cc in centers:
        yy += gauss(xx, cc, 0.7, 10.)

    # plt.plot(xx, yy)
    # plt.show()

    intervals = tuple([(cc - 3, cc + 3) for cc in centers])

    opt = IntervalOptimizer(gauss, xx, yy, least_squares)
    with Pool(cpu_count()) as p:
        print(p.map(opt, intervals))
