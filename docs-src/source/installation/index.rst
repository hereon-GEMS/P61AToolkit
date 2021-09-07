############
Installation
############


*****************
Download binaries
*****************

A pre-compiled version of the Viewer that requires no installation can be found `here <https://github.com/P61A-software/P61AToolkit/releases>`_.

.. _install-from-source:

*****************************
Installation from source code
*****************************

Recommended environment.
========================
If you are well versed in Python and / or open-source software, you probably don't need this tutorial.
However, if you do, here is our recommended technological stack:

1. Python. We recommend using `Anaconda Python <https://www.anaconda.com/products/individual>`_ for its convenience and availability. Depending on your OS and Python distribution, working with packages like Qt and OpenGL can be pretty taxing. Hence, we recommend Anaconda as a convenient cross-platform solution.

2. IDE (source code editor): `PyCharm <https://www.jetbrains.com/pycharm/>`_. We recommend PyCharm for its beginner friendly all-in-one approach and cross-platform availability. The community edition is free and has a lot of helpful features (Virtual environment and Git integration).

Setting up a PyCharm project.
=============================
If you have never used `PyCharm <https://www.jetbrains.com/pycharm/>`_ and `git <https://git-scm.com/>`_ before, you will have to set it up first.
JetBrains provide a tutorial for setting it up and checking out a project from the remote host `here <https://www.jetbrains.com/help/pycharm/set-up-a-git-repository.html>`_.
The URL for the repository you want to clone is: ``https://github.com/P61A-software/P61AToolkit.git``.

After you have created a project, we recommend that you set up a virtual environment for it using the file  ``requirements/env_conda_win.yml`` as explained `here <https://www.jetbrains.com/help/pycharm/conda-support-creating-conda-virtual-environment.html#conda-requirements>`_.

The last thing to do is to mark directories ``src`` and ``src/Viewer`` as Sources Root (in PyCharm: right-click -> Mark Directory as -> Sources Root) and you are ready.

To run P61A::Viewer, right-click ``src/apps/Viewer/P61AViewerMain.py`` in the Project window and choose Run.

