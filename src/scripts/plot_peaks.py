from py61a.viewer_utils import read_peaks, valid_peaks, peak_id_str
from matplotlib import pyplot as plt
import numpy as np


if __name__ == '__main__':
    # dd = read_peaks(r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs\tut02_00001.csv')
    dd = read_peaks((r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aYscan_02000\Peaks_2ayscan.csv',
                    r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aZscan_01999\Peaks_2aZscan.csv'))
    print(dd.shape)
    x_mot = 'eu.chi'

    # custom selection rule
    # dd = dd[np.isclose(dd['md']['eu.phi'], 90., rtol=1e-2)]

    if x_mot in dd['md'].columns:
        dd.sort_values(by=('md', x_mot), inplace=True)
    else:
        raise KeyError('Motor %s is not present in the dataset' % x_mot)

    for peak_id in valid_peaks(dd, valid_for='phase'):

        plt.figure(peak_id_str(dd, peak_id))

        ax11 = plt.subplot(221)
        ax11.set_title('Height')
        ax11.errorbar(dd['md'][x_mot], dd[peak_id]['height'], yerr=dd[peak_id]['height_std'])
        ax11.set_xlabel(x_mot)
        ax11.set_ylabel('[cts]')

        ax12 = plt.subplot(222)
        ax12.set_title(r'$R_{wp}^2$, $\chi^2$')
        ax12.set_ylabel(r'$R_{wp}^2$', color='tab:red')
        ax12.plot(dd['md'][x_mot], dd[peak_id]['rwp2'], color='tab:red')
        ax12.tick_params(axis='y', labelcolor='tab:red')
        ax12_2 = ax12.twinx()
        ax12_2.set_ylabel(r'$\chi^2$', color='tab:blue')
        ax12_2.plot(dd['md'][x_mot], dd[peak_id]['chi2'], color='tab:blue')
        ax12_2.tick_params(axis='y', labelcolor='tab:blue')
        ax12.set_xlabel(x_mot)

        ax21 = plt.subplot(223)
        ax21.set_title('Center')
        ax21.errorbar(dd['md'][x_mot], dd[peak_id]['center'], yerr=dd[peak_id]['center_std'])
        ax21.set_xlabel(x_mot)
        ax21.set_ylabel('[keV]')

        ax22 = plt.subplot(224)
        ax22.set_title('Sigma')
        ax22.errorbar(dd['md'][x_mot], dd[peak_id]['sigma'], yerr=dd[peak_id]['sigma_std'])
        ax22.set_xlabel(x_mot)
        ax22.set_ylabel('[keV]')

        plt.tight_layout()

    plt.show()
