
# coding: utf-8

"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

import tables
from ctapipe.io import event_source
import argparse

from ..tools.get_nb_tel import getNbTel
from ..tools.r0_file import (create_file_structure,
							 open_output_file)
from ..tools.r0_utils import (append_event_telescope_data,
							  flush_r0_tables)
from ..tools.get_telescope_info import (get_telescope_info_from_event,
										check_is_simulation_file)
from ..tools.simulation_utils import (append_corsika_event,
									  fill_simulation_header_info)
from ..tools.instrument_utils import (fill_subarray_layout,
									  fill_optic_description)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="simtel input file",
						required=True)
	parser.add_argument('-o', '--output', help="hdf5 r0 output file",
						required=True)
	parser.add_argument('-m', '--max_event', help="maximum event to reconstruct",
						required=False, type=int)
	parser.add_argument('-c', '--compression',
						help="compression level for the output file [0 (No compression), 1 - 9]. Default = 6",
						required=False, type=int, default='6')
	parser.add_argument('-z', '--zfits',
						help="To be used for a zfits convertion to HDF5",
						required=False, type=bool, default=False)
	args = parser.parse_args()

	inputFileName = args.input
	nbTel = getNbTel(inputFileName)
	print("Number of telescope : ", nbTel)

	# Increase the number of nodes in cache if necessary (avoid warning about nodes reopening)
	tables.parameters.NODE_CACHE_SLOTS = max(tables.parameters.NODE_CACHE_SLOTS, 3*nbTel + 20)

	telInfo_from_evt, nbEvent = get_telescope_info_from_event(inputFileName, nbTel)
	print("Found", nbEvent, "events")
	hfile = open_output_file(args.output, compressionLevel=args.compression)

	print('Create file structure')
	tableMcCorsikaEvent = create_file_structure(hfile, telInfo_from_evt)

	print('Fill the subarray layout information')
	fill_subarray_layout(hfile, telInfo_from_evt, nbTel)
	
	isSimulationMode = not args.zfits
	print("Is simulation mode :",isSimulationMode)
	
	check_is_simulation_file(telInfo_from_evt)

	if isSimulationMode:
		print('Fill the optic description of the telescopes')
		fill_optic_description(hfile, telInfo_from_evt, nbTel)

		print('Fill the simulation header information')
		fill_simulation_header_info(hfile, inputFileName)

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
			append_corsika_event(tableMcCorsikaEvent, event)
		append_event_telescope_data(hfile, event)
		nb_event += 1
		print("\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r{} / {}".format(nb_event, max_event), end="")
		if nb_event >= max_event:
			break
	print("\nFlushing tables")
	if isSimulationMode:
		tableMcCorsikaEvent.flush()

	flush_r0_tables(hfile)
	hfile.close()
	print('\nDone')


if __name__ == '__main__':
	main()
