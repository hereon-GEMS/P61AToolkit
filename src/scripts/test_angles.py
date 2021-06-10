import pandas as pd
from libraries.beamline_utils import motors_to_angles


if __name__ == '__main__':
    data = pd.read_csv(r'C:\Users\dovzheng\Experiments\angles_Nowfal.csv', index_col=0)
    data = motors_to_angles(data)

    print(data[['tth', 'psi', 'eta', 'phi']])