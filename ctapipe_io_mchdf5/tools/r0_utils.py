'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import numbers
import tables
import numpy as np
try:
	from .get_telescope_info import *
except:
	pass


class TriggerInfo(tables.IsDescription):
	'''
	Describe the trigger informations of the telescopes events
	Attributes:
	-----------
		event_id : id of the corresponding event
		time_s : time of the event in second since 1st january 1970
		time_qns : time in nanosecond (or picosecond) to complete the time in second
		obs_id : id of the observation
	'''
	event_id = tables.UInt64Col()
	time_s = tables.UInt32Col()
	time_qns = tables.UInt32Col()
	obs_id = tables.UInt64Col()


class TelescopePointing(tables.IsDescription):
	"""
	Create the telescope point table
	"""
	telescopetrigger_time = tables.Float32Col()
	azimuth = tables.Float32Col()
	altitude = tables.Float32Col()


class MonitoringSubarrayPointing(tables.IsDescription):
	"""
	Create the r0 Subarray pointing inside the monitoring directory
	"""
	time = tables.Float64Col()
	tels_with_trigger = tables.UInt64Col()
	array_azimuth = tables.Float32Col()
	array_altitude = tables.Float32Col()
	array_ra = tables.Float32Col()
	array_dec = tables.Float32Col()


class EventSubarrayTrigger(tables.IsDescription):
	"""
	Create the r0 event subarray trigger table
	"""
	obs_id = tables.UInt64Col()
	event_id = tables.UInt64Col()
	time = tables.Float64Col()
	event_type = tables.UInt64Col()

	# tels_with_trigger is a vlarray that will be created


class TelescopeInformation(tables.IsDescription):
	"""
	Create the description of the telescope information table
	"""
	tel_type = tables.UInt64Col()
	tel_id = tables.UInt64Col()
	tel_index = tables.UInt64Col()
	nb_pixel = tables.UInt64Col()
	nb_gain = tables.UInt64Col()
	nb_slice = tables.UInt64Col()


def create_event_tel_waveform(hfile, tel_node, nb_gain, image_shape, telId, chunkshape=1):
	'''
	Create the waveform tables into the given telescope node
	Parameters:
		hfile : HDF5 file to be used
		tel_node : telescope to be completed
		nb_gain : number of gains of the camera
		image_shape : shape of the camera images (number of slices, number of pixels)
		telId :
		chunkshape : shape of the chunk to be used to store the data
	'''
	if nb_gain > 1:
		columns_dict_waveform = {"waveformHi": tables.UInt16Col(shape=image_shape),
								 "waveformLo": tables.UInt16Col(shape=image_shape)}
	else:
		columns_dict_waveform = {"waveformHi": tables.UInt16Col(shape=image_shape)}

	description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
	hfile.create_table(tel_node, 'tel_{0:0=3d}'.format(telId), description_waveform,
					   "Table of waveform of the high gain signal", chunkshape=chunkshape)


def create_table_pedestal(hfile, cam_tel_group, nbGain, nbPixel):
	'''
	Create the pedestal description of the telescope
	Parameters:
		hfile : HDF5 file to be used
		cam_tel_group : camera node to be used
		nbGain : number of gain of the camera
		nbPixel : number of pixel of the camera
	Return:
		table of the pedestal of the telescope
	'''
	ped_shape = (nbGain, nbPixel)
	columns_dict_pedestal = {
		"first_event_id" :  tables.UInt64Col(),
		"last_event_id" :  tables.UInt64Col(),
		"pedestal" :  tables.Float32Col(shape=ped_shape)
	}
	description_pedestal = type('description columns_dict_pedestal', (tables.IsDescription,), columns_dict_pedestal)
	tablePedestal = hfile.create_table(cam_tel_group, 'pedestal', description_pedestal,
									   "Table of the pedestal for high and low gain", expectedrows=1, chunkshape=1)
	return tablePedestal


def create_mon_tel_pedestal(hfile, telInfo, nb_gain, nb_pixel):
	"""
	Create the r0/monitoring/telescope/pedestal table information for a single telescope
	Parameters:
		hfile: HDF5 file to be used
		telInfo:
		nb_gain:
		nb_pixel:
	"""
	info_tab_ped = telInfo[TELINFO_PEDESTAL]
	tabPed = np.asarray(info_tab_ped, dtype=np.float32)

	tablePedestal = create_table_pedestal(hfile, hfile.root.r0.monitoring.telescope.pedestal, nb_gain, nb_pixel)

	if info_tab_ped is not None:
		tabPedForEntry = tablePedestal.row
		tabPedForEntry["first_event_id"] = np.uint64(0)
		tabPedForEntry["last_event_id"] = np.uint64(1)
		tabPedForEntry["pedestal"] = tabPed
		tabPedForEntry.append()
		tablePedestal.flush()


