import os
import numpy as np
import pandas as pd

from DatasetIO import P61ANexusHandler
from utils import fileparts, fileparts3, requestFiles, read_fio, write_fio

if __name__ == '__main__':
    # select fio files
    fileNames = requestFiles((("Fio files", '*.fio'),), 'Select motor positions files', 'on')
    # take also header values into account
    # include_header_vals = False
    include_header_vals = True
    # import fio file data
    scanDataFrame = pd.DataFrame()
    fixDataList = []
    for i in range(len(fileNames)):
        scanData, fixData = read_fio(fileNames[i], include_header_vals)
        if scanDataFrame.size < 1:
            scanDataFrame = scanData
            scanDataFrame['fileindex'] = i
        else:
            scanDataFrame = scanDataFrame.append(scanData)
            scanDataFrame.loc[np.isnan(scanDataFrame['fileindex']), 'fileindex'] = i
        fixDataList.append(fixData)

    # analyze motor positions
    mot_uni = {mot: np.unique(scanDataFrame[mot]) for mot in scanDataFrame.keys()}
    mot_uni_num = {mot: mot_uni[mot].size for mot in mot_uni.keys() if mot_uni[mot].size > 1}
    print(dict(sorted(mot_uni_num.items(), key=lambda item: item[1], reverse=True)))

    # combine or extract data
    res_fio_name = 'merge_mean_chi'
    select_type = 'mean'  # 'sum', 'mean', 'max', 'min', 'first', 'last'
    keep_motors = ['eu.x']
    merge_motors = ['eu.chi']
    chi_step = 5
    res_chi = list(range(2, 90, chi_step))

    # path, file = fileparts(fileNames[0])
    path = r'Z:\current\processed'
    resPath = path + '/' + res_fio_name + '/'
    if not os.path.exists(resPath):
        os.makedirs(resPath)
    fio_data = pd.DataFrame(columns=scanDataFrame.keys())
    for mot in keep_motors:
        for val in mot_uni[mot]:
            for merge in merge_motors:
                for chi_res in res_chi:
                    # select relevant fio file entries for merging
                    scanDataSelection = scanDataFrame.loc[
                        (scanDataFrame[mot] == val) & (scanDataFrame[merge] >= chi_res - chi_step / 2) & (scanDataFrame[
                            merge] <= chi_res + chi_step / 2)]
                    # set merged entry for fio file - mean values
                    fio_data.loc[fio_data.shape[0]] = scanDataSelection.mean()
                    fio_data.loc[fio_data.shape[0] - 1].update({'xspress3_index': scanDataSelection.iloc[0]['xspress3_index']})
                    # select relevant nexus files
                    selFioFiles = [fileNames[int(i)] for i in scanDataSelection['fileindex']]
                    nexus_files = [('%s/%s/%s_%05d.nxs' % (
                        fileparts3(f)[0], fileparts3(f)[1], '_'.join(fileparts3(f)[1].split('_')[:-1]),
                        scanDataSelection.iloc[i]['xspress3_index'])) for i, f in enumerate(selFioFiles)]
                    # create merged nexus file
                    resFile = resPath + res_fio_name + ('_%05d.nxs' % scanDataSelection.iloc[0]['xspress3_index'])
                    P61ANexusHandler().accumSpectra(resFile, nexus_files, 'sum', select_type, False)
    # create merged fio file
    write_fio({}, fio_data.drop(labels='fileindex', axis=1), path + '/' + res_fio_name + '.fio', True)
