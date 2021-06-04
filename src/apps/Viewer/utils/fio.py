import pandas as pd
import re


def read_fio(f_name):
    header = dict()
    data = pd.DataFrame()

    param_line = re.compile(r'^(?P<key>[\w\.]+) = (?P<val>[\d\.+-eE]+)\n')
    t_header_line = re.compile(r'^ Col (?P<col>[\d]+) (?P<key>[\w\.]+) (?P<type>[\w\.]+)\n')

    with open(f_name, 'r') as f:
        lines = f.readlines()

        for line in lines[lines.index('%p\n') + 1:]:
            m = param_line.match(line)
            if m:
                header[m.group('key')] = float(m.group('val'))

        if not header:
            return header, data

        columns = dict()
        for ii, line in enumerate(lines[lines.index('%d\n') + 1:]):
            m = t_header_line.match(line)
            if m:
                columns[int(m.group('col'))] = m.group('key')
            else:
                break

        if not columns:
            return header, data

        data = pd.DataFrame(columns=list(columns.values()))
        t_row_line = re.compile(r'^' + r'\s+([\d\.+-eE]+)' * len(columns) + r'\n')

        for line in lines[lines.index('%d\n') + ii + 1:]:
            m = t_row_line.match(line)
            if m is not None:
                vals = m.groups()
                row = {columns[i + 1]: float(vals[i]) for i in range(len(columns))}
                data.loc[data.shape[0]] = row

    return header, data


def write_fio(header, data, f_name):
    with open(f_name, 'w') as f:
        f.write('!\n! Parameter\n!\n%p\n')
        for k in header:
            f.write('%s = %f\n' % (k, header[k]))

        f.write('!\n! Data\n!\n%d\n')
        for ii, col in enumerate(data.columns):
            f.write(' Col %d %s DOUBLE\n' % (ii + 1, col))
        for ii in data.index:
            for col in data.columns:
                f.write(' %.03f' % data.loc[ii, col])
            f.write('\n')
        return True