def create_mon_tel_gain(hfile, telInfo):
	"""
	Create the r0/monitoring/telescope/gain table information for a single telescope
	Parameters:
		hfile: HDF5 file to be used
		telInfo:
	"""
	info_tab_gain = telInfo[TELINFO_GAIN]

	if info_tab_gain is not None:
		tab_gain = np.asarray(info_tab_gain, dtype=np.float32)
		hfile.create_array(hfile.root.r0.monitoring.telescope.gain, 'tabGain', tab_gain,
						   "Table of the gain of the telescope (channel, pixel)")


def create_mon_tel_info(hfile, telId, telInfo, nb_gain, nb_pixel, nb_slice):
	"""
	Create the r0/monitoring/telescope/information table with information (nb_slice, nb_gain, nb_pixel etc...)
	for a single telescope

	Parameters:
		hfile: HDF5 file to be used
		telId:
		telInfo:
		nb_gain:
		nb_pixel:
		nb_slice:
	"""
	tel_index = telId - 1
	tel_type = np.uint64(telInfo[TELINFO_TELTYPE])

	information_group = hfile.root.r0.monitoring.telescope.information

	tel_info_table = hfile.create_table(information_group, 'tel_{0:0=3d}'.format(telId), TelescopeInformation,
										"Telescope information")
	tel_info_table_row = tel_info_table.row
	tel_info_table_row['tel_type'] = tel_type
	tel_info_table_row['tel_id'] = telId
	tel_info_table_row['tel_index'] = tel_index
	tel_info_table_row['nb_pixel'] = nb_pixel
	tel_info_table_row['nb_gain'] = nb_gain
	tel_info_table_row['nb_slice'] = nb_slice

	tel_info_table_row.append()


def create_mon_tel_pointing(hfile, telId, nb_pixel, chunkshape=1):
	'''
	Create the base of the telescope structure without waveform
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telId : id of the telescope
		nb_pixel :
		chunkshape : shape of the chunk to be used to store the data
	Return:
	-------
		Created camera group
	'''
	cam_tel_table = hfile.create_table(hfile.root.r0.monitoring.telescope.pointing, 'tel_{0:0=3d}'.format(telId),
									   TelescopePointing, 'Pointing of telescopes ' + str(telId))

	cam_tel_table_row = cam_tel_table.row
	cam_tel_table_row['telescopetrigger_time'] = np.float32(0)  # TODO find where this info comes from
	cam_tel_table_row['azimuth'] = np.float32(0)  # TODO find where this info comes from
	cam_tel_table_row['altitude'] = np.float32(0)  # TODO find where this info comes from

	columns_dict_photo_electron_image = {"photo_electron_image": tables.Float32Col(shape=nb_pixel)}
	description_photo_electron_image = type('description columns_dict_photo_electron_image', (tables.IsDescription,),
											columns_dict_photo_electron_image)
	hfile.create_table(hfile.root.r0.event.telescope.photo_electron_image, 'tel_{0:0=3d}'.format(telId),
					   description_photo_electron_image, "Table of real signal in the camera (for simulation only)",
					   chunkshape=chunkshape)

	return cam_tel_table


def create_tel_group_and_table(hfile, telId, telInfo, chunkshape=1):
	'''
	Create the telescope group and table inside r0:
	/r0/event/telescope/waveform
	/r0/monitoring/telescope/pointing

	It is important not to add an other dataset with the type of the camera to simplify the search of a telescope by
	telescope index in the file structure
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telId : id of the telescope
		telInfo : table of some informations related to the telescope
		chunkshape : shape of the chunk to be used to store the data
	'''
	nb_gain = np.uint64(telInfo[TELINFO_NBGAIN])
	nb_pixel = np.uint64(telInfo[TELINFO_NBPIXEL])
	nb_slice = np.uint64(telInfo[TELINFO_NBSLICE])
	image_shape = (nb_slice, nb_pixel)

	create_mon_tel_pointing(hfile, telId, nb_pixel, chunkshape=chunkshape)

	create_mon_tel_pedestal(hfile, telInfo, nb_pixel, nb_gain)
	create_mon_tel_gain(hfile, telInfo)
	create_mon_tel_info(hfile, telId, telInfo, nb_pixel, nb_gain, nb_slice)

	create_event_tel_waveform(hfile, hfile.root.r0.event.telescope.waveform, nb_gain, image_shape, telId,
							  chunkshape=chunkshape)


def fill_monitoring_subarray(hfile, mon_subarray_pointing_group, telInfo_from_evt):
	"""
	Fill the r0 monitoring subarray with pointing table
	Parameters:
		hfile: HDF5 file to be used
		mon_subarray_pointing_group:
		telInfo_from_evt:
	"""
	mon_subarray_pointing_table = hfile.create_table(mon_subarray_pointing_group, 'pointing', MonitoringSubarrayPointing,
													 'Monitoring Subarray Pointing')

	# TODO to be fill up with telInfo_from_evt
	mon_subarray_pointing_table_row = mon_subarray_pointing_table.row
	mon_subarray_pointing_table_row['time'] = np.float64(0)
	mon_subarray_pointing_table_row['tels_with_trigger'] = np.uint64(0)
	mon_subarray_pointing_table_row['array_azimuth'] = np.float32(0)
	mon_subarray_pointing_table_row['array_altitude'] = np.float32(0)
	mon_subarray_pointing_table_row['array_ra'] = np.float32(0)
	mon_subarray_pointing_table_row['array_dec'] = np.float32(0)

	mon_subarray_pointing_table_row.append()


