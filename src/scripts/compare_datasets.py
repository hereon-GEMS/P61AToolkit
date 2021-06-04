import pandas as pd
from functools import reduce
from matplotlib import pyplot as plt


if __name__ == '__main__':
    paths1 = [
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\Scan1_CD_P61.dat',
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\Scan2_CD_P61.dat',
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\Scan3_CD_P61.dat',
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\Scan4_CD_P61.dat'
    ]

    paths2 = [
        # r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_00001.csv',
        # r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_00002.csv',
        # r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_00003.csv',
        # r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_00004.csv',
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_1-4.csv',
    ]

    dd1 = reduce(lambda a, b: pd.concat((a, b), axis=0, ignore_index=True),
                 (pd.read_csv(pp, sep='\t', skiprows=1) for pp in paths1))
    dd2 = reduce(lambda a, b: pd.concat((a, b), axis=0, ignore_index=True),
                (pd.read_csv(pp, index_col=0) for pp in paths2))

    for phi in set(dd1['phi']).intersection(set(dd2['eu.phi'])):
        _dd1 = dd1[dd1['phi'] == phi]
        _dd2 = dd2[dd2['eu.phi'] == phi]

        plt.figure(phi)
        for prefix in set(col.split('_')[0] for col in dd2.columns if 'center' in col):
            plt.plot(_dd1['psi'], _dd1['_'.join((prefix, 'center'))] - _dd2['_'.join((prefix, 'center'))], label=prefix)
        plt.legend()
        plt.show()