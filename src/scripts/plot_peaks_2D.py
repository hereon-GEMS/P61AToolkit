from py61a.viewer_utils import read_peaks, valid_peaks, peak_id_str
from matplotlib import pyplot as plt


if __name__ == '__main__':
    dd = read_peaks((r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aYscan_02000\Peaks_2ayscan.csv',
                    r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aZscan_01999\Peaks_2aZscan.csv'))
    # dd = read_peaks(r'Z:\p61\2021\commissioning\c20210813_000_gaf_2s21\processed\com4pBending_fullScan_01712.csv')
    x_mot = 'eu.chi'
    y_mot = 'eu.z'

    # custom selection rule
    # dd = dd[np.isclose(dd['md']['eu.phi'], 90., rtol=1e-2)]

    for peak_id in valid_peaks(dd, valid_for='phase'):
        plt.figure(peak_id_str(dd, peak_id))

        ax11 = plt.subplot(221, projection='3d')
        ax11.scatter(dd['md'][x_mot], dd['md'][y_mot], dd[peak_id]['height'])
        ax11.set_title('Height')
        ax11.set_xlabel(x_mot)
        ax11.set_ylabel(y_mot)
        ax11.set_zlabel('[cts]')

        ax12 = plt.subplot(222, projection='3d')
        ax12.set_title(r'$R_{wp}^2$')
        ax12.set_ylabel(r'$R_{wp}^2$')
        ax12.scatter(dd['md'][x_mot], dd['md'][y_mot], dd[peak_id]['rwp2'])
        ax12.set_xlabel(x_mot)
        ax12.set_ylabel(y_mot)

        ax21 = plt.subplot(223, projection='3d')
        ax21.set_title('Center')
        ax21.scatter(dd['md'][x_mot], dd['md'][y_mot], dd[peak_id]['center'])
        ax21.set_xlabel(x_mot)
        ax21.set_ylabel(y_mot)
        ax21.set_zlabel('[keV]')

        ax22 = plt.subplot(224, projection='3d')
        ax22.set_title('Sigma')
        ax22.scatter(dd['md'][x_mot], dd['md'][y_mot], dd[peak_id]['sigma'])
        ax22.set_xlabel(x_mot)
        ax21.set_ylabel(y_mot)
        ax22.set_zlabel('[keV]')

        plt.tight_layout()

    plt.show()
