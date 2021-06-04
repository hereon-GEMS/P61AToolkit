import pandas as pd
import numpy as np
from itertools import permutations
from functools import reduce

from libraries.stress.separated import multiWavelengthAnalysis as multiWavelengthAnalysis2, \
    multiUniversalPlotAnalysis as multiUniversalPlotAnalysis2,\
    plotMultiWavelength, plotStrainFreeLatticeSpacing, plotStresses, plotUniversalPlot
from libraries.stress.reimplemented import sin2psi_analysis
from libraries.cryst_utils import bragg


if __name__ == '__main__':
    tth = 15.  # degrees
    a0 = 2.89  # AA
    density = 7.874  # g/cm3

    peaks_paths = [
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_1-4.csv',
    ]
    abs_path = r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\src\apps\Viewer\cryst_utils\NIST_abs\Fe.csv'
    dec_path = r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\dec\bccFe.csv'

    # reading all data
    dd = reduce(lambda a, b: pd.concat((a, b), axis=0, ignore_index=True),
                (pd.read_csv(pp, index_col=0) for pp in peaks_paths))

    paths1 = [
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\src\scripts\Scan1_CD_P61.dat',
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\src\scripts\Scan2_CD_P61.dat',
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\src\scripts\Scan3_CD_P61.dat',
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\src\scripts\Scan4_CD_P61.dat'
    ]

    dd = reduce(lambda a, b: pd.concat((a, b), axis=0, ignore_index=True),
                 (pd.read_csv(pp, sep='\t', skiprows=1) for pp in paths1))
    cols = [col for col in dd.columns if (('_dspac' in col) or('_s1' in col) or ('_hs2' in col) or ('_depth' in col))]
    dd = dd.drop(cols, axis=1)
    dd = dd.rename(columns={'chi': 'eu.chi', 'phi': 'eu.phi', 'psi': 'eu.psi', 'eta': 'eu.eta',
                            'x': 'eu.x', 'y': 'eu.y', 'z': 'eu.z'})
    dd = dd.rename(columns=lambda x: x if '_err' not in x else x.replace('_err', '_std'))
    dd['eu.chi'] = np.zeros(dd.shape[0])
    prefixes = set(col.split('_')[0] for col in dd.columns if 'center' in col)
    for prefix in prefixes:
        if '_'.join((prefix, 'h')) in dd.columns:
            dd['_'.join((prefix, 'phase'))] = ['Unknown'] * dd.shape[0]

    absorption = pd.read_csv(abs_path, comment='#')
    dec = pd.read_csv(dec_path, index_col=None, comment='#')

    # seeing which peaks we have
    prefixes = set(col.split('_')[0] for col in dd.columns if 'center' in col)

    # adding d-spacing columns to the peaks data
    for prefix in prefixes:
        dd['_'.join((prefix, 'dspac'))] = bragg(en=dd['_'.join((prefix, 'center'))], tth=tth)['d']

    # Angle and position calculation logic
    dd['chi'] = dd['eu.chi']
    dd['psi'] = dd['eu.psi']
    dd['phi'] = dd['eu.phi']
    dd['eta'] = 270.
    dd['x'] = dd['eu.x']
    dd['y'] = dd['eu.y']
    dd['z'] = dd['eu.z']
    dd = dd.drop(labels=['eu.chi', 'eu.phi', 'eu.psi', 'eu.eta', 'eu.x', 'eu.y', 'eu.z'], axis=1)

    # evaluating diffraction elastic constants (only valid for cubic lattices!!!)
    perms = pd.DataFrame(columns=dec.columns)
    for idx in dec.index:
        for h, k, l in set(permutations(dec.loc[idx, ['h', 'k', 'l']].to_numpy())):
            perms.loc[perms.shape[0]] = {'h': h, 'k': k, 'l': l,
                                         's1': dec.loc[idx, 's1'],
                                         'hs2': dec.loc[idx, 'hs2']}
    dec = perms

    # adding diffraction elastic constant columns to the peak data
    for prefix in prefixes:
        if '_'.join((prefix, 'h')) not in dd.columns:
            continue

        dd['_'.join((prefix, 's1'))] = [None] * dd.shape[0]
        dd['_'.join((prefix, 'hs2'))] = [None] * dd.shape[0]

        for idx in dd.index:
            h, k, l = dd.loc[idx, '_'.join((prefix, 'h'))], dd.loc[idx, '_'.join((prefix, 'k'))], \
                      dd.loc[idx, '_'.join((prefix, 'l'))]
            tmp = dec[(dec['h'] == h) & (dec['k'] == k) & (dec['l'] == l)]

            dd.loc[idx, '_'.join((prefix, 's1'))] = tmp['s1'].iloc[0]
            dd.loc[idx, '_'.join((prefix, 'hs2'))] = tmp['hs2'].iloc[0]

    # adding depth column to the peak data
    xs, ys = [], []
    for prefix in prefixes:
        lmi = np.interp(np.log(dd['_'.join((prefix, 'center'))]),
                        np.log(absorption['E'] * 1e3),
                        np.log(absorption['att']))
        mi = np.exp(lmi) * density  # cm^-1
        xs.append(1000 * dd['_'.join((prefix, 'center'))])
        ys.append(10000 / mi)
        tau = 10000 * ((np.sin(np.radians(tth / 2.)) ** 2) - (np.sin(np.radians(dd['psi'])) ** 2) +
                       (np.cos(np.radians(tth / 2.)) ** 2) * (np.sin(np.radians(dd['psi'])) ** 2) *
                       (np.sin(np.radians(dd['eta'])) ** 2)) / (2 * mi * np.sin(np.radians(tth / 2.)) *
                                                                np.cos(np.radians(dd['psi'])))
        dd['_'.join((prefix, 'depth'))] = tau  # mcm

    # dropping data that doesnt have phases assigned
    dd = dd.drop('ScreenName', axis=1)
    for prefix in prefixes:
        if '_'.join((prefix, 'phase')) in dd.columns:
            dd = dd.drop('_'.join((prefix, 'phase')), axis=1)
        else:
            for col in dd.columns:
                if prefix in col:
                    dd = dd.drop(col, axis=1)

    # my analysis implementation
    # dd['tth'] = [tth] * dd.shape[0]
    # dd['a0'] = a0 * dd.shape[0]
    # sin2psi_analysis(dd)

    # typecasting data for analysis
    dd = {col: dd[col].to_numpy(dtype=float) for col in dd.columns}
    dd['tth'] = tth
    dd['a0Val'] = a0 * 0.1

    # MWL
    resDataMwl, plotDataMwl = multiWavelengthAnalysis2(dd, 45)
    for k in plotDataMwl:
        print(k, plotDataMwl[k].keys())
    plotMultiWavelength(plotDataMwl, True)
    plotStrainFreeLatticeSpacing(resDataMwl, True)
    plotStresses(resDataMwl, True)

    # UP
    minDistPsiStar = 0.15
    minValPsiNormal = 0.08
    minValPsiShear = 0.8
    resDataUvp, resDataS33 = multiUniversalPlotAnalysis2(dd, 45, minDistPsiStar,
                                                         minValPsiNormal, minValPsiShear)
    plotUniversalPlot(resDataUvp, False)
    plotStrainFreeLatticeSpacing(resDataS33, False)
    plotStresses(resDataS33, False)
