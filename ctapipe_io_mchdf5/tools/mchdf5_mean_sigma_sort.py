'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from .telescope_copy import copyTelescopeWithoutWaveform

def createSortedWaveformTable(hfile, camTelGroup, nameWaveformHi, nbSlice, nbPixel, chunkshape=1):
	'''
	Create the table to store the signal
	Parameters:
		hfile : HDF5 file to be used
		camTelGroup : telescope group in which to put the tables
		nameWaveformHi : name of the table to store the waveform
		nbSlice : number of slices of the signal
		nbPixel : number of pixels of the camera
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	image_shape = (nbPixel, nbSlice)
	columns_dict_waveformHi  = {nameWaveformHi: tables.UInt16Col(shape=image_shape)}
	description_waveformHi = type('description columns_dict_waveformHi', (tables.IsDescription,), columns_dict_waveformHi)
	hfile.create_table(camTelGroup, nameWaveformHi, description_waveformHi, "Table of waveform of the signal", chunkshape=chunkshape)


def createTelescopeSorted(outFile, telNode, chunkshape=1):
	'''
	Create the telescope group and table
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	camTelGroup = copyTelescopeWithoutWaveform(outFile, telNode, chunkshape)
	
	nbPixel = np.uint64(telNode.nbPixel.read())
	nbSlice = np.uint64(telNode.nbSlice.read())
	
	createSortedWaveformTable(outFile, camTelGroup, "waveformHi", nbSlice, nbPixel, chunkshape=chunkshape)
	nbGain = np.uint64(telNode.nbGain.read())
	if nbGain > 1:
		createSortedWaveformTable(outFile, camTelGroup, "waveformLo", nbSlice, nbPixel, chunkshape=chunkshape)


def createAllTelescopeSorted(outFile, inFile, chunkshape=1):
	'''
	Create all the telescope ready for pixels sorting
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	outFile.create_group("/", 'r1', 'Raw data waveform informations of the run')
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			createTelescopeSorted(outFile, telNode, chunkshape=chunkshape)
		except tables.exceptions.NoSuchNodeError as e:
			pass



def applyInjunctionTableOnMatrix(signalSelect, injunctionTable):
	'''
	Apply the injunction talbe on the input matrix
	Parameters:
		signalSelect : matrix of the signal (pixel, slice) to be used
		injunctionTable : injunction table to be used
	Return:
		matrix with swaped rows according to the injunction table
	'''
	matOut = np.zero(signalSelect.shape, dtype=signalSelect.dtype)
	
	for inputRow, rowIndex in zip(signalSelect, injunctionTable):
		matOut[rowIndex][:] = inputRow[:]
	
	return matOut


def sortChannel(waveformOut, waveformIn, keyWaveform, nbPixel):
	'''
	Transpose all the telescopes channels (waveformHi and waveformLo)
	Parameters:
	-----------
		waveformOut : signal selected
		waveformIn : signal to be selected
		keyWaveform : name of the desired column in tables waveformOut and waveformIn)
		nbPixel : number of pixel in the camera
	'''
	waveformIn = waveformIn.col(keyWaveform)
	waveformInSwap = waveformIn.swapaxes(1,2)
	#Get mean and standard deviation
	tabMean = np.mean(waveformLo, axis=(0, 1))
	tabSigma = np.std(waveformLo, axis=(0, 1))
	#Index of the pixels
	tabIndex = np.arange(0, nbPixel)
	
	matMeanSigmaIndex = np.ascontiguousarray(np.stack((tabMean, tabSigma, tabIndex)).T)
	matRes = np.sort(matMeanSigmaIndex.view('f8,f8,f8'), order=['f0', 'f1'], axis=0).view(np.float64)
	injunctionTable = matResHi[:,2]
	
	tabWaveformOut = waveformOut.row
	for signalSelect in waveformInSwap:
		tabWaveformOut[keyWaveform] = applyInjunctionTableOnMatrix(signalSelect, injunctionTable)
		tabWaveformOut.append()
	
	waveformOut.flush()


def copySortedTelescope(telNodeOut, telNodeIn):
	'''
	Transpose the telescope data
	Parameters:
	-----------
		telNodeOut : output telescope
		telNodeIn : input telescope
	'''
	nbPixel = np.uint64(telNodeIn.nbPixel.read())
	sortChannel(telNodeOut.waveformHi, telNodeIn.waveformHi, "waveformHi", nbPixel)
	try:
		sortChannel(telNodeOut.waveformLo, telNodeIn.waveformLo, "waveformLo", nbPixel)
	except Exception as e:
		print(e)


def copySortedR1(outFile, inFile):
	'''
	Transpose all the telescopes data
	Parameters:
	-----------
		outFile : output file
		inFile : input file
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			copySortedTelescope(telNodeOut, telNodeIn)
		except tables.exceptions.NoSuchNodeError as e:
			pass


def sortPixelFile(inputFileName, outputFileName):
	'''
	Sort the pixel inthe output file
	Parameters:
		inputFileName : input file to be sorted
		outputFileName : sorted output file
	'''
	inFile = tables.open_file(inputFileName, "r")
	outFile = tables.open_file(outputFileName, "w", filters=inFile.filters)
	
	outFile.title = "R1-V2-sorted"
	
	#Copy the instrument and simulation groups
	try:
		outFile.copy_node(inFile.root.instrument, newparent=outFile.root, recursive=True)
	except:
		pass
	try:
		outFile.copy_node(inFile.root.simulation, newparent=outFile.root, recursive=True)
	except:
		pass
	createAllTelescopeSorted(outFile, inFile)
	copySortedR1(outFile, inFile)
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file (sorted)", required=True)
	
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	
	sortPixelFile(inputFileName, outputFileName)



