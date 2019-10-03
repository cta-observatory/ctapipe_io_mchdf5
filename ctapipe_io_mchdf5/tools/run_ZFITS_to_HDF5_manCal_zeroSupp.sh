#!/usr/bin/env bash

INFILE='/Users/garciaenrique/CTA/data/data_notebooks/LST-1.1.Run00251.0000.fits.fz'
OUTFILE_HDF5='/Users/garciaenrique/CTA/output_mchdf5/dl0_251_Branch_manCal.h5'
OUTFILE_HDF5_COMP='/Users/garciaenrique/CTA/output_mchdf5/dl0_251_Branch_manCal_comp.h5'
COMP_LVL=7

python lst-simtel_2_hdf5_v2_manCal_and_zeroSupp.py -i ${INFILE} -o ${OUTFILE_HDF5} -cl 0
ptrepack --comlevel ${COMP_LVL} --complib blosc:zstd ${OUTFILE_HDF5}  ${OUTFILE_HDF5_COMP}
