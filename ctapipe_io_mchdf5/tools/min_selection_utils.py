'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
from .telescope_copy import copyTelescopeWithoutWaveform

def createMinWaveformTable(hfile, cam_tel_group, nameWaveformMinHi, nameMinHi, nbSlice, nbPixel, chunkshape=1):
	'''
	Create the table to store the signal without the minimum value and it minimum in an other table
	Parameters:
		hfile : HDF5 file to be used
		cam_tel_group : telescope group in which to put the tables
		nameWaveformMinHi : name of the table to store the waveform without minimum value
		nameMinHi : name of the table to store the minimum value of the waveform
		nbSlice : number of slices of the signal
		nbPixel : number of pixels of the camera
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	image_shape = (nbSlice, nbPixel)
	columns_dict_waveformMinHi  = {nameWaveformMinHi: tables.UInt16Col(shape=image_shape)}
	description_waveformMinHi = type('description columns_dict_waveformMinHi', (tables.IsDescription,), columns_dict_waveformMinHi)
	hfile.create_table(cam_tel_group, nameWaveformMinHi, description_waveformMinHi, "Table of waveform of the signal without the minimum value", chunkshape=chunkshape)
	
	columns_dict_minHi  = {nameMinHi: tables.UInt16Col(shape=nbPixel)}
	description_waveformMinHi = type('description columns_dict_minHi', (tables.IsDescription,), columns_dict_minHi)
	hfile.create_table(cam_tel_group, nameMinHi, description_waveformMinHi, "Table of the minimum values of the waveform of the signal", chunkshape=chunkshape)
	


def createTelescopeMinSelectionNode(outFile, telNode, chunkshape=1):
	'''
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	cam_tel_group = copyTelescopeWithoutWaveform(outFile, telNode, chunkshape)
	
	nbPixel = np.uint64(telNode.nbPixel.read())
	nbSlice = np.uint64(telNode.nbSlice.read())
	
	createMinWaveformTable(outFile, cam_tel_group, "waveformHi", "minHi", nbSlice, nbPixel, chunkshape=chunkshape)
	
	nbGain = np.uint64(telNode.nbGain.read())
	if nbGain > 1:
		createMinWaveformTable(outFile, cam_tel_group, "waveformLo", "minLo", nbSlice, nbPixel, chunkshape=chunkshape)


def createAllTelescopeMinSelected(outFile, inFile, nbEventPerMin, chunkshape=1):
	'''
	Create all the telescope with the minimum selection
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		nbEventPerMin : number of events to be used to compute one minimum
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	outFile.create_group("/", 'r1', 'Raw data waveform informations of the run')
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			createTelescopeMinSelectionNode(outFile, telNode, chunkshape=chunkshape)
		except tables.exceptions.NoSuchNodeError as e:
			pass



