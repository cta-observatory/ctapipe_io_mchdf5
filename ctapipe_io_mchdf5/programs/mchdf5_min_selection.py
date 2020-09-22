'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

from ctapipe_io_mchdf5.tools.min_selection_utils import create_all_telescope_min_selected


def processMinSelectionChannelBlock(tabWaveformMin, keyWaveformMin, tabMin, keyMin, tabWaveformPart):
	'''
	Get the minimum and waveform without minimum and append them in the output tables (block par block function)
	'''
	tabPixelMin = tabWaveformPart.min(axis=(0,1))
	
	tabSubtractWaveformMin = tabWaveformPart - tabPixelMin
	
	tabMin[keyMin] = tabPixelMin
	tabMin.append()
	
	for subtractedSignal in tabSubtractWaveformMin:
		tabWaveformMin[keyWaveformMin] = subtractedSignal
		tabWaveformMin.append()


def processMinSelectionChannel(tableWaveformMin, keyWaveformMin, tableMin, keyMin, waveformInput, keyWaveform, nbEventPerMin):
	'''
	Process the minimum pixel split on a channel
	Parameters:
		tableWaveformMin : table of waveform substracted by their minimum values
		keyWaveformMin : key to get the data into the tableWaveformMin table
		tableMin : table of the minimum values of the waveform
		keyMin : key to get the data into the tableMin table
		waveformInput : input waveform signal table for a channel
		keyWaveform : key to access the data into the waveformInput channel
	'''
	waveformHi = waveformInput.read()
	waveformHi = waveformHi[keyWaveform]
	
	nbEvent = waveformHi.shape[0]
	
	if nbEvent == 0:
		return
	elif nbEvent >= nbEventPerMin:
		nbMinStep = int(nbEvent/nbEventPerMin)
		lastPosition = nbMinStep*nbEventPerMin
		lastminValue = nbEvent - lastPosition
		lastPosition -= 1
		_nbEventPerMin = nbEventPerMin
	else:
		nbMinStep = 1
		lastminValue = 0
		_nbEventPerMin = nbEvent
	
	tabWaveformMin = tableWaveformMin.row
	tabMin = tableMin.row
	print("\n")
	for i in range(0, nbMinStep):
		processMinSelectionChannelBlock(tabWaveformMin, keyWaveformMin, tabMin, keyMin, waveformHi[i:i + _nbEventPerMin])
		print("\r\r\r\r\r\r\r\r\r\r\r\r",i,"/",nbMinStep, end="")
	
	if lastminValue != 0:
		processMinSelectionChannelBlock(tabWaveformMin, keyWaveformMin, tabMin, keyMin, waveformHi[lastPosition:-1])
	tableWaveformMin.flush()
	tableMin.flush()
	print("\nDone for",keyWaveformMin)


def processMinSelectionTelescope(telNodeOut, telNodeIn, nbEventPerMin):
	'''
	Split the signal in minimum values and signal without minimum values
	Parameters:
	-----------
		telNodeOut : telescope from output file
		telNodeIn : telescope from input file
		nbEventPerMin : number of events to be used to compute one minimum
	'''
	#Get the minimum with numpy min function
	processMinSelectionChannel(telNodeOut.waveformHi, "waveformHi", telNodeOut.minHi, "minHi", telNodeIn.waveformHi, "waveformHi", nbEventPerMin)
	
	try:
		processMinSelectionChannel(telNodeOut.waveformLo, "waveformLo", telNodeOut.minLo, "minLo", telNodeIn.waveformLo, "waveformLo", nbEventPerMin)
	except Exception as e:
		pass


def processMinSelectionAllTelescope(outFile, inFile, nbEventPerMin):
	'''
	Split the signal in minimum values and signal without minimum values for all telescopes
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		nbEventPerMin : number of events to be used to compute one minimum
	'''
	for telNodeIn, telNodeOut in zip(inFile.walk_nodes("/r1", "Group"), outFile.walk_nodes("/r1", "Group")):
		try:
			processMinSelectionTelescope(telNodeOut, telNodeIn, nbEventPerMin)
		except tables.exceptions.NoSuchNodeError as e:
			pass


def processMinSelection(inputFileName, outputFileName, nbEventPerMin, chunkshape=1):
	'''
	Process the minimum selection
	Parameters:
	-----------
		inputFileName : name of the input file
		outputFileName : name of the output file
		nbEventPerMin : number of events to be used to compute one minimum
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
	
	create_all_telescope_min_selected(outFile, inFile, nbEventPerMin, chunkshape=chunkshape)
	processMinSelectionAllTelescope(outFile, inFile, nbEventPerMin)
	
	inFile.close()
	outFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file",
						required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 v2 output file",
						required=True)
	parser.add_argument('-n', '--nbeventpermin', help="Number of event to be used to compute the minimum",
						required=True, type=int)
	args = parser.parse_args()

	inputFileName = args.input
	outputFileName = args.output
	nbEventPerMin = args.nbeventpermin
	processMinSelection(inputFileName, outputFileName, nbEventPerMin)





