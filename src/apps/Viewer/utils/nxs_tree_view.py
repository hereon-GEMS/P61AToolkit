import h5py


def visitor_func(name, node):
    if isinstance(node, h5py.Dataset):
        print(node.name, '\nshape:', node.shape,  '\n', node[()])


with h5py.File('../../test_files/collected/Co57_2019-09-30_09-10-30_.nxs', 'r') as f:
    f.visititems(visitor_func)
