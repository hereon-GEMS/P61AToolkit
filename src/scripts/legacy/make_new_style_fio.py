#
# Author: Gleb Dovzhenko.
# This script takes the data and metadata stored by the old convention (before May 2021) and reorganizes it in
# accordance with the new convention.
#

import os
import shutil
import pandas as pd
import re
from py61a.beamline_utils import read_fio


if __name__ == '__main__':
    dd = r''  # where all the .nxs files are
    old_fio = os.path.join(dd, 'motpos.fio')  # name of the old style fio file
    rd = r''  # directory to save the results to
    mot_names = 'eu.chi', 'eu.phi'
    exp_name = 'sample01'

    header_old, data_old = read_fio(old_fio)

    def filter_fn(ff):
        m = re.findall(r'_([\w\.]+)_([\d\.+-eE]+)_([\w\.]+)_([\d\.+-eE]+)\.nxs', ff)
        if m is None:
            return None
        if all(map(lambda x: x in m[0], mot_names)):
            return {m[0][0]: m[0][1], m[0][2]: m[0][3]}
        else:
            return None

    f_names = dict()
    for f_name in filter(lambda x: x[-4:] == '.nxs', os.listdir(dd)):
        params = filter_fn(f_name)
        if params is not None:
            f_names[tuple(float(params[mn]) for mn in mot_names)] = f_name

    def add_xs_index(row):
        row['xspress3_index'] = row.name
        row['f_name'] = f_names[tuple(float(row[mn]) for mn in mot_names)]
        return row

    data = data_old.apply(add_xs_index, axis=1)

    if not os.path.exists(os.path.join(rd, exp_name + '_00001')):
        os.mkdir(os.path.join(rd, exp_name + '_00001'))

    for idx in data.index:
        # shutil.copyfile(
        #     os.path.join(dd, data.loc[idx, 'f_name']),
        #     os.path.join(rd, exp_name + '_00001', exp_name + '_%05d' % data.loc[idx, 'xspress3_index'] + '.nxs'),
        # )
        print(
            os.path.join(dd, data.loc[idx, 'f_name']), '->',
            os.path.join(rd, exp_name + '_00001', exp_name + '_%05d' % data.loc[idx, 'xspress3_index'] + '.nxs')
        )

    data = data.drop('f_name', axis=1)
    print(header_old)
    print(data)
    # write_fio(header_old, data, os.path.join(rd, exp_name + '_00001.fio'))
