from DatasetIO import P61AFioReader
from matplotlib import pyplot as plt
import os


if __name__ == '__main__':
    f_name = r'D:\degeners\Desktop\temp\Leoni\10mu_rot_0-180_3_06384.fio'
    data = P61AFioReader().read(f_name)
    # print(data)

    fig = plt.figure(os.path.basename(f_name))
    ax = fig.add_subplot(projection='3d')

    # plt.plot(data['eu.phi'], data['xspress3roi1'], '+')
    ax.scatter(data['eu.phi'], data['eu.chi'], data['xspress3roi1'], marker='+')
    plt.show()
