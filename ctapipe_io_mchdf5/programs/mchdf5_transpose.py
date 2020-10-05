'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from ctapipe_io_mchdf5.tools.telescope_copy import copy_telescope_without_waveform


def createTransposedWaveformTable(hfile, cam_tel_group, nameWaveformHi, nbSlice, nbPixel, chunkshape=1):
	'''
	Create the table to store the signal without the minimum value and it minimum in an other table
	Parameters:
		hfile : HDF5 file to be used
		cam_tel_group : telescope group in which to put the tables
		nameWaveformHi : name of the table to store the waveform
		nbSlice : number of slices of the signal
		nbPixel : number of pixels of the camera
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	image_shape = (nbPixel, nbSlice)
	columns_dict_waveformHi  = {nameWaveformHi: tables.UInt16Col(shape=image_shape)}
	description_waveformHi = type('description columns_dict_waveformHi', (tables.IsDescription,), columns_dict_waveformHi)
	hfile.create_table(cam_tel_group, nameWaveformHi, description_waveformHi, "Table of waveform of the signal", chunkshape=chunkshape)


def createTelescopeTransposed(outFile, telNode, chunkshape=1):
	'''
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	cam_tel_group = copy_telescope_without_waveform(outFile, telNode, chunkshape)
	print("createTelescopeTransposed : base of telescope copied")
	nbPixel = np.uint64(telNode.nbPixel.read())
	nbSlice = np.uint64(telNode.nbSlice.read())
	
	createTransposedWaveformTable(outFile, cam_tel_group, "waveformHi", nbSlice, nbPixel, chunkshape=chunkshape)
	nbGain = np.uint64(telNode.nbGain.read())
	if nbGain > 1:
		createTransposedWaveformTable(outFile, cam_tel_group, "waveformLo", nbSlice, nbPixel, chunkshape=chunkshape)


def createAllTelescopeTransposed(outFile, inFile, chunkshape=1):
	'''
	Create all the telescope with the minimum selection
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	print("createAllTelescopeTransposed : create r1 group")
	outFile.create_group("/", 'r1', 'Raw data waveform informations of the run')
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			createTelescopeTransposed(outFile, telNode, chunkshape=chunkshape)
		except tables.exceptions.NoSuchNodeError as e:
			print("createAllTelescopeTransposed : error ",e)


def transposeChannel(waveformOut, waveformIn, keyWaveform):
	'''
	Transpose all the telescopes channels (waveformHi and waveformLo)
	Parameters:
	-----------
		waveformOut : signal selected
		waveformIn : signal to be selected
		keyWaveform : name of the desired column in tables waveformOut and waveformIn)
	'''
	waveformIn = waveformIn.col(keyWaveform)
	
	tabWaveformOut = waveformOut.row
	for signalSelect in waveformIn:
		tabWaveformOut[keyWaveform] = signalSelect.swapaxes(0, 1)
		tabWaveformOut.append()
	
	waveformOut.flush()


def copyTransposedTelescope(telNodeOut, telNodeIn):
	'''
	Transpose the telescope data
	Parameters:
	-----------
		telNodeOut : output telescope
		telNodeIn : input telescope
	'''
	print("copyTransposedTelescope : telNodeOut :", telNodeOut)
	transposeChannel(telNodeOut.waveformHi, telNodeIn.waveformHi, "waveformHi")
	try:
		transposeChannel(telNodeOut.waveformLo, telNodeIn.waveformLo, "waveformLo")
	except tables.exceptions.NoSuchNodeError as e:
		print("copyTransposedTelescope : error :",e)


def copyTransposedR1(outFile, inFile):
	'''
	Transpose all the telescopes data
	Parameters:
	-----------
		outFile : output file
		inFile : input file
	'''
	print("copyTransposedR1 : begin")
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			copyTransposedTelescope(telNodeOut, telNodeIn)
		except tables.exceptions.NoSuchNodeError as e:
			print("copyTransposedR1 : error :",e)


def transposeFile(inputFileName, outputFileName):
	'''
	Tranpose the input file into the output file
	Parameters:
		inputFileName : input file to be transposed
		outputFileName : transposed output file
	'''
	inFile = tables.open_file(inputFileName, "r")
	outFile = tables.open_file(outputFileName, "w", filters=inFile.filters)
	
	outFile.title = "R1-V2-PixelSlice"
	
	#Copy the instrument and simulation groups
	try:
		outFile.copy_node(inFile.root.instrument, newparent=outFile.root, recursive=True)
	except:
		pass
	try:
		outFile.copy_node(inFile.root.simulation, newparent=outFile.root, recursive=True)
	except:
		pass
	createAllTelescopeTransposed(outFile, inFile)
	copyTransposedR1(outFile, inFile)
	inFile.close()
	outFile.close()
	


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file (tranposed)", required=True)
	
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	
	transposeFile(inputFileName, outputFileName)



