'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from ctapipe_io_mchdf5.tools.telescope_copy import copy_all_tel_without_waveform
from ctapipe_io_mchdf5.tools.copy_sort import create_sorted_waveform_tableShape

MODE_PES = 0
MODE_PSE = 1
MODE_EPS = 2
MODE_ESP = 3
MODE_SEP = 4
MODE_SPE = 5

def getTitleForOrderMode(orderMode):
	'''
	Get the corresponding title by respect to the order mode
	Parameters:
		orderMode : order in which to store the output table (PES, PSE, EPS, ESP, SEP, SPE)
	'''
	tabStr = ["PES", "PSE", "EPS", "ESP", "SEP", "SPE"]
	return tabStr[orderMode]


def convertStringToOrderMode(inputStr):
	'''
	Convert a string into the selection mode (PES, PSE, EPS, ESP, SEP, SPE)
	Parameters:
		inputStr : string to be converted into the selection mode
	Return:
		corresponding selection mode
	'''
	strLow = inputStr.upper()
	if strLow == "PES":
		return MODE_PES
	elif strLow == "PSE":
		return MODE_PSE
	elif strLow == "EPS":
		return MODE_EPS
	elif strLow == "ESP":
		return MODE_ESP
	elif strLow == "SEP":
		return MODE_SEP
	elif strLow == "SPE":
		return MODE_SPE
	else:
		raise(RuntimeError, "convertStringToOrderMode : unknown mode '" +inputStr + "', expect PES, PSE, EPS, ESP, SEP, SPE")


def getShapeFromOrder(nbEvent, nbSlice, nbPixel, orderMode):
	'''
	Get the proper shape of the data in the table by respect to the orderMode
	Parameters:
		nbEvent : number of events
		nbSlice : number of slices
		nbPixel : number of pixels
		orderMode : order in which to store the output table (PES, PSE, EPS, ESP, SEP, SPE)
	Return:
		shape of the data in the table (nbEvent, nbSlice), (nbSlice, nbEvent), (nbPixel, nbSlice), (nbSlice, nbPixel), (nbEvent, nbPixel), (nbPixel, nbEvent)
	'''
	if orderMode == MODE_PES:
		return (nbEvent, nbSlice)
	elif orderMode == MODE_PSE:
		return (nbSlice, nbEvent)
	elif orderMode == MODE_EPS:
		return (nbPixel, nbSlice)
	elif orderMode == MODE_ESP:
		return (nbSlice, nbPixel)
	elif orderMode == MODE_SEP:
		return (nbEvent, nbPixel)
	elif orderMode == MODE_SPE:
		return (nbPixel, nbEvent)


def getWaveformSwappedFromOrder(waveformESP, orderMode):
	'''
	Swap the axes of the input waveformESP to get the tensor to be stored with the right shape
	Parameters:
		waveformESP : tensor by event, slice, pixel to be swapped
		orderMode : order in which to swap the output table (PES, PSE, EPS, ESP, SEP, SPE)
	Return:
		tensor of values properly swapped
	'''
	if orderMode == MODE_PES:
		waveformPSE = waveformESP.swapaxes(0, 2)
		return waveformPSE.swapaxes(1, 2)
	elif orderMode == MODE_PSE:
		return waveformESP.swapaxes(0, 2)
	elif orderMode == MODE_EPS:
		return waveformESP.swapaxes(1, 2)
	elif orderMode == MODE_ESP:
		return waveformESP
	elif orderMode == MODE_SEP:
		return waveformESP.swapaxes(0, 1)
	elif orderMode == MODE_SPE:
		waveformPSE = waveformESP.swapaxes(0, 2)
		return waveformPSE.swapaxes(0, 1)


def orderSwapChannel(outFile, telNodeOut, waveformIn, keyWaveform, selectionMode):
	'''
	Transpose all the telescopes channels (waveformHi and waveformLo)
	Parameters:
	-----------
		outFile : output file
		telNodeOut : output telescope
		waveformIn : signal to be selected
		keyWaveform : name of the desired column in tables waveformIn
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
	'''
	waveformIn = waveformIn.col(keyWaveform)
	
	shapeStoredData = getShapeFromOrder(waveformIn.shape[0], waveformIn.shape[1], waveformIn.shape[2], selectionMode)
	
	waveformOut = create_sorted_waveform_tableShape(outFile, telNodeOut, keyWaveform, shapeStoredData)
	rowWaveformOut = waveformOut.row
	
	swappedWaveform = getWaveformSwappedFromOrder(waveformIn, selectionMode)
	
	for tableEntry in swappedWaveform:
		rowWaveformOut[keyWaveform] = tableEntry
		rowWaveformOut.append()
	
	waveformOut.flush()



def copySortedTelescope(outFile, telNodeOut, telNodeIn, selectionMode):
	'''
	Transpose the telescope data
	Parameters:
	-----------
		outFile : output file
		telNodeOut : output telescope
		telNodeIn : input telescope
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
	'''
	orderSwapChannel(outFile, telNodeOut, telNodeIn.waveformHi, "waveformHi", selectionMode)
	try:
		orderSwapChannel(outFile, telNodeOut, telNodeIn.waveformLo, "waveformLo", selectionMode)
	except Exception as e:
		print(e)


def copySortedR1(outFile, inFile, selectionMode):
	'''
	Transpose all the telescopes data
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			copySortedTelescope(outFile, telNodeOut, telNodeIn, selectionMode)
		except tables.exceptions.NoSuchNodeError as e:
			pass


def sortPixelFile(inputFileName, outputFileName, selectionMode):
	'''
	Sort the pixel inthe output file
	Parameters:
		inputFileName : input file to be sorted
		outputFileName : sorted output file
		selectionMode : selection mode for pixel order (MEAN, SIGMA, RANGE)
	'''
	inFile = tables.open_file(inputFileName, "r")
	outFile = tables.open_file(outputFileName, "w", filters=inFile.filters)
	
	outFile.title = "R1-V2-" + getTitleForOrderMode(selectionMode)
	
	#Copy the instrument and simulation groups
	try:
		outFile.copy_node(inFile.root.instrument, newparent=outFile.root, recursive=True)
	except:
		pass
	try:
		outFile.copy_node(inFile.root.simulation, newparent=outFile.root, recursive=True)
	except:
		pass
	copy_all_tel_without_waveform(outFile, inFile)
	copySortedR1(outFile, inFile, selectionMode)
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file (sorted)", required=True)
	parser.add_argument('-r', '--order', help="order to store data. PES, PSE, EPS, ESP, SEP, SPE", required=True)
	
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	
	selectionMode = convertStringToOrderMode(args.order)
	
	sortPixelFile(inputFileName, outputFileName, selectionMode)



