import re
import os
import pandas as pd
import numpy as np
import logging
from collections import defaultdict
from PyQt5.QtWidgets import QFileDialog

from P61App import P61App
from DatasetIO.P61ANexusReader import P61ANexusReader


class P61AFioReader:

    def __init__(self):
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

    def validate(self, f_name):
        return '.fio' in f_name

    def read(self, f_name):
        param_line = re.compile(r'^(?P<key>[\w\.]+) = (?P<val>[\d\.+-eE]+)\n')
        t_header_line = re.compile(r'^ Col (?P<col>[\d]+) (?P<key>[\w\.]+) (?P<type>[\w\.]+)\n')

        with open(f_name, 'r') as f:
            lines = f.readlines()

            static_motpos = dict()
            for line in lines[lines.index('%p\n') + 1:]:
                m = param_line.match(line)
                if m:
                    static_motpos[m.group('key')] = float(m.group('val'))

            if not static_motpos:
                self.logger.info('read: No motor positions found in file %s' % f_name)

            columns = dict()
            for ii, line in enumerate(lines[lines.index('%d\n') + 1:]):
                m = t_header_line.match(line)
                if m:
                    columns[int(m.group('col'))] = m.group('key')
                else:
                    break

            if not columns:
                self.logger.error('read: No table header found in file %s, giving up' % f_name)
                return pd.DataFrame(columns=self.q_app.data.columns)

            metadata = pd.DataFrame(columns=list(columns.values()) + list(static_motpos.keys()))
            # t_row_line = re.compile(r'^' + r'\s+([\d\.+-eE]+)' * len(columns) + r'\n')
            t_row_line = re.compile(r'^' + r'\s+([\w\.+-]+)' * len(columns) + r'\n')

            def _float(s):
                try:
                    return float(s)
                except ValueError:
                    return np.nan

            for line in lines[lines.index('%d\n') + ii + 1:]:
                m = t_row_line.match(line)
                if m is not None:
                    vals = m.groups()
                    row = static_motpos.copy()
                    row.update({columns[i + 1]: _float(vals[i]) for i in range(len(columns))})
                    metadata.loc[metadata.shape[0]] = row

            if 'xspress3_index' not in metadata.columns:
                self.logger.error('read: FIO files without xspress3_index column are not supported, giving up')
                return pd.DataFrame(columns=self.q_app.data.columns)
            else:
                metadata = metadata.astype({'xspress3_index': 'int'})

            if metadata.shape[0] > 0:
                self.logger.info('read: Metadata from %s extracted' % f_name)
            else:
                self.logger.error('read: No table data found in file %s, giving up' % f_name)
                return pd.DataFrame(columns=self.q_app.data.columns)

            dd = os.path.join(os.path.dirname(f_name), os.path.basename(f_name).replace('.fio', ''))
            if not os.path.exists(dd):
                self.logger.error('read: Data directory %s does not exist, requesting' % dd)
                fd = QFileDialog()
                dd = fd.getExistingDirectory(
                    None,
                    'Data directory for %s' % os.path.basename(f_name),
                    os.path.dirname(f_name),
                    options=QFileDialog.Options()
                    )

            fs_to_open = dict()
            f_ids = list(metadata['xspress3_index'])
            prefix = '_'.join(os.path.basename(f_name).split('_')[:-1])
            nxs_f_name = re.compile('(?P<prefix>' + prefix + r'|[\w]+)_(?P<idx>[\d]+).nxs')

            for ff in os.listdir(dd):
                m = nxs_f_name.match(ff)
                if m:
                    pfx, idx = m.group('prefix'), int(m.group('idx'))
                    if idx in f_ids:
                        f_ids.remove(idx)
                        if pfx != prefix:
                            self.logger.error(
                                'read: %s xspress3_index matches %s, but the prefix does not, opening anyway' %
                                (ff, os.path.basename(f_name)))
                        fs_to_open[idx] = os.path.join(dd, ff)
            if f_ids:
                self.logger.error(
                    'read: Found no matches in %s for xspress3_index %s' % (dd, str(f_ids)))

            result = pd.DataFrame(columns=('FNames', 'Motors'))
            for idx, row in metadata.iterrows():
                md = defaultdict(lambda: None)
                md.update(metadata.loc[idx].to_dict().items())
                ks = set(md.keys())
                for k in ks:
                    if np.isnan(md[k]):
                        md[k] = None
                result.loc[result.shape[0]] = {'FNames': fs_to_open[int(row['xspress3_index'])], 'Motors': md.copy()}
            return result
