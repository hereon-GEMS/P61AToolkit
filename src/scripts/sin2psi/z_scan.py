import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from uncertainties import unumpy, ufloat
from copy import deepcopy

from py61a.viewer_utils import read_peaks, valid_peaks, group_by_motors
from py61a.cryst_utils import tau, mu, bragg
from py61a.stress import Sin2Psi, MultiWaveLength, DeviatoricStresses


# def deviatoric_one_point(dataset):
#     # calculating information depth (tau) and d values
#     for peak_id in valid_peaks(dataset, valid_for='sin2psi'):
#         dataset.loc[:, (peak_id, 'depth')] = tau(
#             mu=mu(element, dataset[peak_id]['center']),
#             tth=tth,
#             eta=90.,
#             psi=dataset['md']['eu.chi']
#         )
#         bragg_data = bragg(
#             en=unumpy.uarray(dataset[peak_id]['center'].values, dataset[peak_id]['center_std'].values),
#             tth=tth)
#         dataset.loc[:, (peak_id, 'd')] = unumpy.nominal_values(bragg_data['d'])
#         dataset.loc[:, (peak_id, 'd_std')] = unumpy.std_devs(bragg_data['d'])
#
#     # sin2psi analysis
#     analysis = Sin2Psi(dataset)
#
#     # deviatoric stress component analysis
#     analysis = DeviatoricStresses(
#         analysis,
#         dec=pd.read_csv(r'../../../data/dec/bccFe.csv', index_col=None, comment='#')
#     )
#
#     return analysis.s11m33, analysis.s22m33, analysis.depths

from scipy.optimize import curve_fit
from functools import partial


def linear_regression(x, y, slope=None, intercept=None):
    def f(x, slp, intr):
        return x * slp + intr

    if slope is None and intercept is None:
        popt, pcov = curve_fit(f, x, y, p0=(0., 0.))
        pcov = np.sqrt(np.diag(pcov))
        slope = popt[0]
        intercept = popt[1]
        slope_std = pcov[0]
        intercept_std = pcov[1]
    elif slope is None and intercept is not None:
        f = partial(f, intr=intercept)
        popt, pcov = curve_fit(f, x, y, p0=(0.,))
        pcov = np.sqrt(np.diag(pcov))
        slope = popt[0]
        intercept = intercept
        slope_std = pcov[0]
        intercept_std = np.nan
    elif slope is not None and intercept is None:
        f = partial(f, slp=slope)
        popt, pcov = curve_fit(f, x, y, p0=(0.,))
        pcov = np.sqrt(np.diag(pcov))
        slope = slope
        intercept = popt[0]
        slope_std = np.nan
        intercept_std = pcov[0]
    else:
        slope = np.nan
        intercept = np.nan
        slope_std = np.nan
        intercept_std = np.nan

    return ufloat(slope, slope_std), ufloat(intercept, intercept_std)


def sin2psi(dataset: pd.DataFrame, phi_col: str, phi_atol: float,
            psi_col: str, psi_atol: float, psi_max: float):
    """

    :param dataset:
    :param phi_col:
    :param phi_atol:
    :param psi_col:
    :param psi_atol:
    :param psi_max:
    :return:
    """

    # sin2psi_columns = '0+180s', '0+180i', '0-180s', '90+270s', '90+270i', '90-270s', \
    #                   '45+225s', '45+225i', '45-225s', '135+315s', '135+315i', '135-315s'
    # phi_values = 0, 45, 90, 135, 180, 225, 270, 315

    sin2psi_columns = '0+180s', '0+180i', '0-180s', '90+270s', '90+270i', '90-270s'
    phi_values = 0, 90, 180, 270

    scan_motors = list(dataset['scanpts'].columns) if 'scanpts' in dataset.columns else []

    dataset = dataset.copy(deep=True)
    dataset = group_by_motors(
        dataset,
        motors=[
            {'mot_name': phi_col, 'atol': phi_atol, 'values': phi_values, 'new_name': '__PHI__'},
            {'mot_name': psi_col, 'atol': psi_atol, 'max': psi_max, 'new_name': '__PSI__'}
        ])
    dataset.drop(dataset[dataset.loc[:, ('scanpts', '__PSI__')] == -1].index, inplace=True)

    result_index = pd.MultiIndex.from_frame(
        dataset[[('scanpts', sm) for sm in scan_motors]].drop_duplicates(),
        names=scan_motors
    )

    result_columns = dataset.columns.get_level_values(0).drop_duplicates()
    result_columns = list(result_columns.drop(['md', 'scanpts']))
    result_columns = pd.MultiIndex.from_product([
        result_columns,
        ['h', 'k', 'l', *sum([[col, col + '_std'] for col in sin2psi_columns], [])]
    ])

    result = pd.DataFrame(np.nan, index=result_index, columns=result_columns)

    ds_groups = dataset.groupby([('scanpts', sm) for sm in scan_motors])

    for res_idx in result_index:
        if len(res_idx) == 1:
            res_idx = res_idx[0]

        # this is one sin2psi scan
        tmp = dataset.loc[ds_groups.groups[res_idx]]
        for peak_id in valid_peaks(tmp):
            for ii in ('h', 'k', 'l'):
                result.loc[res_idx, (peak_id, ii)] = np.int(tmp[(peak_id, ii)].iloc[0])

            peak_data = tmp[[('scanpts', '__PHI__'), ('scanpts', '__PSI__'),
                             ('md', psi_col), ('md', phi_col), (peak_id, 'd')]]
            peak_data = peak_data.groupby(by=[('scanpts', '__PHI__'), ('scanpts', '__PSI__')]).mean()
            print(peak_data)

            result.loc[res_idx, (peak_id, '0+180s')] = 0
            result.loc[res_idx, (peak_id, '0+180s_std')] = 0
            result.loc[res_idx, (peak_id, '0+180i')] = 0
            result.loc[res_idx, (peak_id, '0+180i_std')] = 0
            result.loc[res_idx, (peak_id, '0-180s')] = 0
            result.loc[res_idx, (peak_id, '0-180s_std')] = 0

    # typecasting HKL
    for peak_id in valid_peaks(dataset):
        for ii in ('h', 'k', 'l'):
            result.loc[:, (peak_id, ii)] = result.loc[:, (peak_id, ii)].astype(np.int)

    return result


