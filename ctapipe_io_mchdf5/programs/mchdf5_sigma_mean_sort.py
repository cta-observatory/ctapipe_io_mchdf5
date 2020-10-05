'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from ctapipe_io_mchdf5.tools.copy_sort import create_all_telescope_sorted


def applyInjunctionTableOnMatrix(signalSelect, injunctionTable):
	'''
	Apply the injunction talbe on the input matrix
	Parameters:
		signalSelect : matrix of the signal (pixel, slice) to be used
		injunctionTable : injunction table to be used
	Return:
		matrix with swaped rows according to the injunction table
	'''
	matOut = np.zeros(signalSelect.shape, dtype=signalSelect.dtype)
	
	for inputRow, rowIndex in zip(signalSelect, injunctionTable):
		matOut[rowIndex][:] = inputRow[:]
	
	return matOut


def sortChannel(outFile, telNodeOut, waveformOut, waveformIn, keyWaveform, nbPixel, tabInjName, isStoreSlicePixel):
	'''
	Transpose all the telescopes channels (waveformHi and waveformLo)
	Parameters:
	-----------
		telNodeOut : output telescope
		waveformOut : signal selected
		waveformIn : signal to be selected
		keyWaveform : name of the desired column in tables waveformOut and waveformIn)
		nbPixel : number of pixel in the camera
		tabInjName : name of the injunction table array
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
	'''
	waveformIn = waveformIn.col(keyWaveform)
	waveformInSwap = waveformIn.swapaxes(1,2)
	#Get mean and standard deviation
	tabMean = np.mean(waveformIn, axis=(0, 1))
	tabSigma = np.std(waveformIn, axis=(0, 1))
	#Index of the pixels
	tabIndex = np.arange(0, nbPixel)
	
	matMeanSigmaIndex = np.ascontiguousarray(np.stack((tabSigma, tabMean, tabIndex)).T)
	matRes = np.sort(matMeanSigmaIndex.view('f8,f8,f8'), order=['f0', 'f1'], axis=0).view(np.float64)
	injunctionTable = matRes[:,2].astype(np.uint64)
	
	outFile.create_array(telNodeOut, tabInjName, injunctionTable, "Injunction table to store the pixels order of a channel")
	
	tabWaveformOut = waveformOut.row
	for signalSelect in waveformInSwap:
		tabTmp = applyInjunctionTableOnMatrix(signalSelect, injunctionTable)
		if isStoreSlicePixel:
			tabTmp = tabTmp.swapaxes(0, 1)
		
		tabWaveformOut[keyWaveform] = tabTmp
		tabWaveformOut.append()
	
	waveformOut.flush()


def copySortedTelescope(outFile, telNodeOut, telNodeIn, isStoreSlicePixel):
	'''
	Transpose the telescope data
	Parameters:
	-----------
		outFile : output file
		telNodeOut : output telescope
		telNodeIn : input telescope
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
	'''
	nbPixel = np.uint64(telNodeIn.nbPixel.read())
	sortChannel(outFile, telNodeOut, telNodeOut.waveformHi, telNodeIn.waveformHi, "waveformHi", nbPixel, "orderHi", isStoreSlicePixel)
	try:
		sortChannel(outFile, telNodeOut, telNodeOut.waveformLo, telNodeIn.waveformLo, "waveformLo", nbPixel, "orderLo", isStoreSlicePixel)
	except Exception as e:
		print(e)


def copySortedR1(outFile, inFile, isStoreSlicePixel):
	'''
	Transpose all the telescopes data
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			copySortedTelescope(outFile, telNodeOut, telNodeIn, isStoreSlicePixel)
		except tables.exceptions.NoSuchNodeError as e:
			pass


def sortPixelFile(inputFileName, outputFileName, isStoreSlicePixel):
	'''
	Sort the pixel inthe output file
	Parameters:
		inputFileName : input file to be sorted
		outputFileName : sorted output file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
	'''
	inFile = tables.open_file(inputFileName, "r")
	outFile = tables.open_file(outputFileName, "w", filters=inFile.filters)
	
	if isStoreSlicePixel:
		outFile.title = "R1-V2-sortedSlicePixel"
	else:
		outFile.title = "R1-V2-sortedPixelSlice"
	
	#Copy the instrument and simulation groups
	try:
		outFile.copy_node(inFile.root.instrument, newparent=outFile.root, recursive=True)
	except:
		pass
	try:
		outFile.copy_node(inFile.root.simulation, newparent=outFile.root, recursive=True)
	except:
		pass
	create_all_telescope_sorted(outFile, inFile, isStoreSlicePixel)
	copySortedR1(outFile, inFile, isStoreSlicePixel)
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file (sorted)", required=True)
	parser.add_argument('-p', '--pixelslice', help="store data by (pixel, slice)", required=False)
	parser.add_argument('-s', '--slicepixel', help="store data by (slice, pixel) default", required=False)
	
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	
	isStoreSlicePixel = True
	if args.pixelslice != None:
		isStoreSlicePixel = False
	if args.slicepixel != None:
		isStoreSlicePixel = True
	
	sortPixelFile(inputFileName, outputFileName, isStoreSlicePixel)



