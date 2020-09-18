
'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables

from .simulation_utils import create_simulation_dataset
from .instrument_utils import create_instrument_dataset
from .r0_utils import create_r0_dataset


def open_output_file(fileName, compressionLevel=0):
	'''
	Open the output HDF5 file to be used
	Parameters:
		fileName : name of the file to be opened
		compressionLevel : expected compression level (from 0 (no compression, default) to 9)
	'''
	if compressionLevel == 0:
		hfile = tables.open_file(fileName, mode = "w")
		hfile.title = "R0-V2"
		return hfile
	else:
		zstdFilter = tables.Filters(complevel=compressionLevel, complib='blosc:zstd', shuffle=False, bitshuffle=False, fletcher32=False)
		hfile = tables.open_file(fileName, mode = "w", filters=zstdFilter)
		hfile.title = "R0-V2"
		return hfile
	

def create_file_structure(hfile, telInfo_from_evt, enableSimulation=True):
	'''
	Create the structure of the HDF5 file
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
		enableSimulation : True (default) enable the creation of the simulation structure, False disable this creation
	Return:
	-------
		table of mc_event or None if enableSimulation==False
	'''
	create_r0_dataset(hfile, telInfo_from_evt)
	create_instrument_dataset(hfile, telInfo_from_evt)
	if enableSimulation:
		tableMcEvent = create_simulation_dataset(hfile)
		return tableMcEvent
	else:
		return None


