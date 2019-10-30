'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

from ctapipe.io.eventsource import EventSource
from ctapipe.io.containers import DataContainer
from numpy import stack, zeros, swapaxes, array, int16, uint64
from ctapipe.instrument import TelescopeDescription, SubarrayDescription, OpticsDescription
from ctapipe.instrument.camera import CameraGeometry
from astropy import units as u
from astropy.coordinates import Angle
import numpy as np
import tables

__all__ = ['MCHDF5EventSource']
HI_GAIN = 0
LO_GAIN = 1
	
def _convert_per_events_to_per_telescope(hfile):
	'''
	Concert the telescope storage into a event storage
	Parameters:
	-----------
		hfile : HDF5 file to be used
	Return:
	-------
		dictionary which contains the events with the proper telescopes
	'''
	events=dict()
	for telNode in hfile.walk_nodes('/r1', 'Group'):
		try:
			tabEventId = telNode.trigger.col("event_id")
			telescopeIndex = uint64(telNode.telIndex.read())
			telescopeId = uint64(telNode.telId.read())
			for i,eventId in enumerate(tabEventId):
				try:
					events[eventId].append((telescopeId, telescopeIndex, i))
				except KeyError:
					events[eventId] = [(telescopeId, telescopeIndex, i)]
		except tables.exceptions.NoSuchNodeError as e:
			#For the r1 dataset only
			pass
	return events


