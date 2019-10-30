'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from ctapipe_io_mchdf5.tools.copy_sort import createAllTelescopeSorted

MODE_RANGE = 0
MODE_MEAN = 1
MODE_SIGMA = 2
MODE_MIN = 3
MODE_MAX = 4

def convertStringToSelectionMode(inputStr):
	'''
	Convert a string into the selection mode
	Parameters:
		inputStr : string to be converted into the selection mode
	Return:
		corresponding selection mode
	'''
	strLow = inputStr.lower()
	if strLow == "range":
		return MODE_RANGE
	elif strLow == "mean":
		return MODE_MEAN
	elif strLow == "sigma":
		return MODE_SIGMA
	elif strLow == "min":
		return MODE_MIN
	elif strLow == "max":
		return MODE_MAX
	else:
		raise(RuntimeError, "convertStringToSelectionMode : unknown mode '" +inputStr + "', expect RANGE, MEAN, SIGMA, MIN, MAX")



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
	
	#Encode
	for i, rowIndex in enumerate(injunctionTable):
		matOut[i][:] = signalSelect[rowIndex][:]
	
	#Decode
	#for inputRow, rowIndex in zip(signalSelect, injunctionTable):
		#matOut[rowIndex][:] = inputRow[:]
	
	return matOut


def getSelectionMean(waveformIn, tabIndex):
	'''
	Create the injunction table with mean mode
	Parameters:
		waveformIn : signal to be used
		tabIndex : table of the index of the pixels
	'''
	tabMean = np.mean(waveformIn, axis=(0, 1))
	matMeanSigmaIndex = np.ascontiguousarray(np.stack((tabMean, tabIndex)).T)
	matRes = np.sort(matMeanSigmaIndex.view('f8,f8'), order=['f0'], axis=0).view(np.float64)
	injunctionTable = matRes[:,1].astype(np.uint64)
	return injunctionTable


def getSelectionMin(waveformIn, tabIndex):
	'''
	Create the injunction table with min mode
	Parameters:
		waveformIn : signal to be used
		tabIndex : table of the index of the pixels
	'''
	tabMin = np.min(waveformIn, axis=(0, 1))
	matMinSigmaIndex = np.ascontiguousarray(np.stack((tabMin, tabIndex)).T)
	matRes = np.sort(matMinSigmaIndex.view('f8,f8'), order=['f0'], axis=0).view(np.float64)
	injunctionTable = matRes[:,1].astype(np.uint64)
	return injunctionTable


def getSelectionMax(waveformIn, tabIndex):
	'''
	Create the injunction table with min mode
	Parameters:
		waveformIn : signal to be used
		tabIndex : table of the index of the pixels
	'''
	tabMax = np.max(waveformIn, axis=(0, 1))
	matMaxIndex = np.ascontiguousarray(np.stack((tabMax, tabIndex)).T)
	matRes = np.sort(matMaxIndex.view('f8,f8'), order=['f0'], axis=0).view(np.float64)
	injunctionTable = matRes[:,1].astype(np.uint64)
	return injunctionTable


def getSelectionRange(waveformIn, tabIndex):
	'''
	Create the injunction table with range mode
	Parameters:
		waveformIn : signal to be used
		tabIndex : table of the index of the pixels
	'''
	#Get mean and standard deviation
	tabMin = np.min(waveformIn, axis=(0, 1))
	tabMax = np.max(waveformIn, axis=(0, 1))
	
	tabRange = tabMax - tabMin
	matMeanSigmaIndex = np.ascontiguousarray(np.stack((tabRange, tabIndex)).T)
	matRes = np.sort(matMeanSigmaIndex.view('f8,f8'), order=['f0'], axis=0).view(np.float64)
	injunctionTable = matRes[:,1].astype(np.uint64)
	return injunctionTable


def getSelectionSigma(waveformIn, tabIndex):
	'''
	Create the injunction table with mean mode
	Parameters:
		waveformIn : signal to be used
		tabIndex : table of the index of the pixels
	'''
	tabSigma = np.std(waveformIn, axis=(0, 1))
	matMeanSigmaIndex = np.ascontiguousarray(np.stack((tabSigma, tabIndex)).T)
	matRes = np.sort(matMeanSigmaIndex.view('f8,f8'), order=['f0'], axis=0).view(np.float64)
	injunctionTable = matRes[:,1].astype(np.uint64)
	return injunctionTable


