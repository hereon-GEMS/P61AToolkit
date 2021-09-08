import pandas as pd
import numpy as np
from typing import Union, Iterable
from functools import reduce
import random
import string


def read_peaks(f_names: Union[str, list, tuple] = ()) -> pd.DataFrame:
    """
    Reads P61A::Viewer output files and combines them together.
    :param f_names: file path(s): a string or a tuple / list of strings
    :return: data as a pandas DataFrame
    """
    fake_prefixes = ('eh1', 'exp', 'xspress3')  # some motor names start with these + underscore

    def get_prefix(col_name: str) -> tuple:
        parts = col_name.split('_')
        if len(parts) == 1 or parts[0] in fake_prefixes:
            return 'md', col_name
        else:
            return parts[0], '_'.join(parts[1:])

    if isinstance(f_names, str):
        f_names = [f_names]

    if len(f_names) == 0:
        return pd.DataFrame()

    data = []
    for f_name in f_names:
        data.append(pd.read_csv(f_name, index_col=0))
        data[-1].columns = pd.MultiIndex.from_tuples([get_prefix(col) for col in data[-1].columns],
                                                     names=['prefix', 'parameter'])
    data = reduce(merge_peak_datasets, data)

    for peak in get_peak_ids(data, columns=('h', 'k', 'l', 'phase')):
        for k in ('h', 'k', 'l'):
            data.loc[:, (peak, k)] = data[peak][k].mean(skipna=True)
        phase = data[peak]['phase']
        phase = phase[~phase.isna()]
        data.loc[:, (peak, 'phase')] = phase.iloc[0]
    return data


def merge_peak_datasets(d1, d2):
    """
    :param d1:
    :param d2:
    :return:
    """
    def hkl_match(d1_, col1_, d2_, col2_):
        if ('h' not in d1_[col1_].columns) or \
           ('k' not in d1_[col1_].columns) or \
           ('l' not in d1_[col1_].columns) or \
           ('h' not in d2_[col2_].columns) or \
           ('k' not in d2_[col2_].columns) or \
           ('l' not in d2_[col2_].columns):
            return False
        else:
            return (d1_[col1_]['h'].mean().astype(np.int) == d2_[col2_]['h'].mean().astype(np.int)) and \
                   (d1_[col1_]['k'].mean().astype(np.int) == d2_[col2_]['k'].mean().astype(np.int)) and \
                   (d1_[col1_]['l'].mean().astype(np.int) == d2_[col2_]['l'].mean().astype(np.int))

    def next_prefix(px_, pxs_):
        i, idx = -1, 0
        while i > -len(px_):
            try:
                idx = int(px_[i:])
            except ValueError:
                i += 1
                break
            i -= 1

        while True:
            idx += 1
            if (px_[:i] + str(idx)) not in pxs_:
                return px_[:i] + str(idx)

    known_prefixes = set(d2.columns.get_level_values(0))
    known_prefixes.update(set(d1.columns.get_level_values(0)))
    known_prefixes.remove('md')
    d2_lvl0_mapping = dict()

    for col2 in set(d2.columns.get_level_values(0)):
        if col2 == 'md':
            continue

        match = False

        for col1 in set(d1.columns.get_level_values(0)):
            if hkl_match(d1, col1, d2, col2):
                match = True
                break

        if match:
            d2_lvl0_mapping[col2] = col1
        else:
            if col2 in d1.columns.get_level_values(0):
                d2_lvl0_mapping[col2] = next_prefix(col2, known_prefixes)
                known_prefixes.add(d2_lvl0_mapping[col2])

    d2_lvl0_mapping['md'] = 'md'
    d2 = d2.rename(columns=d2_lvl0_mapping)
    d1.sort_index(inplace=True, axis=1)
    d2.sort_index(inplace=True, axis=1)
    d2.index = d2.index + d1.shape[0]

    return pd.concat((d1, d2), axis=0)


def get_peak_ids(data: pd.DataFrame, columns: Iterable[str]):
    prefixes = set(data.columns.get_level_values(0))

    for special_key in ('md', 'scanpts'):
        if special_key in prefixes:
            prefixes.remove(special_key)

    invalid = set()
    for col in columns:
        for px in prefixes:
            if col not in data[px].columns:
                invalid.update({px})

    return list(prefixes - invalid)


def peak_id_str(data: pd.DataFrame, peak_id: str) -> str:
    if ('h' in data[peak_id].columns) and ('k' in data[peak_id].columns) and ('l' in data[peak_id].columns):
        hh, kk, ll = data[peak_id][['h', 'k', 'l']].mean().astype(int)
    else:
        hh, kk, ll = None, None, None

    if 'phase' in data[peak_id].columns:
        phase = data[peak_id]['phase'].iloc[0]
    else:
        phase = None

    if phase is None and hh is None and kk is None and ll is None:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    elif phase is None and hh is not None and kk is not None and ll is not None:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + \
               ' [%d%d%d]' % (hh, kk, ll)
    else:
        return '%s [%d%d%d]' % (phase, hh, kk, ll)


def group_by_motors(data: pd.DataFrame, motors: Union[tuple, list]) -> pd.DataFrame:
    """

    :param data:
    :param motors: list or tuple of dictionaries. Example:
    [{'mot_name': 'eu.z', 'atol': None, 'rtol': 1e-1, 'values': None},
    {'mot_name': 'eu.phi', 'atol': 5., 'rtol': None, 'values': (0, 90, 180, 270)}]
    :return:
    """
    _possible_keys = ('mot_name', 'atol', 'rtol', 'values', 'min', 'max', 'new_name')

    for mt in motors:
        result = np.zeros(data.shape[0]) - 1

        if 'atol' in mt.keys():
            atol = mt['atol']
        else:
            atol = 1.e-8

        if 'rtol' in mt.keys():
            rtol = mt['rtol']
        else:
            rtol = 1.e-5

        if 'min' in mt.keys():
            min_val = mt['min']
        else:
            min_val = -np.inf

        if 'max' in mt.keys():
            max_val = mt['max']
        else:
            max_val = np.inf

        if 'values' in mt.keys():
            unique_values = np.array(mt['values'])
        else:
            ii, unique_values = 0, np.array(data[('md', mt['mot_name'])]).copy()

            while ii < unique_values.size:
                unique_values = unique_values[
                    (~np.isclose(unique_values, unique_values[ii], atol=atol, rtol=rtol)) |
                    (np.arange(0, unique_values.size) == ii)
                    ]
                ii += 1

        unique_values = unique_values[(unique_values < max_val) & (unique_values > min_val)]
        unique_values = np.sort(unique_values)
        for ii, val in enumerate(unique_values):
            result[np.isclose(val, data[('md', mt['mot_name'])].to_numpy(), atol=atol, rtol=rtol)] = ii

        if 'new_name' not in mt:
            data[('scanpts', mt['mot_name'])] = result.astype(np.int)
        else:
            data[('scanpts', mt['new_name'])] = result.astype(np.int)

    return data
