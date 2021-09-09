from py61a.beamline_utils import read_fio
from matplotlib import pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


def func2(z_, bckg, i0, a, h, z0):
    zz_ = z_ - z0
    p2 = (1. / (a**3 * h ** 2)) * (8. - 8. * np.exp(-0.5 * a * (h + 2. * zz_)) +
                                   a * (h + 2. * zz_) * (-4. + a * (h + 2. * zz_)))
    p3 = (1. / (a**3 * h ** 2)) * (8. - 8. * np.exp(-0.5 * a * (h + 2. * zz_)) -
                                   8. * a * np.exp(-a * zz_) * h + 4. * a * (h - 2. * zz_) +
                                   a ** 2 * (h - 2. * zz_) ** 2)
    p4 = (1. / (a**3 * h ** 2)) * 8. * np.exp(-0.5 * a * (h + 2. * zz_)) * \
         (-1. + np.exp(a * h) - a * h * np.exp(0.5 * a * h))

    res = np.zeros(zz_.shape)
    res[(zz_ > -0.5 * h) & (zz_ <= 0.)] = p2[(zz_ > -0.5 * h) & (zz_ <= 0.)]
    res[(zz_ <= 0.5 * h) & (zz_ > 0.)] = p3[(zz_ <= 0.5 * h) & (zz_ > 0.)]
    res[zz_ > 0.5 * h] = p4[zz_ > 0.5 * h]

    res /= np.max(res)
    return bckg + res * i0


def func3(z_, bckg, i0, a, h, z0):
    zz_ = z_ - z0
    p2 = (1. / a) * (1. - np.exp(-0.5 * a * (h + 2. * zz_)))
    p3 = (1. / a) * (2. * np.exp(-a * zz_) * np.sinh(0.5 * a * h))

    res = np.zeros(zz_.shape)
    res[(zz_ > -0.5 * h) & (zz_ < 0.5 * h)] = p2[(zz_ > -0.5 * h) & (zz_ < 0.5 * h)]
    res[zz_ > 0.5 * h] = p3[zz_ > 0.5 * h]

    res /= np.max(res)
    return bckg + res * i0


if __name__ == '__main__':
    f1 = r'..\..\..\data\peaks\TiLSP\phi0Trans_3_00041.fio'
    f2 = r'..\..\..\data\peaks\TiLSP\phi90Trans_4_00046.fio'
    header, data = read_fio(f1)

    zs, cts, chis = [], [], list(sorted(set(data['eu.chi'])))

    for chi in chis:
        d_ = data[np.isclose(data['eu.chi'], chi)]
        d_ = d_[d_['eu.z'] < -51.4]
        plt.plot(d_['eu.z'], d_['xspress3roi1'])

        p0_ = (
            9e4,  # bckg
            (np.max(d_['xspress3roi1']) - np.min(d_['xspress3roi1'])),  # i0
            8.,  # a
            0.17,  # h
            -52.2  # z0
        )

        print(d_['eu.z'].iloc[np.argmax(d_['xspress3roi1'])])

        # popt, pcov = curve_fit(
        #     func2, d_['eu.z'].to_numpy(), d_['xspress3roi1'].to_numpy(),
        #     p0=p0_,
        #     bounds=((0., 0.8 * (np.max(d_['xspress3roi1']) - np.min(d_['xspress3roi1'])), 0., 0.15, -52.25),
        #             (1.01e5, 1.2 * (np.max(d_['xspress3roi1']) - np.min(d_['xspress3roi1'])), 10., 0.20, -51.85)),
        #     max_nfev=1e15, xtol=1e-10
        # )

        popt, pcov = curve_fit(
            func3, d_['eu.z'].to_numpy(), d_['xspress3roi1'].to_numpy(),
            p0=p0_,
            bounds=((0., 0.8 * (np.max(d_['xspress3roi1']) - np.min(d_['xspress3roi1'])), 0., 0.05, -52.25),
                    (1.01e5, 1.2 * (np.max(d_['xspress3roi1']) - np.min(d_['xspress3roi1'])), 20., 0.40, -51.85)),
            max_nfev=1e15, xtol=1e-10
        )

        print(popt)
        plt.plot(d_['eu.z'], func3(d_['eu.z'], *popt))
        zs.append(popt[-1])
        cts.append(popt[0] + popt[1])

        plt.show()

    print(zs)
    print(chis)
    plt.figure()
    ax11 = plt.subplot(111, projection='3d')
    ax11.scatter(data['eu.z'], data['eu.chi'], data['xspress3roi1'])
    ax11.plot(zs, chis, cts, color='orange')
    plt.show()

    plt.plot(chis, zs)
    plt.show()