class MCHDF5EventSource(EventSource):
	"""
	EventSource for the MCHDF5 file format version 2.
	MCHDF5 is a data format for Cherenkov Telescope Array (CTA)
	that provides a memory access patterns
	adapted for high performance computing algorithms.
	It allows algorithms to take advantage of the latest SIMD
	(Single input multiple data) operations included in modern processors,
	for native vectorized optimization of analytical data processing.
	"""

	def __init__(self, config=None, parent=None, **kwargs):
		super().__init__(config=config, parent=parent, **kwargs)

		self.metadata['is_simulation'] = True

		# Create MCRun isntance and load file into memory
		self.run = tables.open_file(self.input_url, "r")
	
	
	@staticmethod
	def is_compatible(file_path):
		try:
			hfile = tables.open_file(file_path, "r")
			isCompatible = hfile.title == "R1-V2"
			hfile.close()
			return isCompatible
		except Exception:
			return False

	def __exit__(self, exc_type, exc_val, exc_tb):
		pass


	def _generator(self):
		# HiPeData arranges data per telescope and not by event like simtel
		# We need to first create a dictionary.
		#   key -> EventId, value -> List of event from triggered telescopes
		self.events = _convert_per_events_to_per_telescope(self.run)

		# the container is initialized once, and data is replaced within
		# it after each yield
		counter = 0
		data = DataContainer()
		data.meta['origin'] = "mchdf5v2"

		# some hessio_event_source specific parameters
		data.meta['input_url'] = self.input_url
		data.meta['max_events'] = self.max_events

		'''
		MC data are valid for the whole run
		'''
		data.mc.tel.clear()  # clear the previous telescopes
		for telNode in self.run.walk_nodes('/r1', 'Group'):
			try:
				tel_id = uint64(telNode.telId.read())
				data.mc.tel[tel_id].dc_to_pe = telNode.tabGain.read()
				
				pedestal = telNode.pedestal.read()
				pedestal = pedestal["pedestal"]
				
				data.mc.tel[tel_id].pedestal = pedestal[0]
				data.mc.tel[tel_id].reference_pulse_shape = telNode.tabRefShape.read()
			except tables.exceptions.NoSuchNodeError as e:
				pass
		
		tabEvent = self.run.root.simulation.mc_event.read()
		tabEventId = tabEvent["event_id"]
		
		azimuth = self.run.root.simulation.run_config.col("run_array_direction")[0]
		
		for event_id, event_list in self.events.items():
			if counter == 0:
				# subarray info is only available when an event is loaded,
				# so load it on the first event.
				data.inst.subarray = self._build_subarray_info(self.run)

			obs_id = 0
			tels_with_data = set([info[0] for info in event_list])
			data.count = counter
			data.r0.obs_id = obs_id
			data.r0.event_id = event_id
			data.r0.tels_with_data = tels_with_data
			data.r1.obs_id = obs_id
			data.r1.event_id = event_id
			data.r1.tels_with_data = tels_with_data
			data.dl0.obs_id = obs_id
			data.dl0.event_id = event_id
			data.dl0.tels_with_data = tels_with_data

			# handle telescope filtering by taking the intersection of
			# tels_with_data and allowed_tels
			if len(self.allowed_tels) > 0:
				selected = tels_with_data & self.allowed_tels
				if len(selected) == 0:
					continue  # skip event
				data.r0.tels_with_data = selected
				data.r1.tels_with_data = selected
				data.dl0.tels_with_data = selected

			#data.trig.tels_with_trigger = set(tels_with_data)
			data.trig.tels_with_trigger = array(list(tels_with_data), dtype=int16)
			
			#TODO : replace this by an astropy join
			indexSimu = np.where(tabEventId == event_id)
			'''
			time_s, time_ns = file.get_central_event_gps_time()
			data.trig.gps_time = Time(time_s * u.s, time_ns * u.ns, format='unix', scale='utc')
			'''
			data.mc.energy = tabEvent["mc_energy"][indexSimu] * u.TeV
			data.mc.alt = Angle(tabEvent["mc_alt"][indexSimu], u.rad)
			data.mc.az = Angle(tabEvent["mc_az"][indexSimu], u.rad)
			data.mc.core_x = tabEvent["mc_core_x"][indexSimu] * u.m
			data.mc.core_y = tabEvent["mc_core_y"][indexSimu] * u.m
			data.mc.h_first_int = tabEvent["mc_h_first_int"][indexSimu] * u.m
			data.mc.x_max = tabEvent["mc_x_max"][indexSimu] * u.g / (u.cm**2)
			data.mc.shower_primary_id = tabEvent["mc_shower_primary_id"][indexSimu]
			
			data.mcheader.run_array_direction = Angle(azimuth * u.rad)
			
			# this should be done in a nicer way to not re-allocate the
			# data each time (right now it's just deleted and garbage
			# collected)

			data.r0.tel.clear()
			data.r1.tel.clear()
			data.dl0.tel.clear()
			data.dl1.tel.clear()

			for telescopeId, telescopeIndex, event in event_list:
				
				telNode = self.run.get_node("/r1", 'Tel_' + str(telescopeId))
				
				matWaveform = telNode.waveformHi.read(event, event + 1)
				matWaveform = matWaveform["waveformHi"][0]
				matSignalPSHi = matWaveform.swapaxes(0, 1)
				try:
					waveformLo = telNode.waveformLo.read(event, event + 1)
					waveformLo = waveformLo["waveformLo"][0]
					
					matSignalPSLo = waveformLo.swapaxes(0, 1)
					tabHiLo = np.stack((matSignalPSHi, matSignalPSLo))
					data.r0.tel[telescopeId].waveform = tabHiLo
					data.r0.tel[telescopeId].num_samples = data.r0.tel[telescopeId].waveform.shape[-1]

					_, _, n_samples = tabHiLo.shape
					ped = data.mc.tel[telescopeId].pedestal[..., np.newaxis] / n_samples
					gain = data.mc.tel[telescopeId].dc_to_pe[..., np.newaxis]
					data.r1.tel[telescopeId].waveform = (tabHiLo - ped) * gain

				except Exception as e:
					print(e)
					data.r0.tel[telescopeId].waveform = np.expand_dims(matSignalPSHi, axis=0)
				
				#data.r0.tel[telescopeId].image= matSignalPSHi.sum(axis=2)
				#data.r0.tel[telescopeId].num_trig_pix = file.get_num_trig_pixels(telescopeId)
				#data.r0.tel[telescopeId].trig_pix_id = file.get_trig_pixels(telescopeId)
				
			yield data
			counter += 1
		return

	def _build_subarray_info(self, run):
		"""
		constructs a SubarrayDescription object from the info in an
		MCRun

		Parameters
		----------
		run: MCRun object

		Returns
		-------
		SubarrayDescription :
			instrumental information
		"""
		subarray = SubarrayDescription("MonteCarloArray")
		
		tabFocalTel = run.root.instrument.subarray.telescope.optics.col("equivalent_focal_length")
		tabPosTelX = run.root.instrument.subarray.layout.col("pos_x")
		tabPosTelY = run.root.instrument.subarray.layout.col("pos_y")
		tabPosTelZ = run.root.instrument.subarray.layout.col("pos_z")
		
		tabPoslXYZ = np.ascontiguousarray(np.vstack((tabPosTelX, tabPosTelY, tabPosTelZ)).T)
		
		'''
		# Correspance HiPeData.Telscope.Type and camera name
		# 0  LSTCam, 1 NectarCam, 2 FlashCam, 3 SCTCam,
		# 4 ASTRICam, 5 DigiCam, 6 CHEC
		'''
		mapping_camera = {0: 'LSTCam', 1: 'NectarCam', 2: 'FlashCam',
				3: 'SCTCam', 4: 'ASTRICam', 5: 'DigiCam',
				6: 'CHEC'}
		
		mapping_telName = {0:'LST', 1:'MST', 2:'MST', 3:'MST', 4:'SST-ASTRI', 5:'SST-1M', 6:'SST-2M'}
		
		for telNode, camNode in zip(self.run.walk_nodes('/r1', 'Group'), self.run.walk_nodes('/instrument/subarray/telescope/camera', 'Group')):
			try:
				telType = uint64(telNode.telType.read())
				telIndex = uint64(telNode.telIndex.read())
				telId = uint64(telNode.telId.read())
				
				cameraName = mapping_camera[telType]
				telName = mapping_telName[telType]
				camera = CameraGeometry.from_name(cameraName)
				camera.cam_id = cameraName
				
				foclen = tabFocalTel[telIndex] * u.m
				
				tel_pos = tabPoslXYZ[telIndex] * u.m
				
				camera.pix_x = camNode.pix_x.read() * u.m
				camera.pix_y = camNode.pix_y.read() * u.m
				
				optic = OpticsDescription.from_name(telName)
				optic.equivalent_focal_length = foclen
				telescope_description = TelescopeDescription(telName, telType, optics=optic, camera=camera)

				#tel.optics.mirror_area = mirror_area
				#tel.optics.num_mirror_tiles = num_tiles
				subarray.tels[telId] = telescope_description
				subarray.positions[telId] = tel_pos
			except tables.exceptions.NoSuchNodeError as e:
				pass

		return subarray
