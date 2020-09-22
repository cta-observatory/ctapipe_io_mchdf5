[![Build Status](https://travis-ci.org/cta-observatory/ctapipe_io_mchdf5.svg?branch=master)](https://travis-ci.org/cta-observatory/ctapipe_io_mchdf5)

ctapipe plugin for reading and converting Monte-Carlo files (contains the same information as Simtel files).

Repository **CURRENTLY** getting update with _ctapipe_0.8 data format.

Installation
============

```sh
  $ git clone https://github.com/cta-observatory/ctapipe_io_mchdf5.git
  $ cd ctapipe_io_mchdf5
  $ python setup.py install
```
Simtel file conversion to HDF5-R0
=================================

```sh
  $ mchdf5_simtel2r0 -i inputFile.simtel.gz -o outputFile.h5
```


HDF5-R1 file conversion to HDF5-DL0_v1
======================================
Average among slices for not selected pixels.

```sh
  $ mchdf5_tailcut_dilation_dl0v1 -i inputFile.h5 -o outputFile-dl0_v1.h5 -c 8 -n 4 -d 3 -m 1
```
 - **-c** : [float] center threshold parameter
 - **-n** : [float] neighbours threshold parameter
 - **-m** : [int]   minimum number of selected neighbours of the current pixel
 - **-d** : [int]   dilation : number of rows to be added around the selected pixel


HDF5-R1 file conversion to HDF5-DL0_v2
======================================
Not selected pixels are removed from waveform. Reconstruction will be needed. 

```sh
  $ mchdf5_tailcut_dilation_dl0v2 -i inputFile.h5 -o outputFile-dl0_v2.h5 -c 8 -n 4 -d 3 -m 1
```
 - **-c** : [float] center threshold parameter
 - **-n** : [float] neighbours threshold parameter
 - **-m** : [int]   minimum number of selected neighbours of the current pixel
 - **-d** : [int]   dilation : number of rows to be added around the selected pixel
 