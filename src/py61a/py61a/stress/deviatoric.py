import pandas as pd
import numpy as np

from py61a.viewer_utils import valid_peaks


def deviatoric_stresses(peaks: pd.DataFrame, s2p: pd.DataFrame, dec: pd.DataFrame):
    result = pd.DataFrame(
        np.nan,
        index=s2p.index,
        columns=pd.MultiIndex.from_product([set(s2p.columns.get_level_values(0)), ('s11-s33', 's22-s33')])
    )

    for peak_id in valid_peaks(peaks, valid_for='sin2psi'): #set(s2p.columns.get_level_values(0)):
        hkl = peaks[peak_id][['h', 'k', 'l']].mean().astype(np.int)
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
                s2p.loc[:, (peak_id, '0+180')].apply(lambda x: x.intercept)
        if '90+270' in s2p[peak_id].columns:
            result.loc[:, (peak_id, 's22-s33')] = \
                (1. / hs2) * s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.uslope) / \
                s2p.loc[:, (peak_id, '90+270')].apply(lambda x: x.intercept)

    result = result.dropna(axis=1, how='all')
    return result