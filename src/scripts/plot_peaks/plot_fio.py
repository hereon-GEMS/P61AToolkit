from py61a.beamline_utils import read_fio
from matplotlib import pyplot as plt


if __name__ == '__main__':
    f1 = r'..\..\..\data\peaks\TiLSP\phi0Trans_3_00041.fio'
    f2 = r'..\..\..\data\peaks\TiLSP\phi0Trans_4_00046.fio'
    header, data = read_fio(f1)

    plt.figure()
    ax = plt.subplot(111, projection='3d')
    ax.scatter(data['eu.z'], data['eu.chi'], data['xspress3roi1'])
    plt.show()