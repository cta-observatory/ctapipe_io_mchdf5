"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

import tables
try:
	from .get_telescope_info import *
except:
	pass


class TriggerInfo(tables.IsDescription):
	"""
	Describe the trigger informations of the telescopes events
	Attributes:
	-----------
		event_id : id of the corresponding event
		time_s : time of the event in second since 1st january 1970
		time_qns : time in nanosecond (or picosecond) to complete the time in second
		obs_id : id of the observation
	"""
	event_id = tables.UInt64Col()
	time_s = tables.UInt32Col()
	time_qns = tables.UInt32Col()
	obs_id = tables.UInt64Col()


class TelescopePointing(tables.IsDescription):
	"""
	Create the telescope point table
	"""
	telescopetrigger_time = tables.Float64Col()
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
	"""
	Create the waveform tables into the given telescope node
	Parameters:
		hfile : HDF5 file to be used
		tel_node : telescope to be completed
		nb_gain : number of gains of the camera
		image_shape : shape of the camera images (number of slices, number of pixels)
		telId : id of the telescope
		chunkshape : shape of the chunk to be used to store the data
	"""
	if nb_gain > 1:
		columns_dict_waveform = {'event_id': tables.UInt64Col(),
								 "waveformHi": tables.UInt16Col(shape=image_shape),
								 "waveformLo": tables.UInt16Col(shape=image_shape)}
	else:
		columns_dict_waveform = {'event_id': tables.UInt64Col(),
								 "waveformHi": tables.UInt16Col(shape=image_shape)}

	description_waveform = type('description columns_dict_waveform', (tables.IsDescription,), columns_dict_waveform)
	hfile.create_table(tel_node, 'tel_{0:0=3d}'.format(telId), description_waveform,
					   "Table of waveform of the high gain signal", chunkshape=chunkshape)


def create_table_pedestal(hfile, cam_tel_group, nbGain, nbPixel, telId):
	"""
	Create the pedestal description of the telescope
	Parameters:
		hfile : HDF5 file to be used
		cam_tel_group : camera node to be used
		nbGain : number of gain of the camera
		nbPixel : number of pixel of the camera
		telId : id of the telescope
	Return:
		table of the pedestal of the telescope
	"""
	ped_shape = (nbGain, nbPixel)
	columns_dict_pedestal = {
		"first_event_id":  tables.UInt64Col(),
		"last_event_id":  tables.UInt64Col(),
		"pedestal": tables.Float32Col(shape=ped_shape)
	}
	description_pedestal = type('description columns_dict_pedestal', (tables.IsDescription,), columns_dict_pedestal)
	table_pedestal = hfile.create_table(cam_tel_group, 'tel_{0:0=3d}'.format(telId), description_pedestal,
										"Table of the pedestal for high and low gain", expectedrows=1, chunkshape=1)
	return table_pedestal


def create_mon_tel_pedestal(hfile, telInfo, nb_gain, nb_pixel, telId):
	"""
	Create the r0/monitoring/telescope/pedestal table information for a single telescope
	Parameters:
		hfile: HDF5 file to be used
		telInfo : table of some information related to the telescope
		nb_gain : number of gain of the camera
		nb_pixel : number of pixel of the camera
		telId : id of the telescope
	"""
	info_tab_ped = telInfo[TELINFO_PEDESTAL]
	tabPed = np.asarray(info_tab_ped, dtype=np.float32)

	table_pedestal = create_table_pedestal(hfile, hfile.root.r0.monitoring.telescope.pedestal, nb_gain, nb_pixel, telId)

	if info_tab_ped is not None:
		tab_ped_for_entry = table_pedestal.row
		tab_ped_for_entry["first_event_id"] = np.uint64(0)
		tab_ped_for_entry["last_event_id"] = np.uint64(1)
		tab_ped_for_entry["pedestal"] = tabPed
		tab_ped_for_entry.append()
		table_pedestal.flush()