def getInjunctionTableFromData(waveformIn, tabIndex, selectionMode):
	'''
	Create the injunction table by respect to the selected mode
	Parameters:
		waveformIn : signal to be used
		tabIndex : table of the index of the pixels
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
	'''
	if selectionMode == MODE_MEAN:
		return getSelectionMean(waveformIn, tabIndex)
	elif selectionMode == MODE_MIN:
		return getSelectionMin(waveformIn, tabIndex)
	elif selectionMode == MODE_RANGE:
		return getSelectionRange(waveformIn, tabIndex)
	elif selectionMode == MODE_SIGMA:
		return getSelectionSigma(waveformIn, tabIndex)
	elif selectionMode == MODE_MAX:
		return getSelectionMax(waveformIn, tabIndex)
	else:
		return tabIndex


def sortChannelBlock(rowWaveformOut, waveformIn, keyWaveform, tabIndex, isStoreSlicePixel, selectionMode, rowInjTab):
	'''
	Sort a block of a channel
	Parameters:
		rowWaveformOut : row to append the sorted signal
		waveformIn : signal to be selected
		keyWaveform : name of the desired column in tables waveformOut and waveformIn)
		tabIndex : table of the index of the pixels
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
		tableInjTab : table of the injunction tables
	'''
	waveformInSwap = waveformIn.swapaxes(1,2)
	injunctionTable = getInjunctionTableFromData(waveformIn, tabIndex, selectionMode)
	
	#TODO : put the right valuesfor first and last event id
	rowInjTab["first_event_id"] = 0
	rowInjTab["last_event_id"] = 0
	rowInjTab["tabinj"] = injunctionTable
	rowInjTab.append()
	
	for signalSelect in waveformInSwap:
		tabTmp = applyInjunctionTableOnMatrix(signalSelect, injunctionTable)
		if isStoreSlicePixel:
			tabTmp = tabTmp.swapaxes(0, 1)
		
		rowWaveformOut[keyWaveform] = tabTmp
		rowWaveformOut.append()


def sortChannel(waveformOut, waveformIn, keyWaveform, nbPixel, tabInjName,
		isStoreSlicePixel, selectionMode, nbEventPerInjTab, tableInjTab):
	'''
	Transpose all the telescopes channels (waveformHi and waveformLo)
	Parameters:
	-----------
		waveformOut : signal selected
		waveformIn : signal to be selected
		keyWaveform : name of the desired column in tables waveformOut and waveformIn)
		nbPixel : number of pixel in the camera
		tabInjName : name of the injunction table array
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
		nbEventPerInjTab : number of event to be treated with the same injunction table
		tableInjTab : table of the injunction tables
	'''
	waveformIn = waveformIn.col(keyWaveform)
	rowWaveformOut = waveformOut.row
	rowInjTab = tableInjTab.row
	#Index of the pixels
	tabIndex = np.arange(0, nbPixel)
	if nbEventPerInjTab == 0:
		sortChannelBlock(rowWaveformOut, waveformIn, keyWaveform, tabIndex, isStoreSlicePixel, selectionMode, rowInjTab)
	else:
		nbEvent = waveformIn.shape[0]
		nbBlock = int(nbEvent/nbEventPerInjTab)
		lastBlockEventIndex = nbEventPerInjTab*nbBlock - 1
		sizeLastBlock = nbEvent - nbEventPerInjTab*nbBlock
		for i in range(0, nbBlock):
			sortChannelBlock(rowWaveformOut, waveformIn[i*nbEventPerInjTab:(i+1)*nbEventPerInjTab],
					keyWaveform, tabIndex, isStoreSlicePixel, selectionMode, rowInjTab)
		if sizeLastBlock != 0:
			sortChannelBlock(rowWaveformOut, waveformIn[lastBlockEventIndex:-1],
					keyWaveform, tabIndex, isStoreSlicePixel, selectionMode, rowInjTab)
	tableInjTab.flush()
	waveformOut.flush()


