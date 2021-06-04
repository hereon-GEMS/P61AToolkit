import pandas as pd
import os


density = {  # g/cm3
    'Al': 2.7,
    'Cr': 7.19,
    'Fe': 7.874,
    'Mg': 1.738,
    'Ni': 8.9,
    'Ti': 4.506,
    'W': 19.28,
}

_wd = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'NIST_abs')
absorption = {  # for description and units see the .csv files
    element.replace('.csv', ''): pd.read_csv(os.path.join(_wd, element), comment='#')
    for element in filter(lambda x: '.csv' in x, os.listdir(_wd))
}
