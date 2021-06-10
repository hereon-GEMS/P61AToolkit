import numpy as np
from scipy.spatial.transform import Rotation
import pandas as pd


def _sample_transform(phi, chi, beta, alpha):
    r1 = Rotation.from_rotvec(phi * np.pi / 180. * np.array([0., 0., 1.]))
    r2 = Rotation.from_rotvec(chi * np.pi / 180. * np.array([0., 1., 0.]))
    r3 = Rotation.from_rotvec(beta * np.pi / 180. * np.array([0., 0., 1.]))
    r4 = Rotation.from_rotvec(alpha * np.pi / 180. * np.array([1., 0., 0.]))
    return r4 * r3 * r2 * r1


def _diff_beam_transform(drx, drz):
    r1 = Rotation.from_rotvec(drz * np.pi / 180. * np.array([0., 0., 1.]))
    r2 = Rotation.from_rotvec(drx * np.pi / 180. * np.array([1., 0., 0.]))
    return r2 * r1


def _tth(drx, drz):
    diff_beam = _diff_beam_transform(drx, drz).apply(np.array([0., 1., 0.]))
    return np.rad2deg(np.arccos(np.inner(diff_beam, np.array([0., 1., 0.]))))


def _psi(phi, chi, beta, alpha, drx, drz):
    sample_norm = _sample_transform(phi, chi, beta, alpha).apply(np.array([0., 0., 1.]))

    diff_vec = _diff_beam_transform(drx, drz).apply(np.array([0., 1., 0.])) - np.array([0., 1., 0.])
    diff_vec /= np.linalg.norm(diff_vec)

    return np.rad2deg(np.arccos(np.inner(diff_vec, sample_norm)))


def _eta(phi, chi, beta, alpha, drx, drz):
    diff_vec = _diff_beam_transform(drx, drz).apply(np.array([0., 1., 0.])) - np.array([0., 1., 0.])
    diff_vec /= np.linalg.norm(diff_vec)

    return np.rad2deg(np.arccos(np.inner(
        np.cross(np.array([0., 1., 0.]), diff_vec),
        np.cross(_sample_transform(phi, chi, beta, alpha).apply(np.array([0., 0., 1.])), diff_vec)
    )))


def motors_to_angles(data: pd.DataFrame):
    """
    Calculates angles in sample coordinate system from motor positions of Eulerian cradle and detector portal.

    :param data:
    :return:
    """
    missing = []
    for col in ('d0.rx', 'd0.rz', 'd1.rx', 'd1.rz', 'eu.chi', 'eu.phi', 'eu.bet', 'eu.alp', 'Channel'):
        if col not in data.columns:
            missing.append(col)
    else:
        if missing:
            raise ValueError('The following columns are missing from the input dataset: %s.' % ', '.join(missing))

    data['tth'] = data.apply(lambda row: _tth(row['d%d.rx' % row['Channel']], row['d%d.rz' % row['Channel']]), axis=1)
    data['psi'] = data.apply(lambda row: _psi(row['eu.phi'], row['eu.chi'], row['eu.bet'], row['eu.alp'],
                                              row['d%d.rx' % row['Channel']], row['d%d.rz' % row['Channel']]), axis=1)
    data['eta'] = data.apply(lambda row: _eta(row['eu.phi'], row['eu.chi'], row['eu.bet'], row['eu.alp'],
                                              row['d%d.rx' % row['Channel']], row['d%d.rz' % row['Channel']]), axis=1)
    data['phi'] = data['eu.phi']

    return data
