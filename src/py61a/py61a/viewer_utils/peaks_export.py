import pandas as pd
from typing import Union
from functools import reduce
import random
import string


def read_peaks(f_names: Union[str, list, tuple] = ()) -> pd.DataFrame:
    """
    Reads P61A::Viewer output files and combines them together.
    :param f_names: file path(s): a string or a tuple / list of strings
    :return: data as a pandas DataFrame
    """
    fake_prefixes = ('eh1', 'exp', 'xspress3')  # some motor names start with these + underscore, need

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

    data = reduce(lambda a, b: pd.concat((a, b), axis=0, ignore_index=True),
                  (pd.read_csv(pp, index_col=0) for pp in f_names))
    data.columns = pd.MultiIndex.from_tuples([get_prefix(col) for col in data.columns],
                                             names=['prefix', 'parameter'])

    return data


def valid_peaks(data: pd.DataFrame, valid_for: Union[str, None] = 'sin2psi'):
    """

    :param data:
    :param valid_for: sin2psi,
    :return:
    """
    columns_sin2psi = (
        '3gamma', 'h', 'k', 'l', 'phase',
        'amplitude', 'amplitude_std',
        'center', 'center_std',
        'height', 'height_std',
        'sigma', 'sigma_std',
        'width', 'width_std'
    )

    columns_hkl = (
        'h', 'k', 'l', 'phase',
    )

    prefixes = set(data.columns.get_level_values(0))

    try:
        prefixes.remove('md')
    except KeyError:
        pass

    if valid_for in ('sin2psi', 'phase'):
        if valid_for == 'sin2psi':
            nc = columns_sin2psi
        elif valid_for == 'phase':
            nc = columns_hkl

        invalid = set()

        for prefix in prefixes:
            if not all(x in data[prefix].columns for x in nc):
                invalid.update({prefix})

        for prefix in invalid:
            prefixes.remove(prefix)
    else:
        pass
    return list(prefixes)


def peak_id_str(data: pd.DataFrame, peak_id: str) -> str:
    try:
        return '%s [%d%d%d]' % (data[peak_id]['phase'].iloc[0],
                                *tuple(data[peak_id][['h', 'k', 'l']].mean().astype(int).tolist()))
    except Exception:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