def create_mon_tel_gain(hfile, telInfo, telId):
	"""
	Create the r0/monitoring/telescope/gain table information for a single telescope
	Parameters:
		hfile: HDF5 file to be used
		telInfo : table of some information related to the telescope
		telId : id of the telescope
	"""
	info_tab_gain = telInfo[TELINFO_GAIN]

	if info_tab_gain is not None:
		tab_gain = np.asarray(info_tab_gain, dtype=np.float32)
		hfile.create_array(hfile.root.r0.monitoring.telescope.gain, 'tel_{0:0=3d}'.format(telId), tab_gain,
						   "Table of the gain of the telescope (channel, pixel)")


def create_mon_tel_info(hfile, telId, telInfo, nb_gain, nb_pixel, nb_slice):
	"""
	Create the r0/monitoring/telescope/information table with information (nb_slice, nb_gain, nb_pixel etc...)
	for a single telescope

	Parameters:
		hfile: HDF5 file to be used
		telId : id of the telescope
		telInfo : table of some information related to the telescope
		nb_gain : number of gain of the camera
		nb_pixel : number of pixel of the camera
		nb_slice: number of slices of the camera
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


def create_mon_tel_pointing(hfile, telId, nb_pixel, tel_info, chunkshape=1):
	"""
	Create the base of the telescope structure without waveform
	Parameters:
	-----------
		hfile : HDF5 file to be used
		telId : id of the telescope
		nb_pixel : number of pixel of the camera
		tel_info : table of some informations related to the telescope
		chunkshape : shape of the chunk to be used to store the data
	Return:
	-------
		Created camera group
	"""
	cam_tel_table = hfile.create_table(hfile.root.r0.monitoring.telescope.pointing, 'tel_{0:0=3d}'.format(telId),
									   TelescopePointing, 'Pointing of telescopes ' + str(telId))

	cam_tel_table_row = cam_tel_table.row
	cam_tel_table_row['telescopetrigger_time'] = np.float32(tel_info[TELINFO_TIME_FIRST_EV])
	cam_tel_table_row['azimuth'] = np.float32(tel_info[TELINFO_ARRAY_AZ])
	cam_tel_table_row['altitude'] = np.float32(tel_info[TELINFO_ARRAY_ALT])

	cam_tel_table_row.append()

	columns_dict_photo_electron_image = {'event_id': tables.UInt64Col(),
										 "photo_electron_image": tables.Float32Col(shape=nb_pixel)}
	description_photo_electron_image = type('description columns_dict_photo_electron_image', (tables.IsDescription,),
											columns_dict_photo_electron_image)
	hfile.create_table(hfile.root.r0.event.telescope.photo_electron_image, 'tel_{0:0=3d}'.format(telId),
					   description_photo_electron_image, "Table of real signal in the camera (for simulation only)",
					   chunkshape=chunkshape)

	return cam_tel_table


def create_tel_group_and_table(hfile, telId, telInfo, chunkshape=1):
	"""
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
	"""
	nb_gain = np.uint64(telInfo[TELINFO_NBGAIN])
	nb_pixel = np.uint64(telInfo[TELINFO_NBPIXEL])
	nb_slice = np.uint64(telInfo[TELINFO_NBSLICE])
	image_shape = (nb_slice, nb_pixel)

	create_mon_tel_pointing(hfile, telId, nb_pixel, telInfo, chunkshape=chunkshape)

	create_mon_tel_pedestal(hfile, telInfo, nb_gain, nb_pixel, telId)
	create_mon_tel_gain(hfile, telInfo, telId)
	create_mon_tel_info(hfile, telId, telInfo, nb_gain, nb_pixel, nb_slice)

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
	mon_subarray_pointing_table = hfile.create_table(mon_subarray_pointing_group, 'pointing',
													 MonitoringSubarrayPointing, 'Monitoring Subarray Pointing')

	tel_info = next(iter(telInfo_from_evt.values()))

	# TODO & complain
	# TODO are all the events ? or just the first tel that triggered.
	# TODO same for time. each event time or first event time
	mon_subarray_pointing_table_row = mon_subarray_pointing_table.row
	mon_subarray_pointing_table_row['time'] = np.float64(tel_info[TELINFO_TIME_FIRST_EV])
	mon_subarray_pointing_table_row['tels_with_trigger'] = np.uint64(0)  # TODO


	mon_subarray_pointing_table_row['array_azimuth'] = tel_info[TELINFO_ARRAY_AZ]
	mon_subarray_pointing_table_row['array_altitude'] = tel_info[TELINFO_ARRAY_ALT]
	mon_subarray_pointing_table_row['array_ra'] = tel_info[TELINFO_ARRAY_RA]
	mon_subarray_pointing_table_row['array_dec'] = tel_info[TELINFO_ARRAY_DEC]

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
	"""
	Create the r0 dataset
	Parameters:
		hfile : HDF5 file to be used
		telInfo_from_evt : information of telescopes
	"""
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


def append_photo_electron_image_in_telescope(tel_pe_table, pe_image, eventId):
	"""
	Append the photo electron image into a telescope node
	Parameters :
		tel_pe_table:
		pe_image:
		eventId : id of the corresponding event
	"""
	tel_pe_table_row = tel_pe_table.row
	tel_pe_table_row['event_id'] = eventId
	tel_pe_table_row['photo_electron_image'] = pe_image

	tel_pe_table_row.append()


def append_waveform_in_telescope(tel_wf_table, waveform, eventId):
	"""
	Append a waveform signal (to be transposed) into a telescope node
	-------------------
	Parameters :
		tel_wf_table : telescope waveform table to be used
		waveform : waveform signal to be used
		eventId : id of the corresponding event
	"""
	tel_wf_table_row = tel_wf_table.row
	tel_wf_table_row['event_id'] = eventId

	tel_wf_table_row['waveformHi'] = waveform[0].swapaxes(0, 1)

	if waveform.shape[0] > 1:
		tel_wf_table_row['waveformLo'] = waveform[1].swapaxes(0, 1)

	tel_wf_table_row.append()


def append_event_telescope_data(hfile, event):
	"""
	Append data from event in telescopes
	--------------
	Parameters :
		hfile : HDF5 file to be used
		event : current event
	"""
	tab_tel_with_data = list(event.r0.tels_with_data)
	event_subarray_tel_w_trigger_row = hfile.root.r0.event.subarray.tels_with_trigger
	event_subarray_tel_w_trigger_row.append(tab_tel_with_data)

	event_subarray_trigger_row = hfile.root.r0.event.subarray.trigger.row
	event_subarray_trigger_row['event_id'] = event.index.event_id
	event_subarray_trigger_row['time'] = np.float64(event.trigger.time.to_value('unix'))
	event_subarray_trigger_row['event_type'] = event.trigger.event_type.value
	event_subarray_trigger_row['obs_id'] = event.index.obs_id

	event_subarray_trigger_row.append()

	dicoTel = event.r0.tel
	for telId in tab_tel_with_data:
		waveform = dicoTel[telId].waveform
		tel_waveform_table = hfile.get_node("/r0/event/telescope/waveform", 'tel_{0:0=3d}'.format(telId))
		tel_pe_image_table = hfile.get_node('/r0/event/telescope/photo_electron_image', 'tel_{0:0=3d}'.format(telId))
		photo_electron_image = event.simulation.tel[telId].true_image

		append_waveform_in_telescope(tel_waveform_table, waveform, event.index.event_id)
		append_photo_electron_image_in_telescope(tel_pe_image_table, photo_electron_image, event.index.event_id)


def flush_r0_tables(hfile):
	"""
	Flush all the R0 tables
	Parameters:
		hfile : file to be used
	"""
	for telNode in hfile.walk_nodes("/r0", "Group"):
		try:
			nbGain = np.uint64(telNode.nbGain.read())
			telNode.photo_electron_image.flush()
			telNode.waveformHi.flush()
			if nbGain > 1:
				telNode.waveformLo.flush()
		except Exception as e:
			pass
