"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""


import tables
import numpy as np

from .r0_utils import create_mon_tel_pointing, TELINFO_NBGAIN, TELINFO_NBPIXEL, TELINFO_NBSLICE


def create_dl0_table_tel(hfile, telNode, nbGain, nbPixel, nbSlice, chunkshape=1):
	"""
	Create the waveform tables into the given telescope node
	Parameters:
		hfile : HDF5 file to be used
		telNode : telescope to be completed
		nbGain : number of gains of the camera
		nbPixel : number of pixels
		nbSlice : number of slices
		chunkshape : shape of the chunk to be used to store the data
	"""
	if nbGain > 1:
		pixelLo = hfile.create_vlarray(telNode, "pixelLo", tables.UInt16Atom(shape=()), "table of the index of the pixels which are in low gain mode",)
	pixelWaveform = hfile.create_vlarray(telNode, "pixelWaveform", tables.UInt16Atom(shape=()), "table of the index of the pixels recorded with the waveform",)

	#columns_dict_waveformoffset  = {"waveformoffset": tables.UInt64Col(shape=())}
	#description_waveformoffset = type('description columns_dict_waveformoffset', (tables.IsDescription,), columns_dict_waveformoffset)
	#hfile.create_table(telNode, 'waveformoffset', description_waveformoffset, "Offset of the waveform stored in the waveform table", chunkshape=chunkshape)
	
	columns_dict_waveform  = {"waveform": tables.UInt16Col(shape=nbSlice)}
	description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
	hfile.create_table(telNode, 'waveform', description_waveform, "Table of waveform of the pixel with waveform", chunkshape=chunkshape)
	
	columns_dict_signal  = {
				#"signal": tables.Float32Col(shape=(nbPixel)),
				"signal": tables.Int16Col(shape=(nbPixel)),
				"waveformoffset": tables.UInt64Col(shape=())
			 }
	description_signal = type('description columns_dict_signal', (tables.IsDescription,), columns_dict_signal)
	hfile.create_table(telNode, 'signal', description_signal, "Calibrated and integrated signal", chunkshape=chunkshape)


def create_dl0_tel_group_and_table(hfile, telId, telInfo, chunkshape=1):
	"""
	Create the telescope group and table
	It is important not to add an other dataset with the type of the camera to simplify the serach of a telescope by telescope index in the file structure
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telId : id of the telescope
		telInfo : table of some informations related to the telescope
		chunkshape : shape of the chunk to be used to store the data
	"""
	cam_tel_group = create_mon_tel_pointing(hfile, telId, telInfo, chunkshape=chunkshape)
	
	nbGain = np.uint64(telInfo[TELINFO_NBGAIN])
	nbPixel = np.uint64(telInfo[TELINFO_NBPIXEL])
	nbSlice = np.uint64(telInfo[TELINFO_NBSLICE])
	
	create_dl0_table_tel(hfile, cam_tel_group, nbGain, nbPixel, nbSlice, chunkshape=chunkshape)


def createDL0Dataset(hfile, telInfo_from_evt):
	"""
	Create the dl0 dataset
	Parameters:
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	"""
	# Group : dl0
	hfile.create_group("/", 'dl0', 'Raw data DL0 waveform and integrated signal informations of the run')
	
	# The group in the dl0 group will be completed on the fly with the informations collected in telInfo_from_evt
	for telId, telInfo in telInfo_from_evt.items():
		create_dl0_tel_group_and_table(hfile, telId, telInfo)

