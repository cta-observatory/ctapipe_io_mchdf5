'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
from .get_telescope_info import *

class SubarrayLayout(tables.IsDescription):
	'''
	Layout of the subarray
	Attributes:
		tel_id : id of the telescope
		pos_x : position of the telescope on the X axix (in meters to the north)
		pos_y : position of the telescope on the Y axix (in meters to the west)
		pos_z : high of the telescope in meters
		name : name of the telescope
		type : type of the telescope
		type_id : type of the telscope in unsigned long (to speed up the access for specific analysis)
		num_mirrors : number of mirror of the telescope
		camera_type : type of the telescope camera
		tel_description : description of the telescope
	'''
	tel_id = tables.UInt64Col()
	pos_x = tables.Float32Col()
	pos_y = tables.Float32Col()
	pos_z = tables.Float32Col()
	name = tables.StringCol(5, dflt=b'')
	type = tables.StringCol(3, dflt=b'')
	type_id = tables.UInt64Col()
	num_mirrors = tables.UInt64Col()
	camera_type = tables.StringCol(9, dflt=b'')
	tel_description = tables.StringCol(14, dflt=b'')


class OpticDescription(tables.IsDescription):
	'''
	Describe the optic of the all the telescopes
	Attributes:
	-----------
		description : description of the telescope optic (one mirror, two, etc)
		name : name of the optic
		type : type of the optic
		mirror_area : area of the mirror in meters square
		num_mirror_tiles : number of mirrors tiles
		equivalent_focal_length : equivalent focal lenght of the mirror in meters
	'''
	description = tables.StringCol(14, dflt=b'')
	name = tables.StringCol(5, dflt=b'')
	type = tables.StringCol(3, dflt=b'')
	mirror_area = tables.Float32Col()
	num_mirrors = tables.UInt64Col()
	num_mirror_tiles = tables.UInt64Col()
	equivalent_focal_length = tables.Float32Col(shape=(), dflt=0.0, pos=6)


def fillSubarrayLayout(hfile, telInfo_from_evt, nbTel):
	'''
	Fill the subarray informations
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
		nbTel : number of telescope in the run
	'''
	tableSubarrayLayout = hfile.root.instrument.subarray.layout
	tabSubLayout = tableSubarrayLayout.row
	
	for telIndexIter in range(0, nbTel):
		telId = telIndexIter + 1
		if telId in telInfo_from_evt:
			telInfo = telInfo_from_evt[telId]
			telType = telInfo[TELINFO_TELTYPE]
			camName = getCameraNameFromType(telType)
			telTypeStr = getTelescopeTypeStrFromCameraType(telType)
			
			tabSubLayout["tel_id"] = np.uint64(telId)
			tabSubLayout["pos_x"] = np.float32(telInfo[TELINFO_TELPOSX])
			tabSubLayout["pos_y"] = np.float32(telInfo[TELINFO_TELPOSY])
			tabSubLayout["pos_z"] = np.float32(telInfo[TELINFO_TELPOSZ])
			tabSubLayout["name"] = camName
			tabSubLayout["type"] = telTypeStr
			tabSubLayout["type_id"] = np.uint64(telType)
			
			tabSubLayout["num_mirrors"] = np.uint64(telInfo[TELINFO_NBMIRROR])
			tabSubLayout["camera_type"] = camName + "Cam"
			tabSubLayout["tel_description"] = "Description"
			tabSubLayout.append()
		else:
			tabSubLayout["tel_id"] = np.uint64(telId)
			tabSubLayout["pos_x"] = np.float32(0.0)
			tabSubLayout["pos_y"] = np.float32(0.0)
			tabSubLayout["pos_z"] = np.float32(0.0)
			tabSubLayout["name"] = ""
			tabSubLayout["type"] = ""
			tabSubLayout["type_id"] = np.uint64(7)
			
			tabSubLayout["num_mirrors"] = np.uint64(0)
			tabSubLayout["camera_type"] = ""
			tabSubLayout["tel_description"] = ""
			tabSubLayout.append()
	tableSubarrayLayout.flush()


