import pandas as pd
from matplotlib import pyplot as plt


if __name__ == '__main__':
    dd = pd.read_csv(r'C:\Users\dovzheng\PycharmProjects\P61AToolkit\data\peaks\stress_00004.csv')
    x_mot = 'eu.psi'

    prefixes = {col.split('_')[0] for col in dd.columns if (('_' in col) and ('pv' in col))}

    if x_mot is None:
        xx = dd.index
    elif x_mot in dd.columns:
        xx = dd[x_mot]
    else:
        xx = dd.index

    for prefix in prefixes:
        if ('_'.join((prefix, 'h')) in dd.columns) and \
                ('_'.join((prefix, 'k')) in dd.columns) and \
                ('_'.join((prefix, 'l')) in dd.columns):
            fig = plt.figure(prefix + ' [%d%d%d]' % (dd.loc[0, '_'.join((prefix, 'h'))],
                                               dd.loc[0, '_'.join((prefix, 'k'))],
                                               dd.loc[0, '_'.join((prefix, 'l'))]))
            fig.suptitle(prefix + ' [%d%d%d]' % (dd.loc[0, '_'.join((prefix, 'h'))],
                                               dd.loc[0, '_'.join((prefix, 'k'))],
                                               dd.loc[0, '_'.join((prefix, 'l'))]))
        else:
            fig = plt.figure(prefix)
            fig.suptitle(prefix)

        ax11 = plt.subplot(221)
        ax11.set_title('Height')
        ax11.errorbar(xx, dd['_'.join((prefix, 'height'))], yerr=dd['_'.join((prefix, 'height', 'std'))])

        ax12 = plt.subplot(222)
        ax12.set_title('$R_{wp}^2$, $\chi^2$')
        ax12.set_ylabel('$R_{wp}^2$', color='tab:red')
        ax12.plot(xx, dd['_'.join((prefix, 'rwp2'))], color='tab:red')
        ax12.tick_params(axis='y', labelcolor='tab:red')
        ax12_2 = ax12.twinx()
        ax12_2.set_ylabel('$\chi^2$', color='tab:blue')
        ax12_2.plot(xx, dd['_'.join((prefix, 'chi2'))], color='tab:blue')
        ax12_2.tick_params(axis='y', labelcolor='tab:blue')

        ax21 = plt.subplot(223)
        ax21.set_title('Center')
        ax21.errorbar(xx, dd['_'.join((prefix, 'center'))], yerr=dd['_'.join((prefix, 'center', 'std'))])

        ax22 = plt.subplot(224)
        ax22.set_title('Sigma')
        ax22.errorbar(xx, dd['_'.join((prefix, 'sigma'))], yerr=dd['_'.join((prefix, 'sigma', 'std'))])

        plt.tight_layout()

    plt.show()
