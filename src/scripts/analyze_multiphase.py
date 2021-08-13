# This script performs stress analysis on the output of the P61A::Viewer.
#
# The Viewer's data output format is a CSV file, where rows correspond to spectra, and the columns are (v. 1.0.0.):
# - ScreenName: name of the spectra, derived from .nxs file name and channel
# - Motor positions: eu.chi, eu.x, ...
# - Other metadata: petracurrent, temperatures, ...
# - Peak fit data. Each peak data column starts with a unique (per dataset) prefix: pv0, pv1, ...
#   (NOTE: while prefixes are unique, they are neither ordered nor have any indexing logic)
#   Peak data columns include:
#    - center, amplitude, height, sigma, width and standard deviations for them
#    - phase, h, k, l, 3gamma IF ASSIGNED during analysis in the Viewer. phase is just a string name, everything else
#      is necessary for the stress analysis. Peaks that do not have this info will be discarded.
#    - chi2, rwp2 fit quality metrics calculated per peak
# - Overall fit quality metrics (v. 1.0.0): Chi2
#
# In addition to the Viewer's output, the following data is necessary:
# - absorption data for the sample material
# - diffraction elastic constants for the phases

import pandas as pd
import numpy as np
from itertools import permutations
from functools import reduce

from py61a.stress.separated import multiWavelengthAnalysis as multiWavelengthAnalysis2, \
    multiUniversalPlotAnalysis as multiUniversalPlotAnalysis2,\
    plotMultiWavelength, plotStrainFreeLatticeSpacing, plotStresses, plotUniversalPlot
from py61a.cryst_utils import bragg, tau, mu

# columns that have to be present for every peak that is to be analysed
necessary_columns = (
    '3gamma', 'h', 'k', 'l', 'phase',
    'amplitude', 'amplitude_std',
    'center', 'center_std',
    'height', 'height_std',
    'sigma', 'sigma_std',
    'width', 'width_std'
)

