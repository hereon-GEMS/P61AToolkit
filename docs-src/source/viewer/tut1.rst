############################
Simple sequential refinement
############################

******
Import
******

P61A beamline saves spectra as NeXuS ``.nxs`` files and metadata as FIO ``.fio`` files.
The beamline conrtrol software `SPOCK <https://hasyweb.desy.de/services/computing/Spock/Spock.pdf>`_ is set up in
such a way, that if you make a single acquisition using ``ct`` command,
just one ``.nxs`` file will be saved, and if you make a scan (``ascan``, ``dscan``, ``mesh``, etc.), a ``.fio`` file
with motor positions will be created, and next to it a directory by the same name with the ``.nxs`` files collected at
different motor positions.

In P61A::Viewer you can import just NeXuS files (without motor positions and other metadata) and FIO files
(with all coorresponding spectra and metadata) using the ``+`` button.

For this tutorial we have prepared a simple dataset you can download here. As a first step,
import the dataset by pressing the ``+`` button on the Viewer and selecting the FIO file.

*************
Project files
*************

After you have imported the data, you should save your analysis using File -> Save As menu.
The format of the project files is ``.pickle``, and they are just
`serialized <https://docs.python.org/3/library/pickle.html>`_ Python 3 objects.

Project files are cross-platform and self-sufficient: you do not need to store them next to the collected data and can
transfer them from one computer to another.

.. warning::
    P61A Toolkit is a young project with high expectancy of bugs! Software may freeze or crash.
    To avoid frustration, please save your analysis regularly.

***********
View / Sort
***********

The dataset for this tutorial is called ``SDP``, which stands for Shifting Double Peaks.
Purpose of this tutorial is to show you how P61A::Viewer treats peaks during sequential refinement.

First step of sequential refinement is organizing your data. You can sort the datasets by
name, detector dead time, fit quality, and metadata values by clicking on the column headers of the dataset table.
You can also add / remove columns from the table by right-clicking the header, and selecting metadata variables in the
popup menu.

In this dataset values for ``eu.x``, ``eu.y`` and ``eu.z`` are random. You can sort the data by them to see how it
looks, but to continue we need to have data sorted by Name or ``xspress3_index``.

***********
Peak search
***********

The peak search algorithm in P61A::Viewer searches for local maxima in the datasets, and then filters them by the
following criteria:

1. **Height:** Minimal height of the point to be considered a peak.

2. **Distance:** Minimal distance between two peaks in keV.

3. **Width:** Minimal width (FWHM) of the peak in keV.

4. **Prominence:** Minimal distance between the peak and the surrounding baseline.

If you want to learn more about the algorithm, you can find its description
`here <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html>`_.