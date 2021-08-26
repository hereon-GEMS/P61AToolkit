import pandas as pd
import numpy as np
from uncertainties import ufloat

from py61a.viewer_utils import valid_peaks


def deviatoric_stresses(peaks: pd.DataFrame, s2p: pd.DataFrame, dec: pd.DataFrame):
    result = pd.DataFrame(
        np.nan,
        index=s2p.index,
        columns=pd.MultiIndex.from_product([
            set(s2p.columns.get_level_values(0)),
            ('s11-s33', 's22-s33', 'depth_min', 'depth_max', 'depth')])
    )

    for peak_id in valid_peaks(peaks, valid_for='sin2psi'):
        hkl = peaks[peak_id][['h', 'k', 'l']].mean().astype(np.int)

        for ii, row in dec.iterrows():
            if np.all(hkl == row[['h', 'k', 'l']].astype(np.int)):
                s1, hs2 = row['s1'], row['hs2']
                break
        else:
            print('WARNING: hkl %s not found in provided DEC dataset! consider adding it' % str(hkl.values))
            continue

        tmp = []
        if '0+180' in s2p[peak_id].columns:
            result.loc[:, (peak_id, 's11-s33')] = \
                (1. / hs2) * s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.uslope) / \
                s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.intercept)
            tmp.append(s2p.loc[:, (peak_id, '0+180')].to_numpy().reshape((-1, 1)))
        if '90+270' in s2p[peak_id].columns:
            result.loc[:, (peak_id, 's22-s33')] = \
                (1. / hs2) * s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uslope) / \
                s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.intercept)
            tmp.append(s2p.loc[:, (peak_id, '90+270')].to_numpy().reshape((-1, 1)))

        tmp = np.concatenate(tmp, axis=1)

        def func(x):
            res = []
            for el in x:
                res.append(el.depth)
            return np.concatenate(res)

        tmp = np.apply_along_axis(func, 1, tmp)

        result.loc[:, (peak_id, 'depth')] = np.mean(tmp, axis=1)
        result.loc[:, (peak_id, 'depth_min')] = np.min(tmp, axis=1)
        result.loc[:, (peak_id, 'depth_max')] = np.max(tmp, axis=1)

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
    for peak_id in valid_peaks(peaks, valid_for='sin2psi'):
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

        print(s1, hs2, d0_)


    return result
