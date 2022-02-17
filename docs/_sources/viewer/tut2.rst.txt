###################################
Realistic diffraction data analysis
###################################

The purpose of this tutorial is to introduce you to the way peak identification and fitting can be done on experimental
data using P61A::Viewer.

******
Import
******

This tutorial starts with the project file that you can find
`here <https://github.com/hereon-GEMS/P61AToolkit/blob/master/data/tutorials/laplace_space_stress.pickle>`_.
This is a simulated BCC Fe diffraction pattern from a measurement in reflection.
Download the file and open it in Viewer using ``File -> Open`` menu.

*****************
Identifying peaks
*****************

First step of the analysis is understanding what you are looking at. In this dataset we expect to see diffraction from
one phase, and in any dataset coming from P61A we expect to see background that includes a few fluorescence peaks.
Here is what the background looks like without the sample in the beam:

.. image:: tut-02-img0.png
   :width: 600

The plot is in log scale for more clarity.
Most prominent fluorescence peaks are (in keV): ``24.2``, ``27.3``, ``58.0``, ``59.3``, ``67.2``, ``69.1``, ``72.8``,
``75.0``, ``84.9``, ``87.3``. They correspond with emission spectra of ``W`` and ``Pb``.

Compare this to the spectra with diffraction data.

.. image:: tut-02-img1.png
   :width: 600

Let us identify which peaks belong to Fe. We know that the measurements were performed at 2Θ = 8°,
and generally the cell parameter of BCC Fe is around 2.85 Å.
So we can set the parameters in the phase constructor in the bottom left as:
``Space group: im-3m``, ``a = 2.85 Å``, ``2Θ = 8°``, and check the ``Show hkl`` checkbox above the plot.
Stripes should appear indicating the modelled peak positions.

.. image:: tut-02-img2.png
   :width: 600

*************
Finding peaks
*************

Now that we know which peaks we want to fit, we can start setting up the refinement model.

On one hand, you may want to fit as many peaks as you can identify on the image.
You have already collected the data, no reason to waste it.
On the other hand, the more peaks you have in the refinement model, the longer it takes to fit them.
Additionally, small peaks with high variance in position, amplitude, and especially width, take longer to refine and are prone to errors.
Minimizing algorithm tends to lose its way and often requires tedious adjustments when signal to noise ratio is low.

Unfortunately, all data is different, so there is very little general advice on how many peaks is the right amount for analysis.
The idea is that you choose as many prominent peaks as the Viewer can handle in reasonable time, while also adding all the small neighbouring peaks that can affect the fit quality.
This will become more clear in further sections.

As a first attempt to do the peak search we can always launch it with default parameters.
So if you just press ``Find`` button in the top left corner you will get this

.. image:: tut-02-img3.png
   :width: 600

This is a pretty good starting point.
Multiple diffraction peaks are identified plus a few of their neighbours that we need to pay attention to.
That means you can press the ``Make Tracks`` button and proceed to the next step.

*************
Tracks
*************

Once you have pressed ``Make Tracks``, created tracks should appear on the list on the left

.. image:: tut-02-img5.png
   :width: 600

The idea behind the tracks is that each track follows the evolution of a peak over the collected spectra.
The list gives you the peak positions and which hkl and phase they are identified as.

**************
Editing Tracks
**************

The track creation / editing workflow should go as follows:

#. Search for peaks.
#. If too many / not enough peaks were found, adjust peak search parameters (see :ref:`peak-search`) and search again.
#. Make tracks.
#. If the tracks do not follow the observed diffraction peaks, adjust ``Track Window`` parameter and then search and make tracks again.

Please pay attention, that the ``Track Window`` parameter is not too wide or too narrow (see :ref:`peak-tracking`)!

``Track Window`` should be larger than the variance in peak position between the spectra and smaller than the distance between the two neighbouring peaks.
Here are two examples of wrong ``Track Window`` values.

Too large (clearly different observed peaks are selected as one):

.. image:: tut-02-img6.png
   :width: 600

Too small (multiple tracks created for one peak):

.. image:: tut-02-img7.png
   :width: 600

Correct:

.. image:: tut-02-img8.png
   :width: 600

#. Once most / some of the peaks are tracked correctly, you can edit (move)

****************
Expanding tracks
****************

Next step is to make sure that all of the tracks cover all of the datasets.
For this particular dataset this is not a concern, but sometimes the intensity variance is

******************
Adding more tracks
******************

We have already added most of the peaks we want, there is just a few left.
But before we start adding more tracks, let us look at the ones we have.
The idea behind the tracks is that

A closer look on the ``Peak Fit`` tab shows what we are missing:

.. image:: tut-02-img4.png
   :width: 600

We want to fit the peaks at ``62.6``, ``76.6``, and ``88.5`` as precisely as possible.