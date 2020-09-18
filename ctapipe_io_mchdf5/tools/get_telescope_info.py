'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import numpy as np

try:
	from ctapipe.io import event_source
except:
	pass

from .camera_tel_type import get_camera_type_from_name, getCameraNameFromType, getTelescopeTypeStrFromCameraType

TELINFO_REFSHAPE = 0
TELINFO_NBSLICE = 1
TELINFO_PEDESTAL = 2
TELINFO_GAIN = 3
TELINFO_TELTYPE = 4
TELINFO_FOCLEN = 5
TELINFO_TABPIXELX = 6
TELINFO_TABPIXELY = 7
TELINFO_NBMIRROR = 8
TELINFO_TELPOSX = 9
TELINFO_TELPOSY = 10
TELINFO_TELPOSZ = 11
TELINFO_NBMIRRORTILES = 12
TELINFO_MIRRORAREA = 13
TELINFO_NBGAIN = 14
TELINFO_NBPIXEL = 15
TELINFO_NBEVENT = 16
TEL_INFOR_CAMERA_ROTATION = 17
TEL_INFOR_PIX_ROTATION = 18


def getTelescopeInfoFromEvent(inputFileName, max_nb_tel):
	'''
	Get the telescope information from the event
	Parameters:
	-----------
		inputFileName : name of the input file to be used
		max_nb_tel : maximum number of telescope in the simulation
	Return:
	-------
		tuple of (dictionnnary which contains the telescope informations (ref_shape, nb_slice, ped, gain) with telescope id as key, and the number of events in the file
	'''
	telescope_info = dict() # Key is tel id, value (ref_shape, slice, ped, gain, telType, focalLen, tabPixelX, tabPixelY, nbMirror)
	nbEvent = 0
	with event_source(inputFileName) as source:
		dicoTelInfo = None
		posTelX = None
		posTelY = None
		posTelZ = None
		for evt in source:
			nbEvent += 1
			if dicoTelInfo is None:
				dicoTelInfo = source.subarray.tel
				posTelX = np.asarray(source.subarray.tel_coords.x, dtype=np.float32)
				posTelY = np.asarray(source.subarray.tel_coords.y, dtype=np.float32)
				posTelZ = np.asarray(source.subarray.tel_coords.z, dtype=np.float32)
			for tel_id in evt.r0.tels_with_data:
				if not tel_id in telescope_info:
					ref_shape = source.subarray.tel[tel_id].camera.readout.reference_pulse_shape
					nb_slice = evt.r0.tel[tel_id].waveform.shape[2]
					nbGain = evt.r0.tel[tel_id].waveform.shape[0]
					nbPixel = evt.r0.tel[tel_id].waveform.shape[1]
					ped = evt.mc.tel[tel_id].pedestal
					gain = evt.mc.tel[tel_id].dc_to_pe
					cameraRotation = source.subarray.tel[tel_id].camera.geometry.pix_rotation.value
					pixRotation = source.subarray.tel[tel_id].camera.geometry.cam_rotation.value
					
					telInfo = dicoTelInfo[tel_id]
					telType = np.uint64(get_camera_type_from_name(telInfo.camera.cam_id))
					focalLen = np.float32(telInfo.optics.equivalent_focal_length.value)
					
					tabPixelX = np.asarray(telInfo.camera.pix_x, dtype=np.float32)
					tabPixelY = np.asarray(telInfo.camera.pix_y, dtype=np.float32)
					
					nbMirror = np.uint64(telInfo.optics.num_mirrors)
					nbMirrorTiles = np.uint64(telInfo.optics.num_mirror_tiles)
					mirrorArea = np.uint64(telInfo.optics.mirror_area.value)
					
					telX = posTelX[int(tel_id - 1)]
					telY = posTelY[int(tel_id - 1)]
					telZ = posTelZ[int(tel_id - 1)]
					
					telescope_info[tel_id] = [ref_shape, nb_slice, ped, gain, telType, focalLen, tabPixelX, tabPixelY, nbMirror,
									telX, telY, telZ, nbMirrorTiles, mirrorArea, nbGain, nbPixel, 0, cameraRotation, pixRotation]
				else:
					telescope_info[tel_id][TELINFO_NBEVENT] += 1
	return telescope_info, nbEvent



def checkIsSimulationFile(telInfo_from_evt):
	'''
	Function which check if the file is a simulation one or not
	For now there is no origin in the ctapipe_io_lst plugin so I use this function to get the origin of the file
	Parameters:
	-----------
		telInfo_from_evt : information of the different telescopes
	Return:
	-------
		True if the data seems to provide of a simulation, False if not
	'''
	for key, value in telInfo_from_evt.items():
		if value[TELINFO_REFSHAPE] is None:
			return False
		else:
			return True