def create_event_subarray_trigger(hfile, event_subarray_group):
	"""
	Create the event subarray trigger table
	Parameters:
		hfile: HDF5 file to be used
		event_subarray_group:
	"""
	hfile.create_table(event_subarray_group, 'trigger', EventSubarrayTrigger, 'Trigger information')
	hfile.create_vlarray(event_subarray_group, "tels_with_trigger", tables.UInt16Atom(shape=()),
						 'Telescope that have triggered - tels_with_data')


def create_r0_dataset(hfile, telInfo_from_evt):
	'''
	Create the r0 dataset
	Parameters:
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	'''
	# Group : r0
	hfile.create_group("/", 'r0', 'Raw data waveform information of the run')

	hfile.create_group('/r0', 'monitoring', 'Telescope monitoring')
	mon_subarray = hfile.create_group('/r0/monitoring', 'subarray', 'Subarrays')
	fill_monitoring_subarray(hfile, mon_subarray, telInfo_from_evt)

	hfile.create_group('/r0/monitoring', 'telescope', 'Telescopes')
	hfile.create_group('/r0/monitoring/telescope', 'pointing', 'Pointing of each telescope')
	hfile.create_group('/r0/monitoring/telescope', 'pedestal', 'Pedestal of telescope camera')
	hfile.create_group('/r0/monitoring/telescope', 'gain', 'Gain of telescope camera')
	hfile.create_group('/r0/monitoring/telescope', 'information', 'Telescope monitoring information')

	hfile.create_group('/r0', 'event', 'R0 events')
	hfile.create_group('/r0/event', 'telescope', 'R0 telescope events')
	hfile.create_group('/r0/event/telescope', 'waveform', 'R0 waveform events')
	hfile.create_group('/r0/event/telescope', 'photo_electron_image', 'ph.e image without noise')

	event_subarray = hfile.create_group('/r0/event', 'subarray', 'R0 subarray events')
	create_event_subarray_trigger(hfile, event_subarray)

	hfile.create_group('/r0', 'service', 'Service')

	# The group in the r0 group will be completed on the fly with the information collected in telInfo_from_evt
	for telId, telInfo in telInfo_from_evt.items():
		create_tel_group_and_table(hfile, telId, telInfo)


def appendWaveformInTelescope(telNode, waveform, photo_electron_image, eventId, timeStamp):
	'''
	Append a waveform signal (to be transposed) into a telescope node
	-------------------
	Parameters :
		telNode : telescope node to be used
		waveform : waveform signal to be used
		photo_electron_image : image of the pixel with signal (without noise)
		eventId : id of the corresponding event
		timeStamp : time of the event in UTC
	'''
	tabtrigger = telNode.trigger.row
	tabtrigger['event_id'] = eventId


	#TODO : use the proper convertion from timeStamp to the time in second and nanosecond
	if isinstance(timeStamp, numbers.Number):
		timeSecond = int(timeStamp)
		timeMicroSec = timeStamp - timeSecond
		tabtrigger['time_s'] = timeSecond
		tabtrigger['time_qns'] = timeMicroSec
	tabtrigger.append()

	tabWaveformHi = telNode.waveformHi.row
	tabWaveformHi['waveformHi'] = waveform[0].swapaxes(0, 1)
	tabWaveformHi.append()

	if waveform.shape[0] > 1:
		tabWaveformLo = telNode.waveformLo.row
		tabWaveformLo['waveformLo'] = waveform[1].swapaxes(0, 1)
		tabWaveformLo.append()

	if photo_electron_image is not None and isinstance(photo_electron_image, list):
		tabPhotoElectronImage = telNode.photo_electron_image.row
		tabPhotoElectronImage["photo_electron_image"] = photo_electron_image
		tabPhotoElectronImage.append()



def appendEventTelescopeData(hfile, event):
	'''
	Append data from event in telescopes
	--------------
	Parameters :
		hfile : HDF5 file to be used
		event : current event
	'''
	tabTelWithData = event.r0.tels_with_data
	dicoTel = event.r0.tel
	for telId in tabTelWithData:
		waveform = dicoTel[telId].waveform
		telNode = hfile.get_node("/r1", 'Tel_' + str(telId))
		photo_electron_image = event.mc.tel[telId].photo_electron_image
		appendWaveformInTelescope(telNode, waveform, photo_electron_image, event.r0.event_id, event.trig.gps_time.value)


def flushR1Tables(hfile):
	'''
	Flush all the R1 tables
	Parameters:
		hfile : file to be used
	'''
	for telNode in hfile.walk_nodes("/r1", "Group"):
		try:
			nbGain = np.uint64(telNode.nbGain.read())
			telNode.photo_electron_image.flush()
			telNode.waveformHi.flush()
			if nbGain > 1:
				telNode.waveformLo.flush()
		except Exception as e:
			pass

