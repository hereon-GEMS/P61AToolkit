########
Overview
########

P61A Toolkit is a set of analysis tools for energy dispersive diffraction data from P61A beamline at PETRA III.

Everything within the Toolkit is written in Python 3 and distributed under GPL v.3 license

The Toolkit includes:

************
P61A::Viewer
************

A tool for viewing, sorting and analysing data from the beamline with features including:

* Diffraction spectra & metadata (motor positions, sample environment readouts, etc.) import and visualization;
* *Currently in development:* diffraction spectra energy scale corrections;
* Automatic peak search, sequential peak / background refinement;
* Diffraction spectra / peak position export for further analysis.

The Viewer is available as a part of the Toolkit (see: :ref:`install-from-source`) or as a Windows executable file.

.. warning::
    P61A Toolkit is a young project that is constantly receiving feature and performance updates and bug fixes.
    While we do provide executables for the Viewer, we recommend that you install the Toolkit from source code and pull updates from github before every use.

************
P61A::Stress
************

A tool for computing stress distributions based on the crystallographic and positional data.

This software is very early in its development and currently is only available as a set of Python scripts that you will probably have to modify to use.

***********************
Current state and plans
***********************

The current feature set of the Toolkit allows for:

* Peak fitting for most experimental cases at the beamline;
* Stress analysis on single cubic phase materials for multiple experiment geometries (requires some familiarity with Python).

Features currently in development:

* Diffraction spectra energy scale corrections: detector dead time, geometry, etc.;
* Stress analysis on hcp phases;
* UI for the stress analysis that does not require Python knowledge.

Further plans:

* Phase & texture analysis.