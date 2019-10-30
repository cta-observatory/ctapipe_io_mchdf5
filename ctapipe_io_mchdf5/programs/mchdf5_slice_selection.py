
'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from ctapipe_io_mchdf5.tools.telescope_copy import copyTelescopeWithoutWaveform

def createMWaveformTable(hfile, camTelGroup, nameWaveformHi, nbSlice, nbPixel, chunkshape=1):
	'''
	Create the table to store the signal without the minimum value and it minimum in an other table
	Parameters:
		hfile : HDF5 file to be used
		camTelGroup : telescope group in which to put the tables
		nameWaveformHi : name of the table to store the waveform
		nbSlice : number of slices of the signal
		nbPixel : number of pixels of the camera
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	image_shape = (nbSlice, nbPixel)
	columns_dict_waveformHi  = {nameWaveformHi: tables.UInt16Col(shape=image_shape)}
	description_waveformHi = type('description columns_dict_waveformHi', (tables.IsDescription,), columns_dict_waveformHi)
	hfile.create_table(camTelGroup, nameWaveformHi, description_waveformHi, "Table of waveform of the signal", chunkshape=chunkshape)


def createTelescopeSliceSelectionNode(outFile, telNode, nbSlice, chunkshape=1):
	'''
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		nbSlice : number of slices to be expected
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	camTelGroup = copyTelescopeWithoutWaveform(outFile, telNode, chunkshape)
	
	nbPixel = np.uint64(telNode.nbPixel.read())
	
	createMWaveformTable(outFile, camTelGroup, "waveformHi", nbSlice, nbPixel, chunkshape=chunkshape)
	nbGain = np.uint64(telNode.nbGain.read())
	if nbGain > 1:
		createMWaveformTable(outFile, camTelGroup, "waveformLo", nbSlice, nbPixel, chunkshape=chunkshape)


def createAllTelescopeMinSelected(outFile, inFile, nbSlice, chunkshape=1):
	'''
	Create all the telescope with the minimum selection
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		nbSlice : number of slices to be expected
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	outFile.create_group("/", 'r1', 'Raw data waveform informations of the run')
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			createTelescopeSliceSelectionNode(outFile, telNode, nbSlice, chunkshape=chunkshape)
		except tables.exceptions.NoSuchNodeError as e:
			pass


def selectSliceChannel(waveformOut, waveformIn, keyWaveform, firstSliceIndex, lastSliceIndex):
	'''
	Select the slices on tables
	Parameters:
	-----------
		waveformOut : signal selected
		waveformIn : signal to be selected
		keyWaveform : name of the desired column in tables waveformOut and waveformIn)
		firstSliceIndex : Index of the first slice to be selected
		lastSliceIndex : Index of the last slice no to be selected
	'''
	waveformIn = waveformIn.read()
	waveformIn = waveformIn[keyWaveform]
	
	waveformSelect = waveformIn[:, firstSliceIndex:lastSliceIndex, :]
	
	tabWaveformOut = waveformOut.row
	for signalSelect in waveformSelect:
		tabWaveformOut[keyWaveform] = signalSelect
		tabWaveformOut.append()
	
	waveformOut.flush()


def copySelectedSlicesTelescope(telNodeOut, telNodeIn, firstSliceIndex, lastSliceIndex):
	'''
	Create all the telescope with the minimum selection
	Parameters:
	-----------
		telNodeOut : output telescope
		telNodeIn : input telescope
		firstSliceIndex : Index of the first slice to be selected
		lastSliceIndex : Index of the last slice no to be selected
	'''
	selectSliceChannel(telNodeOut.waveformHi, telNodeIn.waveformHi, "waveformHi", firstSliceIndex, lastSliceIndex)
	try:
		selectSliceChannel(telNodeOut.waveformLo, telNodeIn.waveformLo, "waveformLo", firstSliceIndex, lastSliceIndex)
	except Exception as e:
		print(e)


def copySelectedSlicesR1(outFile, inFile, firstSliceIndex, lastSliceIndex):
	'''
	Create all the telescope with the minimum selection
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		firstSliceIndex : Index of the first slice to be selected
		lastSliceIndex : Index of the last slice no to be selected
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			copySelectedSlicesTelescope(telNodeOut, telNodeIn, firstSliceIndex, lastSliceIndex)
		except tables.exceptions.NoSuchNodeError as e:
			pass
	
	


def processSliceSelectionFile(inputFileName, outputFileName, firstSliceIndex, lastSliceIndex, chunkshape=1):
	'''
	Do the slice selection on the input file and create the output file
	Parameters:
	-----------
		inputFileName : name of the input file
		outputFileName : name of the output file
		firstSliceIndex : Index of the first slice to be selected
		lastSliceIndex : Index of the last slice no to be selected
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	inFile = tables.open_file(inputFileName, "r")
	outFile = tables.open_file(outputFileName, "w", filters=inFile.filters)
	outFile.title = inFile.title
	#Copy the instrument and simulation groups
	try:
		outFile.copy_node(inFile.root.instrument, newparent=outFile.root, recursive=True)
	except:
		pass
	try:
		outFile.copy_node(inFile.root.simulation, newparent=outFile.root, recursive=True)
	except:
		pass
	
	nbSlice = lastSliceIndex - firstSliceIndex
	createAllTelescopeMinSelected(outFile, inFile, nbSlice, chunkshape=chunkshape)
	copySelectedSlicesR1(outFile, inFile, firstSliceIndex, lastSliceIndex)
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-f', '--first', help="Index of the first slice to be selected", required=True, type=int)
	parser.add_argument('-l', '--last', help="Index of the first last no to be selected", required=True, type=int)
	
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	firstSliceIndex = args.first
	lastSliceIndex = args.last
	
	processSliceSelectionFile(inputFileName, outputFileName, firstSliceIndex, lastSliceIndex)



