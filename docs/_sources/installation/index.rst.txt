############
Installation
############


*****************
Download binaries
*****************

A pre-compiled version of the Viewer that requires no installation can be found `here <https://github.com/hereon-GEMS/P61AToolkit/releases>`_.

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
JetBrains provide a tutorial for setting it up and cloning a project from the remote host `here <https://www.jetbrains.com/help/pycharm/set-up-a-git-repository.html>`_.
The URL for the repository you want to clone is: ``https://github.com/hereon-GEMS/P61AToolkit.git``.

If you do not wish to use git and keep the project up to date, you can download the source code `here <https://github.com/hereon-GEMS/P61AToolkit/archive/refs/heads/master.zip>`_.
After extracting the ``.zip`` archive, create a PyCharm project as described `here <https://www.jetbrains.com/help/pycharm/importing-project-from-existing-source-code.html>`_.

After you have created a project, we recommend that you set up a virtual environment for it using the file  ``requirements/env_conda_win.yml``.
If you are unfamiliar with the process, the easiest way to do that is to use Anaconda-Navigator that came with your Python installation, proceed to Environments tab, click Import -> Local Drive, and select the ``requirements/env_conda_win.yml`` file.
You can change the name of the environment if you want. After it is created, follow `these instructions <https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html>`_ (do not create a new environment in PyCharm, add an Existing environment and put in the address of the one you just made).
After this step PyCharm usually hangs for a few minutes while it is indexing all packages from the selected environment.

The last thing to do is to mark directories ``src`` and ``src/py61a`` as Sources Root (in PyCharm: right-click the directory in Project view -> Mark Directory as -> Sources Root) and you are ready.

To run P61A::Viewer, right-click ``src/apps/Viewer/P61AViewerMain.py`` in the Project window and choose Run.

