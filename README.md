Acoustics 2012 Hong Kong: Real-Time Segmentation of the Temporal Evolution of Musical Sounds
============================================================================================

Code needed to replicate the results from my 2012 paper in the proceedings of the Acoustics 2012
Hong Kong conference.

Send comments/queries to john dot c dot glover at nuim dot ie


Dependencies
------------

* [pyyaml](http://pyyaml.org)
* [clint](http://pypi.python.org/pypi/clint)
* [notesegmentation](http://github.com/johnglover/notesegmentation) (and all related dependencies)
* [modal](http://github.com/johnglover/modal) (and all related dependencies)
* [simpl](http://simplsound.sourceforge.net) (and all related dependencies)


Annotated Samples
-----------------

The set of annotated samples is available at
[https://github.com/downloads/johnglover/acoustics2012/samples.hdf5](https://github.com/downloads/johnglover/acoustics2012/samples.hdf5)

Use
---

Set the MODAL_ONSETS_PATH environment variable to point to the location of
the set of annotated samples. Then, run:

    $ python analysis.py 
