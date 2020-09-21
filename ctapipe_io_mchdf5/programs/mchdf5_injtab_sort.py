'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from ctapipe_io_mchdf5.tools.copy_sort import create_all_telescope_sorted


def sortChannel(outFile, telNodeOut, waveformOut, waveformIn, keyWaveform, nbPixel, tabInjName, isStoreSlicePixel, injunctionTable):
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
		injunctionTable : injunction table to be used
	'''
	waveformIn = waveformIn.col(keyWaveform)
	waveformInSwap = waveformIn.swapaxes(1,2)
	
	outFile.create_array(telNodeOut, tabInjName, injunctionTable, "Injunction table to store the pixels order of a channel")
	tabWaveformOut = waveformOut.row
	if injunctionTable.size == waveformIn.shape[2]:
		for signalSelect in waveformInSwap:
			tabTmp = signalSelect[injunctionTable]
			if isStoreSlicePixel:
				tabTmp = tabTmp.swapaxes(0, 1)
			
			tabWaveformOut[keyWaveform] = tabTmp
			tabWaveformOut.append()
	else:
		for signalSelect in waveformInSwap:
			tabTmp = signalSelect
			if isStoreSlicePixel:
				tabTmp = tabTmp.swapaxes(0, 1)
			tabWaveformOut[keyWaveform] = tabTmp
			tabWaveformOut.append()
	
	waveformOut.flush()


def copySortedTelescope(outFile, telNodeOut, telNodeIn, isStoreSlicePixel, injunctionTable):
	'''
	Transpose the telescope data
	Parameters:
	-----------
		outFile : output file
		telNodeOut : output telescope
		telNodeIn : input telescope
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		injunctionTable : injunction table to be used
	'''
	nbPixel = np.uint64(telNodeIn.nbPixel.read())
	sortChannel(outFile, telNodeOut, telNodeOut.waveformHi, telNodeIn.waveformHi, "waveformHi", nbPixel, "orderHi", isStoreSlicePixel, injunctionTable)
	try:
		sortChannel(outFile, telNodeOut, telNodeOut.waveformLo, telNodeIn.waveformLo, "waveformLo", nbPixel, "orderLo", isStoreSlicePixel, injunctionTable)
	except Exception as e:
		print(e)


def copySortedR1(outFile, inFile, isStoreSlicePixel, injunctionTable):
	'''
	Transpose all the telescopes data
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		injunctionTable : injunction table to be used
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			copySortedTelescope(outFile, telNodeOut, telNodeIn, isStoreSlicePixel, injunctionTable)
		except tables.exceptions.NoSuchNodeError as e:
			pass


def sortPixelFile(inputFileName, outputFileName, isStoreSlicePixel, injunctionTable):
	'''
	Sort the pixel inthe output file
	Parameters:
		inputFileName : input file to be sorted
		outputFileName : sorted output file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		injunctionTable : injunction table to be used
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
	copySortedR1(outFile, inFile, isStoreSlicePixel, injunctionTable)
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file (sorted)", required=True)
	parser.add_argument('-p', '--pixelslice', help="store data by (pixel, slice)", required=False)
	parser.add_argument('-s', '--slicepixel', help="store data by (slice, pixel) default", required=False)
	parser.add_argument('-t', '--injtab', help="injunction table file containing uint16", required=True)
	
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	
	injunctionTable = np.fromfile(args.injtab, dtype=np.uint16)
	
	isStoreSlicePixel = True
	if args.pixelslice != None:
		isStoreSlicePixel = False
	if args.slicepixel != None:
		isStoreSlicePixel = True
	
	sortPixelFile(inputFileName, outputFileName, isStoreSlicePixel, injunctionTable)



