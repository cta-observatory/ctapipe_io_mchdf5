
# coding: utf-8

'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
from ctapipe.io import event_source
import argparse

from ..tools.get_nb_tel import getNbTel
from ..tools.r1_file import *
from ..tools.r1_utils import *
from ..tools.get_telescope_info import *
from ..tools.simulation_utils import *
from ..tools.instrument_utils import *


def createFileStructure(hfile, telInfo_from_evt):
	'''
	Create the structure of the HDF5 file
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	Return:
	-------
		table of mc_event
	'''
	createR1Dataset(hfile, telInfo_from_evt)
	createInstrumentDataset(hfile, telInfo_from_evt)
	tableMcEvent = createSimiulationDataset(hfile)
	return tableMcEvent


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="simtel input file",
						required=True)
	parser.add_argument('-o', '--output', help="hdf5 r1 output file",
						required=True)
	parser.add_argument('-m', '--max_event', help="maximum event to reconstruct",
						required=False, type=int)
	parser.add_argument('-c', '--compression',
						help="compression level for the output file [0 (No compression), 1 - 9]. Default = 6",
						required=False, type=int, default='6')
	args = parser.parse_args()

	inputFileName = args.input
	nbTel = getNbTel(inputFileName)
	print("Number of telescope : ", nbTel)
	
	#Increase the number of nodes in cache if necessary (avoid warning about nodes reopening)
	tables.parameters.NODE_CACHE_SLOTS = max(tables.parameters.NODE_CACHE_SLOTS, 3*nbTel + 20)
	
	telInfo_from_evt, nbEvent = getTelescopeInfoFromEvent(inputFileName, nbTel)
	print("Found", nbEvent, "events")
	hfile = openOutputFile(args.output, compressionLevel=args.compression)
	
	print('Create file structure')
	tableMcCorsikaEvent = createFileStructure(hfile, telInfo_from_evt)
	
	print('Fill the subarray layout information')
	fillSubarrayLayout(hfile, telInfo_from_evt, nbTel)
	
	isSimulationMode = checkIsSimulationFile(telInfo_from_evt)
	
	if isSimulationMode:
		print('Fill the optic description of the telescopes')
		fillOpticDescription(hfile, telInfo_from_evt, nbTel)
		
		print('Fill the simulation header information')
		fillSimulationHeaderInfo(hfile, inputFileName)
	
	source = event_source(inputFileName)
	
	nb_event = 0
	max_event = 10000000
	if args.max_event != None:
		max_event = int(args.max_event)
	else:
		max_event = nbEvent
	print("\n")
	for event in source:
		if isSimulationMode:
			appendCorsikaEvent(tableMcCorsikaEvent, event)
		appendEventTelescopeData(hfile, event)
		nb_event += 1
		print("\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r{} / {}".format(nb_event, max_event), end="")
		if nb_event >= max_event:
			break
	print("\nFlushing tables")
	if isSimulationMode:
		tableMcCorsikaEvent.flush()
		
	flushR1Tables(hfile)
	hfile.close()
	print('\nDone')


if __name__ == '__main__':
	main()