if __name__ == '__main__':
    # read the data
    dd = read_peaks(r'Z:\p61\2021\commissioning\c20210813_000_gaf_2s21\processed\com4pBending_fullScan_01712.csv')

    # calculate the d values from peak positions
    tth = dd[('md', 'd1.rx')].mean()
    for peak_id in valid_peaks(dd, valid_for='sin2psi'):
        d_val = bragg(en=unumpy.uarray(dd[(peak_id, 'center')], dd[(peak_id, 'center_std')]), tth=tth)['d']
        dd[(peak_id, 'd')] = unumpy.nominal_values(d_val)
        dd[(peak_id, 'd_std')] = unumpy.std_devs(d_val)

    # dd = group_by_motors(dd, motors=[{'mot_name': 'eu.z', 'atol': 1e-3}])

    analysis = sin2psi(dataset=dd, phi_col='eu.phi', phi_atol=5.,
                       psi_col='eu.chi', psi_atol=.1, psi_max=90.)

    print(analysis)

    # zs, s11m33, s22m33 = [], [], []
    # zs_mean, s11m33_mean, s22m33_mean = [], [], []
    # for zg in set(dd[('scanpts', 'eu.z')]):
    #     tmp = dd.loc[dd[('scanpts', 'eu.z')] == zg].copy()
    #     s1, s2, ts = deviatoric_one_point(tmp)
    #     s11m33.extend(list(s1))
    #     s22m33.extend(list(s2))
    #     zs.extend([tmp[('md', 'eu.z')].mean()] * s1.shape[0])
    #     s11m33_mean.append(s1.mean())
    #     s22m33_mean.append(s2.mean())
    #     zs_mean.append(tmp[('md', 'eu.z')].mean())
    #
    # zs, s11m33, s22m33 = np.array(zs), np.array(s11m33), np.array(s22m33)
    # zs_mean, s11m33_mean, s22m33_mean = np.array(zs_mean), np.array(s11m33_mean), np.array(s22m33_mean)
    # ids = np.argsort(zs_mean)
    # zs_mean, s11m33_mean, s22m33_mean = zs_mean[ids], s11m33_mean[ids], s22m33_mean[ids]
    #
    # ax = plt.subplot(111)
    # ax.errorbar(zs, unumpy.nominal_values(s11m33), yerr=unumpy.std_devs(s11m33), marker='.', linestyle='',
    #              label=r'$\sigma_{11} - \sigma_{33}$', color='blue')
    # ax.plot(zs_mean, unumpy.nominal_values(s11m33_mean), marker='', linestyle='--', color='blue', label=None)
    # ax.errorbar(zs, unumpy.nominal_values(s22m33), yerr=unumpy.std_devs(s22m33), marker='.', linestyle='',
    #              label=r'$\sigma_{22} - \sigma_{33}$', color='orange')
    # ax.plot(zs_mean, unumpy.nominal_values(s22m33_mean), marker='', linestyle='--', color='orange', label=None)
    # plt.xlabel('eu.z')
    # plt.ylabel('Stress [MPa]')
    # plt.legend()
    # plt.show()