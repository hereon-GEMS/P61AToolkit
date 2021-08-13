import numpy as np


def hooke(strain_tensor, s1, hs2):
    assert isinstance(strain_tensor, np.ndarray)
    assert strain_tensor.ndim == 3
    assert strain_tensor.shape[0] == 3
    assert strain_tensor.shape[1] == 3
    return (1. / hs2) * strain_tensor - \
           (1. / hs2) * (s1 / (hs2 + 3. * s1)) * np.tensordot(np.eye(3), np.trace(strain_tensor), axes=0)


def inv_hooke(stress_tensor, s1, hs2):
    assert isinstance(stress_tensor, np.ndarray)
    assert stress_tensor.ndim == 3
    assert stress_tensor.shape[0] == 3
    assert stress_tensor.shape[1] == 3
    return hs2 * stress_tensor + s1 * np.tensordot(np.eye(3), np.trace(stress_tensor), axes=0)


def tensor_projection(strain_tensor, phi_, psi_):
    assert strain_tensor.ndim == 2
    return strain_tensor[0, 0] * (np.cos(np.radians(phi_)) * np.sin(np.radians(psi_))) ** 2 + \
           strain_tensor[0, 1] * np.sin(np.radians(2. * phi_)) * (np.sin(np.radians(psi_))) ** 2 + \
           strain_tensor[0, 2] * np.cos(np.radians(phi_)) * np.sin(np.radians(2. * psi_)) + \
           strain_tensor[1, 1] * (np.sin(np.radians(phi_)) * np.sin(np.radians(psi_))) ** 2 + \
           strain_tensor[1, 2] * np.sin(np.radians(phi_)) * np.sin(np.radians(2. * psi_)) + \
           strain_tensor[2, 2] * (np.cos(np.radians(psi_))) ** 2
