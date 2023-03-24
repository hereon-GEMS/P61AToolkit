import h5py
import numpy as np
import pandas as pd
import os
from time import sleep, localtime, strftime

# import basics.functions as bf
# import basics.filehandling as fg
# import diffraction.filehandling as fs


# implementation based on Gleb
class P61ANexusHandler:
    # linear energy calibration for ch0 and ch1 (but given as quadratic coefficients)
    # calib = np.array([[0, 0.0505, -0.1], [0, 0.0499999999999995, -0.0249999999990678]])
    # based on P61AToolkit
    # calib = np.array([[0, 0.050494483569344, 0.029899315869827], [0, 0.04995786201326, 0.106286326963684]])
    # 07.07.22
    calib = np.array([[0, 0.0502526643786186, 0.0233578244744876], [0, 0.0499765125529105, 0.02579913996599]])
    # linear dead time calibration for ch0 and ch1 only based on first Fe measurements with different graphite plates
    # dtcalib = np.array([[2.50101945306792E-06, 0.0163784591685192], [0.0000056494547880336, 0.0379388442097675]])
    # quadratic dead time calibration for ch0 and ch1 based on both Fe measurements with different graphite plates
    dtcalib = np.array([[2.6927340476936e-14, 2.48127889225408e-06, 0.0224972569377339],
                        [-2.21978987294787e-13, 5.96715902282922e-06, -0.0320589089676879]])
    # define entries in nexus format
    ch0 = ('entry', 'instrument', 'xspress3', 'channel00')
    ch1 = ('entry', 'instrument', 'xspress3', 'channel01')
    hist = 'histogram'
    scaler = 'scaler'
    all_event = 'allevent'
    all_good = 'allgood'
    in_window0 = 'inwindow0'
    in_window1 = 'inwindow1'
    pileup = 'pileup'
    reset_counts = 'resetcounts'
    reset_ticks = 'resetticks'
    time = 'time'
    total_ticks = 'totalticks'
    scaler_items = (all_event, all_good, in_window0, in_window1, pileup, reset_counts, reset_ticks, time, total_ticks)
    # define column names for raw data table
    rawcols = ('file', 'channel', hist, *scaler_items)
    # define column names for resulting table
    columns = ('DataX', 'DataY', 'DataID', 'Channel', 'ScreenName', 'Active', 'Color', 'DeadTime', 'CountTime')

    def __init__(self):
        self.q_app = None
        self._replace = True
        # # read calibration values from ini file
        # calibData = fg.dlmread('P61A_detector.ini', usedCols=(1, 2, 3))
        # self.calib = calibData[0:2, :]
        # self.dtcalib = calibData[2:, :]

    def validate(self, f_name):
        hists = False
        try:
            with h5py.File(f_name, 'r') as f:
                hists |= '/'.join((*self.ch0, self.hist)) in f
                hists |= '/'.join((*self.ch1, self.hist)) in f
        except Exception:
            return False

        return hists

    def read(self, f_name=None, accum_frames='sum', extract=True):
        # accum_frames: 'none', 'sum', 'mean', 'median', 'max', 'min'
        # kev_per_bin = 5E-2  # default
        # define resulting data frame
        if extract:
            if self.q_app is not None:
                result = pd.DataFrame(columns=self.q_app.data.columns)
                if self.q_app.get_merge_frames():
                    accum_frames = 'sum'
                else:
                    accum_frames = 'none'
            else:
                result = pd.DataFrame(columns=self.columns)
        else:
            result = pd.DataFrame(columns=self.rawcols)
        # select nexus files
        # if f_name is None:
        #     f_name = fg.requestFiles((("Nexus files", "*.nxs"),), "Select P61A file", "off")
        # try to process current nexus file
        with h5py.File(f_name, 'r') as f:
            # iterate over each channel
            for ii, channel in enumerate((self.ch0, self.ch1)):
                # if no frames existing
                if '/'.join((*channel, self.hist)) not in f:
                    continue
                # determine frames of measured intensity
                frames = f['/'.join((*channel, self.hist))]
                if accum_frames == 'sum':
                    frames = [np.sum(frames, axis=0)]
                elif accum_frames == 'mean':
                    frames = [np.mean(frames, axis=0)]
                elif accum_frames == 'median':
                    frames = [np.median(frames, axis=0)]
                elif accum_frames == 'max':
                    frames = [np.max(frames, axis=0)]
                elif accum_frames == 'min':
                    frames = [np.min(frames, axis=0)]
                # determine scaler values
                scaler_values = pd.DataFrame(columns=self.rawcols[3:])
                for scaler_val in self.scaler_items:
                    if '/'.join((*channel, self.scaler, scaler_val)) in f:
                        scaler_values[scaler_val] = f['/'.join((*channel, self.scaler, scaler_val))]
                if accum_frames == 'sum':
                    scaler_values = scaler_values.sum()
                elif accum_frames == 'mean':
                    scaler_values = scaler_values.mean()
                elif accum_frames == 'median':
                    scaler_values = scaler_values.median()
                elif accum_frames == 'max':
                    scaler_values = scaler_values.max()
                elif accum_frames == 'min':
                    scaler_values = scaler_values.min()
                # iterate over frames
                for fr_num, frame in enumerate(frames):
                    if extract:
                        # reset intensities at low energies (noise) and at highest energy (unprocessed)
                        frame[:20] = 0.0
                        frame[-1] = 0.0
                        # corrections to NIST Pb and W lines
                        # calculation of energies
                        # kev = np.arange(frames.shape[0]) * kev_per_bin
                        # if ii == 0:
                        #     kev = np.arange(frames.shape[0]) * 0.050494483569344 + 0.029899315869827
                        # elif ii == 1:
                        #     kev = np.arange(frames.shape[0]) * 0.04995786201326 + 0.106286326963684
                        # else:
                        #     kev = (np.arange(frames.shape[0]) + 0.5) * kev_per_bin
                        ch_vals = np.arange(frame.shape[0]) + 1  # index starting at 1
                        kev = self.calib[ii, 0] * ch_vals ** 2 + self.calib[ii, 1] * ch_vals + self.calib[ii, 2]
                        # only intensities >0 allowed
                        if self._replace:
                            frame[frame < 1.0] = 1.0
                        else:
                            # self.logger.warning('NeXuS import filters out intensities < 1 ct. '
                            #     'Not all imported datasets have the same shape, this might bring unexpected '
                            #     'consequences!')
                            kev, frame = kev[frame >= 1.0], frame[frame >= 1.0]
                        # set values of row
                        if self.q_app is not None:
                            row = {c: None for c in self.q_app.data.columns}
                        else:
                            row = {c: None for c in self.columns}
                        if accum_frames == 'sum' or accum_frames == 'mean' or accum_frames == 'median' or \
                                accum_frames == 'max' or accum_frames == 'min':
                            file_id = ''
                        else:
                            file_id = ':%03d' % fr_num
                        # determine count time, reset ticks and dead time
                        if self.time in scaler_values and self.reset_ticks in scaler_values:
                            if accum_frames == 'sum' or accum_frames == 'mean' or accum_frames == 'median' or \
                                    accum_frames == 'max' or accum_frames == 'min':
                                ct_sec = scaler_values[self.time] * 1.25e-8
                                dt_x = scaler_values[self.reset_ticks] / ct_sec
                            else:
                                ct_sec = scaler_values[self.time][fr_num] * 1.25e-8
                                dt_x = scaler_values[self.reset_ticks][fr_num] / ct_sec
                            row.update({'CountTime': ct_sec})
                            row.update({'DeadTime': self.dtcalib[ii, 0] * dt_x ** 2 + self.dtcalib[ii, 1] * dt_x +
                                                    self.dtcalib[ii, 2]})
                        # if self.all_event in scaler_values and self.all_good in scaler_values:
                        #     row.update({'DeadTime':
                        #                 (1. - scaler_values[self.all_good] / scaler_values[self.all_event]) * 100})
                        row.update({
                            'DataX': kev,
                            'DataY': frame,
                            'DataID': f_name + ':' + '/'.join(channel),
                            'Channel': ii,
                            'ScreenName': os.path.basename(f_name) + ':' + '%02d' % ii + file_id,
                            'Active': True,
                        })
                        if self.q_app is not None:
                            row.update({'Color': next(self.q_app.params['ColorWheel'])})
                    else:
                        row = {c: None for c in self.rawcols}
                        # set values of row
                        row.update({'file': f_name, 'channel': ii, 'histogram': frame})
                        if accum_frames == 'sum' or accum_frames == 'mean' or accum_frames == 'median' or \
                                accum_frames == 'max' or accum_frames == 'min':
                            row.update(dict(scaler_values))
                        else:
                            row.update(dict(scaler_values.iloc[fr_num]))
                    result.loc[result.shape[0]] = row
        # except Exception:  # exception cause of invalid file (e.g. empty file when measurement interrupted)
        #     print('Problem with file: ' + f_name)
        #     return None
        # return result
        if extract:
            result = result.astype('object')
            result[pd.isna(result)] = None
        return result

    def write(self, f_name, data0=None, data1=None):
        with h5py.File(f_name, 'w') as f:
            if data0 is not None:
                f.create_dataset('/'.join((*self.ch0, self.hist)), data=np.array(list(data0[self.hist])),
                                 dtype=np.int32)
                for scaler_val in self.scaler_items:
                    if scaler_val in data0:
                        f.create_dataset('/'.join((*self.ch0, self.scaler, scaler_val)),
                                         data=data0[scaler_val].to_numpy(dtype=np.float32))
            if data1 is not None:
                f.create_dataset('/'.join((*self.ch1, self.hist)), data=np.array(list(data1[self.hist])),
                                 dtype=np.int32)
                for scaler_val in self.scaler_items:
                    if scaler_val in data1:
                        f.create_dataset('/'.join((*self.ch1, self.scaler, scaler_val)),
                                         data=data1[scaler_val].to_numpy(dtype=np.float32))

    def writeData(self, f_name, hist0=None, hist1=None, scaler0=None, scaler1=None):
        with h5py.File(f_name, 'w') as f:
            if hist0 is not None:
                f.create_dataset('/'.join((*self.ch0, self.hist)), data=hist0, dtype=np.int32)
            if scaler0 is not None:
                for scaler_val in self.scaler_items:
                    if scaler_val in scaler0:
                        f.create_dataset('/'.join((*self.ch0, self.scaler, scaler_val)), data=scaler0[scaler_val],
                                         dtype=np.float32)
            if hist1 is not None:
                f.create_dataset('/'.join((*self.ch1, self.hist)), data=hist1, dtype=np.int32)
            if scaler1 is not None:
                for scaler_val in self.scaler_items:
                    if scaler_val in scaler1:
                        f.create_dataset('/'.join((*self.ch1, self.scaler, scaler_val)), data=scaler1[scaler_val],
                                         dtype=np.float32)

    def convertText(self, files=None, accum_frames='sum', differentOutputFolder=True, extract=True, selFolder=False,
                    recursive=False):
        # accum_frames: 'none', 'sum', 'mean', 'median', 'max', 'min'
        # differentOutputFolder = False
        # select nexus files
        # if files is None:
        #     if selFolder:
        #         pathName = fg.requestDirectory(dialogTitle='Select folder of spectra files')
        #         files = fg.fileSearch(pathName, '*.nxs', recursive)
        #     else:
        #         files = fg.requestFiles((("Nexus files", "*.nxs"),), "Select P61A file", "on")
        #         pathName, _ = fg.fileparts(files[0])
        pathName, _ = os.path.split(files[0])
        # read all data from selected files
        handler = P61ANexusHandler()
        if extract:
            data = pd.DataFrame(columns=handler.columns)
        else:
            data = pd.DataFrame(columns=handler.rawcols)
        for f_name in files:
            data = pd.concat((data, handler.read(f_name, accum_frames, extract)), ignore_index=True)
        # select output folder if wanted
        # if differentOutputFolder:
        #     outputPath = fg.requestDirectory(dialogTitle='Select output folder', folder=pathName)
        # else:
        #     outputPath = pathName
        # export data to spectrum files
        if accum_frames == 'mean' or accum_frames == 'median' or accum_frames == 'max' or accum_frames == 'min':
            accumType = '_' + accum_frames
        else:  # sum or none
            accumType = ''
        for i in range(data.shape[0]):
            curData = data.iloc[i]
            if extract:
                header = ['SCREEN_NAME=' + curData['ScreenName'], 'CHANNEL=' + str(curData['Channel']),
                          'DEADTIME=' + str(curData['DeadTime']), 'TREAL=' + str(curData['CountTime']),
                          'SPECTRTXT=' + str(len(curData['DataX']))]
                vals = np.transpose([curData['DataX'], curData['DataY']])
                resFile = pathName + '/' + curData['ScreenName'].replace('.nxs', '').replace(':', '_') + accumType + '.txt'
            else:
                header = [scaler_val + '=' + str(curData[scaler_val]) for scaler_val in self.scaler_items]
                vals = np.transpose([np.arange(curData[self.hist].shape[0]) + 1, curData[self.hist]])
                if accum_frames != 'mean' and accum_frames != 'median' and accum_frames != 'max' and \
                        accum_frames != 'min' and accum_frames != 'sum':
                    accumType = '_%03d' % i
                _, file = os.path.split(curData['file'])
                resFile = pathName + '/' + file.replace('.nxs', '') + '_%02d_' % curData['channel'] + \
                          'raw' + accumType + '.txt'
            fid = open(resFile, 'w')
            for h in range(len(header)):
                fid.write('%s\n' % (header[h]))
            np.savetxt(fid, vals, delimiter='\t', newline=os.linesep, fmt='%g')
            fid.close()

    def accumSpectra(self, resFile=None, files=None, accum_frames='sum', method='sum', extract=True, dataDelim='\t',
                     headerLines=True, selFolder=False, recursive=False):
        # accum_frames: 'sum', 'mean', 'median', 'max', 'min'
        if accum_frames != 'sum' and accum_frames != 'mean' and accum_frames != 'median' and accum_frames != 'max' \
                and accum_frames != 'min':
            accum_frames = 'sum'
        # method: 'sum', 'mean', 'max', 'min'
        # default return values and parameter
        results = None
        header = []
        # select nexus files
        # if files is None:
        #     if selFolder:
        #         pathName = fg.requestDirectory(dialogTitle='Select folder of spectra files')
        #         files = fg.fileSearch(pathName, '*.nxs', recursive)
        #     else:
        #         files = fg.requestFiles((("Nexus files", "*.nxs"),), "Select P61A file", "on")
        #         pathName, _ = fg.fileparts(files[0])
        # read all data from selected files
        handler = P61ANexusHandler()
        for f_name in files:
            data = handler.read(f_name, accum_frames, extract)
            if extract:
                if results is None:
                    # initialize values if not existing
                    results = np.transpose([data['DataX'], data['DataY']])
                    treal = data['CountTime'].to_numpy()
                    dt = data['DeadTime'].to_numpy()
                else:
                    # get current live and real time
                    trealCur = data['CountTime'].to_numpy()
                    dtCur = data['DeadTime'].to_numpy()
                    # update values
                    if method == 'sum' or method == 'mean':
                        results[:, 1] = results[:, 1] + data['DataY'].to_numpy()
                        treal = treal + trealCur
                        dt = dt + dtCur
                    elif method == 'max':
                        results[:, 1] = np.max((results[:, 1], data['DataY'].to_numpy()), axis=0)
                        treal = np.max((treal, trealCur))
                        dt = np.max((dt, dtCur))
                    elif method == 'min':
                        results[:, 1] = np.min((results[:, 1], data['DataY'].to_numpy()), axis=0)
                        treal = np.min((treal, trealCur))
                        dt = np.min((dt, dtCur))
            else:
                if results is None:
                    # initialize values if not existing
                    results = data
                else:
                    # update values
                    if method == 'sum' or method == 'mean':
                        results[self.hist] = results[self.hist] + data[self.hist]
                        for scaler_val in self.scaler_items:
                            results[scaler_val] = results[scaler_val] + data[scaler_val]
                    elif method == 'max':
                        results[self.hist] = np.max((results[self.hist], data[self.hist]))
                        for scaler_val in self.scaler_items:
                            results[scaler_val] = np.max((results[scaler_val], data[scaler_val]))
                    elif method == 'min':
                        results[self.hist] = np.min((results[self.hist], data[self.hist]))
                        for scaler_val in self.scaler_items:
                            results[scaler_val] = np.min((results[scaler_val], data[scaler_val]))
        if method == 'mean':
            if extract:
                results[:, 1] = results[:, 1] / len(files)
                treal = treal / len(files)
                dt = dt / len(files)
            else:
                results[self.hist] = results[self.hist] / len(files)
                for scaler_val in self.scaler_items:
                    results[scaler_val] = results[scaler_val] / len(files)
        # if result file is not specified request file name
        # if resFile is None or len(resFile) == 0:
        #     resFile = fg.requestSaveFile(dialogTitle='Specify result file name')
        # write result file
        if len(resFile) > 0:
            if '.nxs' in resFile:
                if extract:
                    handler.writeData(resFile, results[0][1], results[1][1],
                                      {self.time: treal[0], self.total_ticks: treal[0]},
                                      {self.time: treal[1], self.total_ticks: treal[1]})
                else:
                    handler.write(resFile, results[results['channel'] == 0], results[results['channel'] == 1])
            else:  # elif '.txt' in resFile:
                if headerLines:
                    fid0 = open(resFile.replace('.txt', '_00.txt'), 'w')
                    fid1 = open(resFile.replace('.txt', '_01.txt'), 'w')
                    if extract:
                        header0 = ['DATE=' + strftime('%d-%m-%Y', localtime()), 'TIME=' + strftime('%H:%M:%S', localtime()),
                                   'DEADTIME=' + str(dt[0]), 'TREAL=' + str(treal[0]),
                                   'SPECTRTXT=' + str(len(results[0][0]))]
                        header1 = ['DATE=' + strftime('%d-%m-%Y', localtime()), 'TIME=' + strftime('%H:%M:%S', localtime()),
                                   'DEADTIME=' + str(dt[1]), 'TREAL=' + str(treal[1]),
                                   'SPECTRTXT=' + str(len(results[1][0]))]
                    else:
                        header0 = [scaler_val + '=' + str(results[results['channel'] == 0][scaler_val].array[0])
                                   for scaler_val in self.scaler_items]
                        header1 = [scaler_val + '=' + str(results[results['channel'] == 1][scaler_val].array[0])
                                   for scaler_val in self.scaler_items]
                    for i in range(len(header0)):
                        fid0.write(('%s\n' % (header0[i])))
                    for i in range(len(header1)):
                        fid1.write(('%s\n' % (header1[i])))
                if extract:
                    np.savetxt(fid0, np.transpose(np.array(list(results[0]))), delimiter=dataDelim, newline='\n',
                               fmt='%g')
                    np.savetxt(fid1, np.transpose(np.array(list(results[1]))), delimiter=dataDelim, newline='\n',
                               fmt='%g')
                else:
                    yy0 = np.squeeze(np.array(list(results[results['channel'] == 0][self.hist]), dtype=np.float32))
                    np.savetxt(fid0, np.transpose([np.arange(yy0.size) + 1, yy0]), delimiter=dataDelim, newline='\n',
                               fmt='%g')
                    yy1 = np.squeeze(np.array(list(results[results['channel'] == 1][self.hist]), dtype=np.float32))
                    np.savetxt(fid1, np.transpose([np.arange(yy1.size) + 1, yy1]), delimiter=dataDelim, newline='\n',
                               fmt='%g')
                fid0.close()
                fid1.close()
        return results, header, files

    def extractRoi(self, rois0=None, rois1=None, roiIdent0=None, roiIdent1=None, resFile=None, files=None,
                   accum_frames='sum', method='sum', dataDelim='\t', headerLines=True, includeFileNames=False,
                   selFolder=False, recursive=False):
        # accum_frames: 'none', 'sum', 'mean', 'median', 'max', 'min'
        # method: 'sum', 'mean', 'median', 'max', 'min'
        # select nexus files
        # if files is None:
        #     if selFolder:
        #         pathName = fg.requestDirectory(dialogTitle='Select folder of spectra files')
        #         files = fg.fileSearch(pathName, '*.nxs', recursive)
        #     else:
        #         files = fg.requestFiles((("Nexus files", "*.nxs"),), "Select P61A file", "on")
        #         pathName, _ = fg.fileparts(files[0])
        # read all data from selected files
        roiVals0 = None
        roiVals1 = None
        if (rois0 is not None and len(rois0) > 0) or (rois1 is not None and len(rois1) > 0):
            handler = P61ANexusHandler()
            data = pd.DataFrame(columns=handler.columns)
            for f_name in files:
                data = pd.concat((data, handler.read(f_name, accum_frames)), ignore_index=True)
            # export data to roi files
            if rois0 is not None and len(rois0) > 0:
                curData = data[data['Channel'] == 0]
                roiVals0 = np.zeros((curData.shape[0], len(rois0)))
                for i in range(len(rois0)):
                    for j in range(curData.shape[0]):
                        curItem = curData.iloc[j]
                        xVals = curItem['DataX']
                        yVals = curItem['DataY']
                        curVals = yVals[xVals >= rois0[i, 0] & xVals <= rois0[i, 0]]
                        if method == 'mean':
                            roiVals0[j, i] = np.mean(curVals)
                        elif method == 'median':
                            roiVals0[j, i] = np.median(curVals)
                        elif method == 'max':
                            roiVals0[j, i] = np.max(curVals)
                        elif method == 'min':
                            roiVals0[j, i] = np.min(curVals)
                        else:  # 'sum'
                            roiVals0[j, i] = np.sum(curVals)
                resFile = files[0].replace('.nxs', '_rois_01_' + method + '.txt')
                if headerLines and roiIdent0 is not None and len(roiIdent0) > 0:
                    # if includeFileNames:
                    #     roiIdent0.insert(0, 'file')
                    header = dataDelim.join(roiIdent0)
                else:
                    header = ''
                # if includeFileNames:
                np.savetxt(resFile, roiVals0, fmt='%.5g', delimiter=dataDelim, newline='\t', header=header)
            if rois1 is not None and len(rois1) > 0:
                curData = data[data['Channel'] == 1]
                roiVals1 = np.zeros((curData.shape[0], len(rois1)))
                for i in range(len(rois1)):
                    for j in range(curData.shape[0]):
                        curItem = curData.iloc[j]
                        xVals = curItem['DataX']
                        yVals = curItem['DataY']
                        curVals = yVals[(xVals >= rois1[i, 0]) & (xVals <= rois1[i, 1])]
                        if method == 'mean':
                            roiVals1[j, i] = np.mean(curVals)
                        elif method == 'median':
                            roiVals1[j, i] = np.median(curVals)
                        elif method == 'max':
                            roiVals1[j, i] = np.max(curVals)
                        elif method == 'min':
                            roiVals1[j, i] = np.min(curVals)
                        else:  # 'sum'
                            roiVals1[j, i] = np.sum(curVals)
                resFile = files[0].replace('.nxs', '_rois_01_' + method + '.txt')
                if headerLines and roiIdent1 is not None and len(roiIdent1) > 0:
                    # if includeFileNames:
                    #     roiIdent1.insert(0, 'file')
                    header = dataDelim.join(roiIdent1)
                else:
                    header = ''
                # if includeFileNames:
                #     roiVals1 = np.concatenate((files, roiVals1))
                np.savetxt(resFile, roiVals1, fmt='%.5g', delimiter=dataDelim, newline='\t', header=header)
        return roiVals0, roiVals1


if __name__ == '__main__':
    files = ()
    P61ANexusHandler().read(files)
