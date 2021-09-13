import pandas as pd
import numpy as np
from uncertainties import ufloat, unumpy

from py61a.viewer_utils import get_peak_ids
from py61a.stress import hooke


def deviatoric_stresses(peaks: pd.DataFrame, s2p: pd.DataFrame, dec: pd.DataFrame):
    result = pd.DataFrame(
        np.nan,
        index=s2p.index,
        columns=pd.MultiIndex.from_product([
            set(s2p.columns.get_level_values(0)),
            ('s11-s33', 's22-s33', 'depth_min', 'depth_max', 'depth')])
    )

    # TODO: fix logic in column iteration. which columns are we looking up in which dataset?
    for peak_id in get_peak_ids(peaks, columns=('h', 'k', 'l', 'd', 'd_std')):
        hkl = peaks[peak_id][['h', 'k', 'l']].mean().astype(np.int)

        if peak_id not in s2p.columns.get_level_values(0):
            continue

        for ii, row in dec.iterrows():
            if np.all(hkl == row[['h', 'k', 'l']].astype(np.int)):
                s1, hs2 = row['s1'], row['hs2']
                break
        else:
            print('WARNING: hkl %s not found in provided DEC dataset! consider adding it' % str(hkl.values))
            continue

        if '0+180' in s2p[peak_id].columns:
            result.loc[:, (peak_id, 's11-s33')] = \
                (1. / hs2) * s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.uslope) / \
                s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.uintercept)
        else:
            result.loc[:, (peak_id, 's11-s33')] = ufloat(np.nan, np.nan)

        if '90+270' in s2p[peak_id].columns:
            result.loc[:, (peak_id, 's22-s33')] = \
                (1. / hs2) * s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uslope) / \
                s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uintercept)
        else:
            result.loc[:, (peak_id, 's22-s33')] = ufloat(np.nan, np.nan)

        result.loc[:, (peak_id, 'depth')] = np.nanmean(s2p[peak_id].applymap(lambda cell: np.nanmean(cell.depth)))
        result.loc[:, (peak_id, 'depth_min')] = np.nanmin(s2p[peak_id].applymap(lambda cell: np.nanmin(cell.depth)))
        result.loc[:, (peak_id, 'depth_max')] = np.nanmax(s2p[peak_id].applymap(lambda cell: np.nanmax(cell.depth)))

    result = result.dropna(axis=1, how='all')
    return result


def all_stresses(peaks: pd.DataFrame, s2p: pd.DataFrame, dec: pd.DataFrame, d0: pd.DataFrame):
    result = pd.DataFrame(
        np.nan,
        index=s2p.index,
        columns=pd.MultiIndex.from_product([
            set(s2p.columns.get_level_values(0)),
            ('s11', 's22', 's33', 's13', 's23', 's12', 'depth_min', 'depth_max', 'depth')])
    )
    for peak_id in get_peak_ids(peaks, columns=('h', 'k', 'l', 'center', 'center_std')):
        hkl = peaks[peak_id][['h', 'k', 'l']].mean().astype(np.int)

        for ii, row in dec.iterrows():
            if np.all(hkl == row[['h', 'k', 'l']].astype(np.int)):
                s1, hs2 = row['s1'], row['hs2']
                break
        else:
            print('WARNING: hkl %s not found in provided DEC dataset! consider adding it' % str(hkl.values))
            continue

        for ii, row in d0.iterrows():
            if np.all(hkl == row[['h', 'k', 'l']].astype(np.int)):
                d0_ = ufloat(row['d0'], row['d0_std'])
                break
        else:
            print('WARNING: d0 %s not found in provided dataset! consider adding it' % str(hkl.values))
            continue

        e11, e22, e33, e12, e13, e23 = np.array([np.nan] * result.shape[0]), np.array([np.nan] * result.shape[0]), \
                                       np.array([np.nan] * result.shape[0]), np.array([np.nan] * result.shape[0]), \
                                       np.array([np.nan] * result.shape[0]), np.array([np.nan] * result.shape[0])
        data_found = False
        if '0+180' in s2p[peak_id].columns:
            e11 = (s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.uslope) +
                   s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.uintercept) - d0_) / d0_
            e33 = (s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.uintercept) - d0_) / d0_
            data_found = True

        if '90+270' in s2p[peak_id].columns:
            e22 = (s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uslope) +
                   s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uintercept) - d0_) / d0_
            e33 = (s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uintercept) - d0_) / d0_
            data_found = True

        if ('0+180' in s2p[peak_id].columns) and ('90+270' in s2p[peak_id].columns):
            e33 = (0.5 * s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uintercept) +
                   0.5 * s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.uintercept) - d0_) / d0_
            data_found = True

        if '0-180' in s2p[peak_id].columns:
            e13 = s2p.loc[:, (peak_id, '0-180')].apply(lambda x: x.uslope) / d0_
            data_found = True

        if '90-270' in s2p[peak_id].columns:
            e23 = s2p.loc[:, (peak_id, '90-270')].apply(lambda x: x.uslope) / d0_
            data_found = True

        # TODO: e12 calculation

        if data_found:
            result.loc[:, (peak_id, 'depth')] = np.nanmean(s2p[peak_id].applymap(lambda cell: np.nanmean(cell.depth)))
            result.loc[:, (peak_id, 'depth_min')] = np.nanmin(s2p[peak_id].applymap(lambda cell: np.nanmin(cell.depth)))
            result.loc[:, (peak_id, 'depth_max')] = np.nanmax(s2p[peak_id].applymap(lambda cell: np.nanmax(cell.depth)))

            s = hooke(np.array([
                [e11, e12, e13],
                [e12, e22, e23],
                [e13, e23, e33]
            ]), s1, hs2)

            for i, j in ((0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)):
                if not all(np.isnan(unumpy.nominal_values(s[i, j]))):
                    result.loc[:, (peak_id, 's%d%d' % (i + 1, j + 1))] = s[i, j]

    result = result.dropna(axis=1, how='all')
    return result
