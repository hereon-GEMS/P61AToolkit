import h5py
import numpy as np
import pandas as pd
import os
import logging

from P61App import P61App


class P61ANexusReader:
    # define entries in nexus format
    ch0 = ('entry', 'instrument', 'xspress3', 'channel00')
    ch1 = ('entry', 'instrument', 'xspress3', 'channel01')
    all_event = ('scaler', 'allevent')
    all_good = ('scaler', 'allgood')
    time = ('scaler', 'time')
    hist = ('histogram', )
    # define column names for resulting table
    columns = ('DataX', 'DataY', 'DataID', 'Channel', 'ScreenName', 'Active', 'Color', 'DeadTime', 'CountTime', 'Cps')

    def __init__(self):
        self.q_app = P61App.instance()
        self.logger = logging.getLogger(str(self.__class__))

        self._replace = True

    def validate(self, f_name):
        hists = False
        try:
            with h5py.File(f_name, 'r') as f:
                hists |= '/'.join(self.ch0 + self.hist) in f
                hists |= '/'.join(self.ch1 + self.hist) in f
        except Exception:
            return False

        return hists

    def read(self, f_name, sum_frames=False):
        # define resulting data frame
        if self.q_app is not None:
            result = pd.DataFrame(columns=self.q_app.data.columns)
            sum_frames = self.q_app.get_merge_frames()
        else:
            result = pd.DataFrame(columns=self.columns)
        # process current nexus file
        with h5py.File(f_name, 'r') as f:
            # iterate over each channel
            for ii, channel in enumerate((self.ch0, self.ch1)):
                # if no frames existing
                if '/'.join(channel + self.hist) not in f:
                    continue
                # determine frames of measured intensity
                if sum_frames:
                    frames = [np.sum(f['/'.join(channel + self.hist)], axis=0)]
                else:
                    frames = f['/'.join(channel + self.hist)]
                # determine all events and all good events
                if ('/'.join(channel + self.all_event) in f) and ('/'.join(channel + self.all_good) in f):
                    if sum_frames:
                        allevent = np.sum(f['/'.join(channel + self.all_event)], axis=0)
                        allgood = np.sum(f['/'.join(channel + self.all_good)], axis=0)
                        time = np.sum(f['/'.join(channel + self.time)], axis=0)
                    else:
                        allevent = f['/'.join(channel + self.all_event)]
                        allgood = f['/'.join(channel + self.all_good)]
                        time = f['/'.join(channel + self.time)]
                # iterate over frames
                for fr_num, frame in enumerate(frames):
                    # reset intensities at low energies (noise) and at highest energy (unprocessed)
                    frame[:20] = 0.0
                    frame[-1] = 0.0
                    # corrections to NIST Pb and W lines
                    # calculation of energies
                    if ii == 0:
                        kev = np.arange(frame.shape[0]) * 0.050494483569344 + 0.029899315869827  # old
                        # kev = np.arange(frame.shape[0]) * 0.0502526643786186 + 0.0233578244744876  # 07.07.22
                    elif ii == 1:
                        kev = np.arange(frame.shape[0]) * 0.04995786201326 + 0.106286326963684  # old
                        # kev = np.arange(frame.shape[0]) * 0.0499765125529105 + 0.02579913996599  # 07.07.22
                    else:
                        kev = (np.arange(frame.shape[0]) + 0.5) * 5E-2
                    # only intensities >0 allowed
                    if self._replace:
                        frame[frame < 1.0] = 1.0
                    else:
                        self.logger.warning('NeXuS import filters out intensities <1 ct. '
                                            'Not all imported datasets have the same shape, this might bring unexpected'
                                            ' consequences!')
                        kev, frame = kev[frame >= 1.0], frame[frame >= 1.0]
                    # set values of row
                    if self.q_app is not None:
                        row = {c: None for c in self.q_app.data.columns}
                    else:
                        row = {c: None for c in self.columns}
                    if ('/'.join(channel + self.all_event) in f) and ('/'.join(channel + self.all_good) in f):
                        row.update({'DeadTime': 1. - allgood / allevent if sum_frames else 1. - allgood[fr_num] / allevent[fr_num]})
                    if '/'.join(channel + self.time) in f:
                        row.update({'CountTime': time * 1.25e-8 if sum_frames else time[fr_num] * 1.25e-8})
                        if '/'.join(channel + self.all_good) in f:
                            row.update({'Cps': allgood / (time * 1.25e-8) if sum_frames else allgood[fr_num] / (time[fr_num] * 1.25e-8)})

                    row.update({
                        'DataX': kev,
                        'DataY': frame,
                        'DataID': f_name + ':' + '/'.join(channel),
                        'Channel': ii,
                        'ScreenName': os.path.basename(f_name) + ':' + '%02d' % ii + ('' if sum_frames else ':%03d' % fr_num),
                        'Active': True,
                    })
                    if self.q_app is not None:
                        row.update({'Color': next(self.q_app.params['ColorWheel'])})
                    result.loc[result.shape[0]] = row
        # return result
        result = result.astype('object')
        result[pd.isna(result)] = None
        return result
