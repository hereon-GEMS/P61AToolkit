##########################
Laplace space stress analysis
##########################

The purpose of this tutorial is to introduce you to the way peak identification and fitting can be done on experimental
data using P61A::Viewer.

******
Import
******

This tutorial starts with the project file that you can find
`here <https://github.com/P61A-software/P61AToolkit/blob/master/data/tutorials/laplace_space_stress.pickle>`_.
This is a simulated BCC Fe diffraction pattern from a measurement in reflection.
Download the file and open it in Viewer using ``File -> Open`` menu.

*****************
Identifying peaks
*****************

First step of the analysis is understanding what you are looking at. In this dataset we expect to see diffraction from
one phase, and in any dataset coming from P61A we expect to see background that includes a few fluorescence peaks.
Here is what the background looks like without the sample in the beam:

.. image:: background.png
   :width: 600

Most prominent fluorescence peaks are (in keV): ``24.2``, ``27.3``, ``58.0``, ``59.3``, ``67.2``, ``69.1``, ``72.8``,
``75.0``, ``84.9``, ``87.3``
at 8 degrees

