"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

import tables
import numpy as np

from .telescope_copy import copy_telescope_without_waveform


def create_sorted_waveform_table(hfile, cam_tel_group, nameWaveformHi, nbSlice, nbPixel, isStoreSlicePixel,
								 chunkshape=1):
	"""
	Create the table to store the signal
	Parameters:
		hfile : HDF5 file to be used
		cam_tel_group : telescope group in which to put the tables
		nameWaveformHi : name of the table to store the waveform
		nbSlice : number of slices of the signal
		nbPixel : number of pixels of the camera
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	"""
	image_shape = (nbPixel, nbSlice)
	if isStoreSlicePixel:
		image_shape = (nbSlice, nbPixel)
	columns_dict_waveformHi  = {nameWaveformHi: tables.UInt16Col(shape=image_shape)}
	description_waveformHi = type('description columns_dict_waveformHi', (tables.IsDescription,),
								  columns_dict_waveformHi)
	hfile.create_table(cam_tel_group, nameWaveformHi, description_waveformHi, "Table of waveform of the signal",
					   chunkshape=chunkshape)


def create_telescope_sorted(outFile, telNode, isStoreSlicePixel, chunkshape=1):
	"""
	Create the telescope group and table
	Parameters:
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	"""
	cam_tel_group = copy_telescope_without_waveform(outFile, telNode, chunkshape)

	nbPixel = np.uint64(telNode.nbPixel.read())
	nbSlice = np.uint64(telNode.nbSlice.read())

	create_sorted_waveform_table(outFile, cam_tel_group, "waveformHi", nbSlice, nbPixel, isStoreSlicePixel,
								 chunkshape=chunkshape)
	nbGain = np.uint64(telNode.nbGain.read())
	if nbGain > 1:
		create_sorted_waveform_table(outFile, cam_tel_group, "waveformLo", nbSlice, nbPixel, isStoreSlicePixel,
									 chunkshape=chunkshape)


def create_all_telescope_sorted(outFile, inFile, isStoreSlicePixel, chunkshape=1):
	"""
	Create all the telescope ready for pixels sorting
	Parameters:
		outFile : output file
		inFile : input file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	"""
	outFile.create_group("/", 'r1', 'Raw data waveform information of the run')
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			create_telescope_sorted(outFile, telNode, isStoreSlicePixel, chunkshape=chunkshape)
		except tables.exceptions.NoSuchNodeError as e:
			pass

def create_sorted_waveform_tableShape(hfile, cam_tel_group, nameWaveformHi, dataEntryShape, chunkshape=1):
	"""
	Create the table to store the signal
	Parameters:
		hfile : HDF5 file to be used
		cam_tel_group : telescope group in which to put the tables
		nameWaveformHi : name of the table to store the waveform
		dataEntryShape : shape of the entries to be stored
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	Return:
		create table
	"""
	columns_dict_waveformHi  = {nameWaveformHi: tables.UInt16Col(shape=dataEntryShape)}
	description_waveformHi = type('description columns_dict_waveformHi', (tables.IsDescription,),
								  columns_dict_waveformHi)
	return hfile.create_table(cam_tel_group, nameWaveformHi, description_waveformHi, "Table of waveform of the signal",
							  chunkshape=chunkshape)







