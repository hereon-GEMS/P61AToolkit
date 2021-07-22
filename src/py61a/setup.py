from distutils.core import setup


setup(name='py61a',
      version='1.0',
      description='Python utilities for data analysis from P61A beamline',
      author='Gleb Dovzhenko',
      author_email='gleb.dovzhenko@hereon.de',
      url='https://p61a-software.github.io/P61AToolkit/',
      package_dir={'': '..'},
      packages=[
          'py61a',
          'py61a.beamline_utils',
          'py61a.cryst_utils',
          'py61a.stress'
      ])