def createCameraTable(hfile, telId, telInfo):
	'''
	Create a table to describe a camera
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telId : id of the telescope
		telInfo : table of some informations related to the telescope
	'''
	
	camTelGroup = hfile.create_group("/instrument/subarray/telescope/camera", "Cam_"+str(telId), 'Camera of telescope '+str(telId))
	
	pix_x = np.asarray(telInfo[TELINFO_TABPIXELX], dtype=np.float32)
	hfile.create_array(camTelGroup, 'pix_x', pix_x, "Position of the pixels on the X axis of the camera in meters")
	
	pix_y = np.asarray(telInfo[TELINFO_TABPIXELY], dtype=np.float32)
	hfile.create_array(camTelGroup, 'pix_y', pix_y, "Position of the pixels on the Y axis of the camera in meters")
	
	#You can get it direcly from telInfo if you complete the field
	pix_id = np.arange(0, pix_y.size, dtype=np.uint64)
	hfile.create_array(camTelGroup, 'pix_id', pix_id, "Id of the pixels of the camera")
	
	pix_area = np.float32(0.0)
	hfile.create_array(camTelGroup, 'pix_area', pix_area, "Area of the pixels in meters square")
	
	cameraRotation = np.float32(telInfo[TEL_INFOR_CAMERA_ROTATION])
	hfile.create_array(camTelGroup, 'cam_rotation', cameraRotation, "Rotation of the camera")
	
	pixRotation = np.float32(telInfo[TEL_INFOR_PIX_ROTATION])
	hfile.create_array(camTelGroup, 'pix_rotation', pixRotation, "Rotation of the pixels")


def createInstrumentDataset(hfile, telInfo_from_evt):
	'''
	Create the instrument dataset
	Parameters:
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	'''
	#Group : instrument
	hfile.create_group("/", 'instrument', 'Instrument informations of the run')
	#	Group : instrument/subarray
	subarrayGroup = hfile.create_group("/instrument", 'subarray', 'Subarray of the run')
	hfile.create_table(subarrayGroup, 'layout', SubarrayLayout, "Layout of the subarray")
	#		Group : instrument/subarray/telescope
	subarrayTelescopeGroup = hfile.create_group("/instrument/subarray", 'telescope', 'Telescope of the subarray')
	
	#			Group : instrument/subarray/telescope/camera
	hfile.create_group("/instrument/subarray/telescope", 'camera', 'Camera in the run')
	
	for telId, telInfo in telInfo_from_evt.items():
		createCameraTable(hfile, telId, telInfo)
	
	hfile.create_table(subarrayTelescopeGroup, 'optics', OpticDescription, "Describe the optic of the all the telescopes")


def fillOpticDescription(hfile, telInfo_from_evt, nbTel):
	'''
	Fill the optic description table
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
		nbTel : number of telescope in the run
	'''
	
	tableOptic = hfile.root.instrument.subarray.telescope.optics
	tabOp = tableOptic.row
	for telIndexIter in range(0, nbTel):
		telId = telIndexIter + 1
		if telId in telInfo_from_evt:
			telInfo = telInfo_from_evt[telId]
			telType = telInfo[TELINFO_TELTYPE]
			
			camName = getCameraNameFromType(telType)
			telTypeStr = getTelescopeTypeStrFromCameraType(telType)
			
			tabOp["description"] = "Description"
			tabOp["name"] = camName
			tabOp["type"] = telTypeStr
			tabOp["mirror_area"] = np.float32(telInfo[TELINFO_MIRRORAREA])
			tabOp["num_mirrors"] = np.float32(telInfo[TELINFO_NBMIRROR])
			tabOp["num_mirror_tiles"] = np.float32(telInfo[TELINFO_NBMIRRORTILES])
			tabOp["equivalent_focal_length"] = np.float32(telInfo[TELINFO_FOCLEN])
			tabOp.append()
		else:
			tabOp["description"] = ""
			tabOp["name"] = ""
			tabOp["type"] = ""
			tabOp["mirror_area"] = np.float32(0.0)
			tabOp["num_mirrors"] = np.float32(0.0)
			tabOp["num_mirror_tiles"] = np.float32(0.0)
			tabOp["equivalent_focal_length"] = np.float32(1.0)
			tabOp.append()