if __name__ == '__main__':
    tth = 15.  # degrees
    a0 = 2.8403  # AA

    # path to the peak data export(s) from the Viewer
    peaks_paths = [
        r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\nxs\tut02_00001_true.csv'
        # r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_1-4.csv'
    ]

    # paths to absorption and DEC datasets
    abs_element_name = 'Fe'
    dec_path = r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\dec\bccFe.csv'

    # reading all data
    dd = reduce(lambda a, b: pd.concat((a, b), axis=0, ignore_index=True),
                (pd.read_csv(pp, index_col=0) for pp in peaks_paths))

    dd = dd.drop(['DeadTime', 'eu.psi'], axis=1, errors='ignore')

    # absorption = pd.read_csv(abs_path, comment='#')
    dec = pd.read_csv(dec_path, index_col=None, comment='#')

    # only selecting peaks that have all necessary_columns
    prefixes = set(col.split('_')[0] for col in dd.columns if 'center' in col)
    for prefix in prefixes:
        if not all('_'.join((prefix, col_name)) in dd.columns for col_name in necessary_columns):
            dd = dd.drop(list(filter(lambda x: (prefix + '_') in x, dd.columns)), axis=1)

    prefixes = set(col.split('_')[0] for col in dd.columns if 'center' in col)
    print(prefixes)

    # adding d-spacing columns to the peaks data
    for prefix in prefixes:
        dd['_'.join((prefix, 'dspac'))] = bragg(en=dd['_'.join((prefix, 'center'))], tth=tth)['d']

    # angle and position transformation from beamline motors to sample coordinates
    dd['chi'] = dd['eu.chi']
    dd['psi'] = dd['eu.chi']
    dd['phi'] = dd['eu.phi']
    dd['eta'] = 90.
    dd['x'] = dd['eu.x']
    dd['y'] = dd['eu.y']
    dd['z'] = dd['eu.z']
    dd = dd.drop(labels=['eu.chi', 'eu.phi', 'eu.x', 'eu.y', 'eu.z', 'eu.alp', 'eu.bet', 'eu.abc'], axis=1, errors='ignore')

    # evaluating diffraction elastic constants (only valid for cubic lattices!!!)
    perms = pd.DataFrame(columns=dec.columns)
    for idx in dec.index:
        for h, k, l in set(permutations(dec.loc[idx, ['h', 'k', 'l']].to_numpy())):
            perms.loc[perms.shape[0]] = {'h': h, 'k': k, 'l': l,
                                         's1': dec.loc[idx, 's1'],
                                         'hs2': dec.loc[idx, 'hs2']}
    dec = perms

    # Printing peaks, their phases and HKL
    for prefix in sorted(prefixes, key=lambda prefix: dd['_'.join((prefix, 'center'))].mean()):
        if '_'.join((prefix, 'h')) in dd.columns:
            print(prefix, '%.02f' % dd['_'.join((prefix, 'center'))].mean(),
                  dd['_'.join((prefix, 'phase'))].iloc[0],
                  '[%d %d %d]' % (
                  dd['_'.join((prefix, 'h'))].iloc[0].astype(int),
                  dd['_'.join((prefix, 'k'))].iloc[0].astype(int),
                  dd['_'.join((prefix, 'l'))].iloc[0].astype(int)
                  ))
        else:
            print(prefix, dd['_'.join((prefix, 'center'))].mean())

    # adding diffraction elastic constant columns to the peak data
    dec_missing = set([])
    for prefix in prefixes:
        dd['_'.join((prefix, 's1'))] = [None] * dd.shape[0]
        dd['_'.join((prefix, 'hs2'))] = [None] * dd.shape[0]

        h, k, l = dd['_'.join((prefix, 'h'))].iloc[0], dd['_'.join((prefix, 'k'))].iloc[0], \
                  dd['_'.join((prefix, 'l'))].iloc[0]
        tmp = dec[(dec['h'] == h) & (dec['k'] == k) & (dec['l'] == l)]

        if tmp.shape[0] > 0:
            dd.loc[:, '_'.join((prefix, 's1'))] = tmp['s1'].iloc[0]
            dd.loc[:, '_'.join((prefix, 'hs2'))] = tmp['hs2'].iloc[0]
        else:
            dd = dd.drop(list(filter(lambda x: (prefix + '_') in x, dd.columns)), axis=1)
            dec_missing.add((h, k, l))

    for hkl in dec_missing:
        print('DEC constants are missing a plane: [%d %d %d]' % hkl)

    prefixes = set(col.split('_')[0] for col in dd.columns if 'center' in col)

    # adding depth column to the peak data
    for prefix in prefixes:
        dd['_'.join((prefix, 'depth'))] = tau(mu=mu(el=abs_element_name, en=dd['_'.join((prefix, 'center'))]),
                                              tth=tth, psi=dd['psi'], eta=dd['eta'])
        print(dd[['_'.join((prefix, 'center')), 'psi', 'eta', 'phi', '_'.join((prefix, 'depth'))]])

    # separating data by phase
    dd_phases = dict()
    md = dd.drop(list(filter(lambda x: any(((prefix + '_') in x for prefix in prefixes)), dd.columns)), axis=1)
    for prefix in prefixes:
        if dd['_'.join((prefix, 'phase'))].iloc[0] not in dd_phases.keys():
            dd_phases[dd['_'.join((prefix, 'phase'))].iloc[0]] = md.copy()

        dd_phases[dd['_'.join((prefix, 'phase'))].iloc[0]] = pd.concat([
            dd_phases[dd['_'.join((prefix, 'phase'))].iloc[0]],
            dd[list(filter(lambda x: (prefix + '_') in x, dd.columns))]], axis=1
        )

    # dropping unnecessary columns, dropping NANs, and running the analysis
    for phase in dd_phases:
        pd.set_option('display.max_columns', None)
        print(dd_phases[phase])
        dd_phases[phase] = dd_phases[phase].drop(
            ['ScreenName', 'Channel', *['_'.join((prefix, 'phase')) for prefix in prefixes]], axis=1, errors='ignore')
        dd_phases[phase] = dd_phases[phase].dropna(axis=0)

        tmp = {col: dd_phases[phase][col].to_numpy(dtype=float) for col in dd_phases[phase].columns}
        tmp['tth'] = tth
        tmp['a0Val'] = a0 * 0.1

        # MWL
        resDataMwl, plotDataMwl = multiWavelengthAnalysis2(tmp, 45)
        for k in plotDataMwl:
            print(k, plotDataMwl[k].keys())
        plotMultiWavelength(plotDataMwl, showErr=False)
        plotStrainFreeLatticeSpacing(resDataMwl, showErr=False)
        plotStresses(resDataMwl, True)

        # UP
        # minDistPsiStar = 0.15
        # minValPsiNormal = 0.08
        # minValPsiShear = 0.8
        # resDataUvp, resDataS33 = multiUniversalPlotAnalysis2(tmp, 45, minDistPsiStar,
        #                                                      minValPsiNormal, minValPsiShear)
        # plotUniversalPlot(resDataUvp, False)
        # plotStrainFreeLatticeSpacing(resDataS33, False)
        # plotStresses(resDataS33, False)