def createInjunctionTabTable(hfile, camTelGroup, nameTable, nbPixel, chunkshape=1):
	'''
	Create the table to store the signal
	Parameters:
		hfile : HDF5 file to be used
		camTelGroup : telescope group in which to put the tables
		nameTable : name of the table to store the injunction tables
		nbPixel : number of pixels of the camera
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	Return:
		Created table
	'''
	columns_dict_tabInj  = {"first_event_id" :  tables.UInt64Col(),
				"last_event_id" :  tables.UInt64Col(),
				"tabinj": tables.UInt16Col(shape=nbPixel)}
	
	description_tabInj = type('description columns_dict_tabInj', (tables.IsDescription,), columns_dict_tabInj)
	return hfile.create_table(camTelGroup, nameTable, description_tabInj, "Injunction tables of the signal", chunkshape=chunkshape)


def copySortedTelescope(outFile, telNodeOut, telNodeIn, isStoreSlicePixel, selectionMode, nbEventPerInjTab):
	'''
	Transpose the telescope data
	Parameters:
	-----------
		outFile : output file
		telNodeOut : output telescope
		telNodeIn : input telescope
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
		nbEventPerInjTab : number of event to be treated with the same injunction table
	'''
	nbPixel = np.uint64(telNodeIn.nbPixel.read())
	tableInjTabHi = createInjunctionTabTable(outFile, telNodeOut, "injunctionHi", nbPixel)
	sortChannel(telNodeOut.waveformHi, telNodeIn.waveformHi, "waveformHi", nbPixel, "orderHi",
			isStoreSlicePixel, selectionMode, nbEventPerInjTab, tableInjTabHi)
	tableInjTabHi.flush()
	try:
		tableInjTabLo = createInjunctionTabTable(outFile, telNodeOut, "injunctionLo", nbPixel)
		sortChannel(telNodeOut.waveformLo, telNodeIn.waveformLo, "waveformLo", nbPixel, "orderLo",
				isStoreSlicePixel, selectionMode, nbEventPerInjTab, tableInjTabLo)
		tableInjTabLo.flush()
	except Exception as e:
		print(e)


def copySortedR1(outFile, inFile, isStoreSlicePixel, selectionMode, nbEventPerInjTab):
	'''
	Transpose all the telescopes data
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
		nbEventPerInjTab : number of event to be treated with the same injunction table
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			copySortedTelescope(outFile, telNodeOut, telNodeIn, isStoreSlicePixel, selectionMode, nbEventPerInjTab)
		except tables.exceptions.NoSuchNodeError as e:
			pass


def sortPixelFile(inputFileName, outputFileName, isStoreSlicePixel, selectionMode, nbEventPerInjTab):
	'''
	Sort the pixel inthe output file
	Parameters:
		inputFileName : input file to be sorted
		outputFileName : sorted output file
		isStoreSlicePixel : true to store data per slice and pixel, false for pixel and slice
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
		nbEventPerInjTab : number of event to be treated with the same injunction table
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
	createAllTelescopeSorted(outFile, inFile, isStoreSlicePixel)
	copySortedR1(outFile, inFile, isStoreSlicePixel, selectionMode, nbEventPerInjTab)
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file (sorted)", required=True)
	parser.add_argument('-r', '--order', help="order to store data. slicepixel : (slice, pixel) default, or pixelslice (pixel, slice)", required=False)
	parser.add_argument('-n', '--nbeventperInjTab', help="number of events per injunction table (0 mean all the events)", required=True, type=int)
	parser.add_argument('-m', '--selectionmode', help="mode of the pixels selection (RANGE, MEAN, SIGMA, MIN, MAX)", required=True)
	
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	
	isStoreSlicePixel = True
	if args.order != None:
		if args.order in ["pixelslice", "slicepixel"]:
			isStoreSlicePixel = args.order == "slicepixel"
	
	selectionMode = convertStringToSelectionMode(args.selectionmode)
	nbEventPerInjTab = args.nbeventperInjTab
	
	sortPixelFile(inputFileName, outputFileName, isStoreSlicePixel, selectionMode, nbEventPerInjTab)



