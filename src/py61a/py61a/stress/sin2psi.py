import numpy as np
import pandas as pd
from uncertainties import ufloat

from py61a.viewer_utils import valid_peaks, group_by_motors
from scipy.optimize import curve_fit
from functools import partial

pd.options.mode.chained_assignment = None


class Sin2PsiProjection:
    def __init__(self, xdata, ydata, depth, slope=None, intercept=None):
        if not (xdata.shape == ydata.shape == depth.shape):
            raise ValueError('Array shapes should match')

        self.xdata = xdata
        self.ydata = ydata
        self.depth = depth

        ids = np.isnan(self.xdata) | np.isnan(self.ydata)
        self.xdata, self.ydata, self.depth = self.xdata[~ids], self.ydata[~ids], self.depth[~ids]

        if self.xdata.size < 3 or self.ydata.size < 3:
            self.slope = np.nan
            self.intercept = np.nan
            self.slope_std = np.nan
            self.intercept_std = np.nan
            self.xdata = np.array([np.nan])
            self.ydata = np.array([np.nan])
            self.depth = np.array([np.nan])
            return

        def f(x, slp, intr):
            return x * slp + intr

        if slope is None and intercept is None:
            popt, pcov = curve_fit(f, self.xdata, self.ydata, p0=(0., 0.))
            pcov = np.sqrt(np.diag(pcov))
            self.slope = popt[0]
            self.intercept = popt[1]
            self.slope_std = pcov[0]
            self.intercept_std = pcov[1]
        elif slope is None and intercept is not None:
            f = partial(f, intr=intercept)
            popt, pcov = curve_fit(f, self.xdata, self.ydata, p0=(0.,))
            pcov = np.sqrt(np.diag(pcov))
            self.slope = popt[0]
            self.intercept = intercept
            self.slope_std = pcov[0]
            self.intercept_std = np.nan
        elif slope is not None and intercept is None:
            f = partial(f, slp=slope)
            popt, pcov = curve_fit(f, self.xdata, self.ydata, p0=(0.,))
            pcov = np.sqrt(np.diag(pcov))
            self.slope = slope
            self.intercept = popt[0]
            self.slope_std = np.nan
            self.intercept_std = pcov[0]
        else:
            self.slope = np.nan
            self.intercept = np.nan
            self.slope_std = np.nan
            self.intercept_std = np.nan

    @property
    def ycalc(self):
        return self.slope * self.xdata + self.intercept

    @property
    def y_median(self):
        return self.slope * 0.5 + self.intercept

    @property
    def uslope(self):
        return ufloat(self.slope, self.slope_std)

    @property
    def uintercept(self):
        return ufloat(self.intercept, self.intercept_std)

    def __repr__(self):
        return '%f * x + %f' % (self.slope, self.intercept)

    def isnan(self):
        return np.isnan(self.slope) and np.isnan(self.intercept)


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

    phi_values = 0, 45, 90, 135, 180, 225, 270, 315
    phi_dict = {
        k: (str(phi_values[k]), str(phi_values[k + len(phi_values) // 2])) for k in range(len(phi_values) // 2)
    }
    sin2psi_columns = sum([('+'.join(val), '-'.join(val)) for (key, val) in phi_dict.items()], ())

    dataset = dataset.copy(deep=True)

    if 'scanpts' in dataset.columns:
        scan_motors = list(dataset['scanpts'].columns)
    else:
        scan_motors = ['__PT__']
        dataset.loc[:, ('scanpts', '__PT__')] = 0

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
    result_columns = pd.MultiIndex.from_product([result_columns, sin2psi_columns])

    result = pd.DataFrame(np.nan, index=result_index, columns=result_columns, dtype=object)

    ds_groups = dataset.groupby([('scanpts', sm) for sm in scan_motors])

    for res_idx in result_index:
        if len(res_idx) == 1:
            res_idx = res_idx[0]

        # this is one sin2psi scan
        tmp = dataset.loc[ds_groups.groups[res_idx]]
        for peak_id in valid_peaks(tmp):
            if (peak_id, 'depth') in tmp.columns:
                peak_data = tmp[[('scanpts', '__PHI__'), ('scanpts', '__PSI__'),
                                 ('md', psi_col), ('md', phi_col), (peak_id, 'd'), (peak_id, 'depth')]]
            else:
                peak_data = tmp[[('scanpts', '__PHI__'), ('scanpts', '__PSI__'),
                                 ('md', psi_col), ('md', phi_col), (peak_id, 'd')]]
            peak_data = peak_data.groupby(by=[('scanpts', '__PHI__'), ('scanpts', '__PSI__')]).mean()

            for ii in range(len(phi_values) // 2):
                peak_data_proj = peak_data.loc[
                    peak_data.index.get_level_values(('scanpts', '__PHI__')).map(
                        lambda x: x in (ii, ii + len(phi_values) // 2)
                    )
                ].groupby(by=[('scanpts', '__PSI__')]).mean()

                if (peak_id, 'depth') in peak_data_proj.columns:
                    depth = peak_data_proj.loc[:, (peak_id, 'depth')].to_numpy()
                else:
                    depth = np.array([np.nan] * peak_data_proj.shape[0])

                result.loc[res_idx, (peak_id, '+'.join(phi_dict[ii]))] = Sin2PsiProjection(
                    xdata=(np.sin(np.radians(peak_data_proj.loc[:, ('md', psi_col)])) ** 2).to_numpy(),
                    ydata=peak_data_proj.loc[:, (peak_id, 'd')].to_numpy(),
                    depth=depth
                )

                peak_data_proj = peak_data.loc[
                    peak_data.index.get_level_values(('scanpts', '__PHI__')).map(
                        lambda x: x in (ii, ii + len(phi_values) // 2)
                    )
                ]
                ids = peak_data_proj.loc[
                    peak_data_proj.index.get_level_values(('scanpts', '__PHI__')) == (ii + len(phi_values) // 2)
                ].index
                peak_data_proj.loc[ids, (peak_id, 'd')] = -1 * peak_data_proj.loc[ids, (peak_id, 'd')]
                peak_data_proj = peak_data_proj.groupby(by=[('scanpts', '__PSI__')]).mean()

                if (peak_id, 'depth') in peak_data_proj.columns:
                    depth = peak_data_proj.loc[:, (peak_id, 'depth')].to_numpy()
                else:
                    depth = np.array([np.nan] * peak_data_proj.shape[0])

                result.loc[res_idx, (peak_id, '-'.join(phi_dict[ii]))] = Sin2PsiProjection(
                    xdata=(np.sin(np.radians(2. * peak_data_proj.loc[:, ('md', psi_col)]))).to_numpy(),
                    ydata=peak_data_proj.loc[:, (peak_id, 'd')].to_numpy(),
                    depth=depth,
                    intercept=0.
                )

    for peak_id in valid_peaks(dataset):
        for col in sin2psi_columns:
            if all(result.loc[:, (peak_id, col)].apply(lambda x: x.isnan())):
                result.drop(columns=[(peak_id, col)], inplace=True)

    return result
