from py61a.viewer_utils import read_peaks, valid_peaks, peak_id_str
from matplotlib import pyplot as plt
import numpy as np


if __name__ == '__main__':
    dd = read_peaks((r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aYscan_02000\Peaks_2ayscan.csv',
                    r'Z:\p61\2021\data\11010463\raw\2a\experiments\2aZscan_01999\Peaks_2aZscan.csv'))

    dd = dd[dd['md']['eu.y'] < 30.]

    plt.plot(dd['md']['eu.chi'], label='eu.chi')
    plt.plot(dd['md']['eu.z'], label='eu.z')
    plt.plot(dd['md']['eu.y'], label='eu.y')
    plt.legend()
    plt.show()