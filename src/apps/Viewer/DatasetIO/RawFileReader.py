import numpy as np
import pandas as pd
import os
import struct

from P61App import P61App


class RawFileReader:
    """
    Validator here just checks that the file exists, so this one should go last on the list of readers
    """
    def __init__(self):
        self.q_app = P61App.instance()

    def validate(self, f_name):
        try:
            with open(f_name, 'rb') as f:
                return True
        except Exception:
            return False

    def read(self, f_name):
        int_size = 4  # bytes
        kev_per_bin = 1E-3
        result = pd.DataFrame(columns=self.q_app.data.columns)

        with open(f_name, 'rb') as f:
            _, _, _, nos = struct.unpack('hhhh', f.read(2 * int_size))
            event_size = 8 * int_size * nos

        with open(f_name, 'rb') as f:
            event = f.read(event_size)
            channels = dict()
            while event != b'':
                edep = int.from_bytes(event[8:10], byteorder='little')
                channel = event[1]
                if channel not in channels:
                    channels[channel] = [edep]
                else:
                    channels[channel].append(edep)
                event = f.read(event_size)

        for ch in channels:
            values, bins = np.histogram(channels[ch], bins=2 ** 16)
            bins = bins[:-1] + 0.5
            bins = bins[values != 0]
            values = values[values != 0]

            row = {c: None for c in self.q_app.data.columns}
            row.update({
                'DataX': kev_per_bin * bins,
                'DataY': values,
                'DataID': f_name + ':%02d' % ch,
                'ScreenName': os.path.basename(f_name) + ':%02d' % ch,
                'Active': True,
                'Color': next(self.q_app.params['ColorWheel'])
            })

            result.loc[result.shape[0]] = row

        return result
