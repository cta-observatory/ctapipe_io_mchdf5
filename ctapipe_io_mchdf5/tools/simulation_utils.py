"""
    Auteur : Pierre Aubert
    Mail : aubertp7@gmail.com
    Licence : CeCILL-C
"""

import tables
import numpy as np

from ctapipe.io import event_source


class RunConfigEvent(tables.IsDescription):
    """
    Configuration of the simulated events
    Attributes:
        atmosphere : Atmospheric model number
        core_pos_mode : Core Position Mode (fixed/circular/...)
        corsika_bunchsize : Number of photons per bunch
        corsika_high_E_detail : Detector MC information
        corsika_high_E_model : Detector MC information
        corsika_iact_options : Detector MC information
        corsika_low_E_detail : Detector MC information
        corsika_low_E_model : Detector MC information
        corsika_version : CORSIKA version * 1000
        corsika_wlen_max : Maximum wavelength of cherenkov light [nm]
        corsika_wlen_min : Minimum wavelength of cherenkov light [nm]
        detector_prog_id : simtelarray=1
        detector_prog_start : Time when detector simulation started
        diffuse : True if the events are diffuse, False is they are point like
        energy_range_max : Upper limit of energy range of primary particle [TeV]
        energy_range_min : Lower limit of energy range of primary particle [TeV]
        injection_height : Height of particle injection [m]
        max_alt : Maximum altitude of the simulated showers in radian
        max_az : Maximum azimuth of the simulated showers in radian
        max_scatter_range : Maximum scatter range [m]
        max_viewcone_radius : Maximum viewcone radius [deg]
        min_alt : Minimum altitude of the simulated showers in radian
        min_az : Minimum azimuth of the simulated showers in radian
        min_scatter_range : Maximum scatter range [m]
        min_viewcone_radius : Minimum viewcone radius [deg]
        num_showers : total number of shower
        obs_id : id of the observation
        prod_site_B_declination : magnetic declination [rad]
        prod_site_B_inclination : magnetic inclination [rad]
        prod_site_B_total : total geomagnetic field [uT]
        prod_site_alt : height of observation level [m]
        run_array_direction : direction of the run (in azimuth and altitude in radian)
        shower_prog_id : CORSIKA=1, ALTAI=2, KASCADE=3, MOCCA=4
        shower_prog_start : Time when shower simulation started, CORSIKA: only date
        shower_reuse : Number of used shower per event
        simtel_version : sim_telarray version * 1000
        spectral_index : Power-law spectral index of spectrum
    """
    atmosphere = tables.UInt64Col()
    core_pos_mode = tables.UInt64Col()
    corsika_bunchsize = tables.Float32Col()
    corsika_high_E_detail = tables.Int32Col()
    corsika_high_E_model = tables.Int32Col()
    corsika_iact_options = tables.Int32Col()
    corsika_low_E_detail = tables.Int32Col()
    corsika_low_E_model = tables.Int32Col()
    corsika_version = tables.Int32Col()
    corsika_wlen_max = tables.Float32Col()
    corsika_wlen_min = tables.Float32Col()
    detector_prog_id = tables.UInt64Col()
    detector_prog_start = tables.Int32Col()
    diffuse = tables.Int32Col()
    energy_range_max = tables.Float32Col()
    energy_range_min = tables.Float32Col()
    injection_height = tables.Float32Col()
    max_alt = tables.Float32Col()
    max_az = tables.Float32Col()
    max_scatter_range = tables.Float32Col()
    max_viewcone_radius = tables.Float32Col()
    min_alt = tables.Float32Col()
    min_az = tables.Float32Col()
    min_scatter_range = tables.Float32Col()
    min_viewcone_radius = tables.Float32Col()
    num_showers = tables.UInt64Col()
    obs_id = tables.UInt64Col()
    prod_site_B_declination = tables.Float32Col()
    prod_site_B_inclination = tables.Float32Col()
    prod_site_B_total = tables.Float32Col()
    prod_site_alt = tables.Float32Col()
    run_array_direction = tables.Float32Col(shape=2)
    shower_prog_id = tables.UInt64Col()
    shower_prog_start = tables.Int32Col()
    shower_reuse = tables.UInt64Col()
    simtel_version = tables.Int32Col()
    spectral_index = tables.Float32Col()


class ShowerDistribution(tables.IsDescription):
    """
    Distribution of the simulated events
    Attributes:
        bins_core_dist : distribution of the impact parameters by respect to the dstance by the center of the site
        bins_energy : distribution of the energy of the simulated events
        hist_id : id of the histogram
        num_entries : number of entries of the histogram
        obs_id : observation id
    """
    bins_core_dist = tables.Float32Col(shape=(201,))
    bins_energy = tables.Float32Col(shape=(121,))
    hist_id = tables.UInt64Col()
    histogram = tables.Float32Col(shape=(120, 200))
    num_entries = tables.UInt64Col()
    obs_id = tables.UInt64Col()


class MCEvent(tables.IsDescription):
    """
    Simulated corsika event
    Attributes
    event_id : tables.UInt64Col
    	Shower event id.
    true_alt : tables.Float32Col
    	Shower altitude (zenith) angle. From Monte Carlo simulation parameters.
    true_az : tables.Float32Col
    	Shower azimuth angle. From Monte Carlo simulation parameters.
    true_core_x : tables.Float32Col
    	Shower core position x coordinate. From Monte Carlo simulation
    	parameters.
    true_core_y : tables.Float32Col
    	Shower core position y coordinate. From Monte Carlo simulation
    	parameters.
    true_energy : tables.Float32Col
    	Energy of the shower primary particle. From Monte Carlo simulation
    	parameters.
    true_h_first_int : tables.Float32Col
    	Height of shower primary particle first interaction. From Monte Carlo
    	simulation parameters.
    true_shower_primary_id : tables.UInt8Col
    	Particle type id for the shower primary particle. From Monte Carlo
    	simulation parameters.
    true_x_max : tables.Float32Col
    	Atmospheric depth of shower maximum [g/cm^2], derived from all charged particles
    obs_id : tables.UInt64Col
    	Shower observation (run) id. Replaces old "run_id" in ctapipe r0
    	container.
    """
    event_id = tables.UInt64Col()
    true_alt = tables.Float32Col()
    true_az = tables.Float32Col()
    true_core_x = tables.Float32Col()
    true_core_y = tables.Float32Col()
    true_energy = tables.Float32Col()
    true_h_first_int = tables.Float32Col()
    true_shower_primary_id = tables.UInt64Col()
    true_x_max = tables.Float32Col()
    obs_id = tables.UInt64Col()


def create_simulation_dataset(hfile):
    """
    Create the simulation dataset
    Parameters:
        hfile : HDF5 file to be used
    Return:
        table of the mc_event
    """
    hfile.create_group('/', 'simulation', 'Simulation information of the run')
    service_group = hfile.create_group('/simulation', 'service', 'Service simulation')
    hfile.create_table(service_group, 'shower_distribution', ShowerDistribution, 'Distribution of the simulated events')

    # configuration group already created in `instrument_utils.py`
    config_sim_group = hfile.create_group('/configuration', 'simulation',
                                          'Configuration simulation information of the run')
    hfile.create_table(config_sim_group, 'run', RunConfigEvent, "Configuration of the simulated events", expectedrows=1)

    hfile.create_group('/simulation', 'event', 'Event simulation')
    sim_event_subarray_group = hfile.create_group('/simulation/event', 'subarray', 'Subarray shower')
    table_mc_event = hfile.create_table(sim_event_subarray_group, 'shower', MCEvent, "All simulated Corsika events")
    return table_mc_event


def fill_simulation_header_info(hfile, inputFileName):
    """
    Fill the simulation information in the simulation header (/simulation/run_config)
    Parameters:
        hfile : HDF5 file to be used
        inputFileName : name of the input file to be used
    """
    with event_source(inputFileName) as source:
        evt = next(iter(source))

        tableSimulationConfig = hfile.root.configuration.simulation.run
        tabSimConf = tableSimulationConfig.row

        mcHeader = evt.mcheader
        tabSimConf["atmosphere"] = np.uint64(mcHeader.atmosphere)
        tabSimConf["core_pos_mode"] = np.uint64(mcHeader.core_pos_mode)
        tabSimConf["corsika_bunchsize"] = np.float32(mcHeader.corsika_bunchsize)
        tabSimConf["corsika_high_E_detail"] = np.int32(mcHeader.corsika_high_E_detail)
        tabSimConf["corsika_high_E_model"] = np.int32(mcHeader.corsika_high_E_model)
        tabSimConf["corsika_iact_options"] = np.int32(mcHeader.corsika_iact_options)
        tabSimConf["corsika_low_E_detail"] = np.int32(mcHeader.corsika_low_E_detail)
        tabSimConf["corsika_low_E_model"] = np.int32(mcHeader.corsika_low_E_model)
        tabSimConf["corsika_version"] = np.int32(mcHeader.corsika_version)
        tabSimConf["corsika_wlen_max"] = np.float32(mcHeader.corsika_wlen_max)
        tabSimConf["corsika_wlen_min"] = np.float32(mcHeader.corsika_wlen_min)
        tabSimConf["detector_prog_id"] = np.uint64(mcHeader.detector_prog_id)
        tabSimConf["detector_prog_start"] = np.int32(mcHeader.detector_prog_start)
        tabSimConf["diffuse"] = np.int32(mcHeader.diffuse)
        tabSimConf["energy_range_max"] = np.float32(mcHeader.energy_range_max)
        tabSimConf["energy_range_min"] = np.float32(mcHeader.energy_range_min)
        tabSimConf["injection_height"] = np.float32(mcHeader.injection_height)
        tabSimConf["max_alt"] = np.float32(mcHeader.max_alt)
        tabSimConf["max_az"] = np.float32(mcHeader.max_az)
        tabSimConf["max_scatter_range"] = np.float32(mcHeader.max_scatter_range)
        tabSimConf["max_viewcone_radius"] = np.float32(mcHeader.max_viewcone_radius)
        tabSimConf["min_alt"] = np.float32(mcHeader.min_alt)
        tabSimConf["min_az"] = np.float32(mcHeader.min_az)
        tabSimConf["min_scatter_range"] = np.float32(mcHeader.min_scatter_range)
        tabSimConf["min_viewcone_radius"] = np.float32(mcHeader.min_viewcone_radius)
        tabSimConf["num_showers"] = np.uint64(mcHeader.num_showers)
        tabSimConf["obs_id"] = np.uint64(evt.index.obs_id)
        tabSimConf["prod_site_B_declination"] = np.float32(mcHeader.prod_site_B_declination)
        tabSimConf["prod_site_B_inclination"] = np.float32(mcHeader.prod_site_B_inclination)
        tabSimConf["prod_site_B_total"] = np.float32(mcHeader.prod_site_B_total)
        tabSimConf["prod_site_alt"] = np.float32(mcHeader.prod_site_alt)
        tabSimConf["run_array_direction"] = np.float32(mcHeader.run_array_direction)
        tabSimConf["shower_prog_id"] = np.uint64(mcHeader.shower_prog_id)
        tabSimConf["shower_prog_start"] = np.int32(mcHeader.shower_prog_start)
        tabSimConf["shower_reuse"] = np.uint64(mcHeader.shower_reuse)
        tabSimConf["simtel_version"] = np.int32(mcHeader.simtel_version)
        tabSimConf["spectral_index"] = np.float32(mcHeader.spectral_index)
        tabSimConf.append()


def append_corsika_event(tableMcCorsikaEvent, event):
    """
    Append the Monte Carlo information in the table of Corsika events
    Parameter :
        tableMcCorsikaEvent : table of Corsika events to be completed
        event : Monte Carlo event to be used
    """
    tabMcEvent = tableMcCorsikaEvent.row
    tabMcEvent['event_id'] = np.uint64(event.index.event_id)
    tabMcEvent['true_az'] = np.float32(event.mc.az)
    tabMcEvent['true_alt'] = np.float32(event.mc.alt)

    tabMcEvent['true_core_x'] = np.float32(event.mc.core_x)
    tabMcEvent['true_core_y'] = np.float32(event.mc.core_y)

    tabMcEvent['true_energy'] = np.float32(event.mc.energy)
    tabMcEvent['true_h_first_int'] = np.float32(event.mc.h_first_int)
    tabMcEvent['true_shower_primary_id'] = np.uint8(event.mc.shower_primary_id)

    tabMcEvent['true_x_max'] = np.float32(event.mc.x_max)

    tabMcEvent['obs_id'] = np.uint64(event.index.obs_id)

    # I don't know where to find the following informations but they exist in C version
    # tabMcEvent['depthStart'] = np.float32(0.0)
    # tabMcEvent['hmax'] = np.float32(0.0)
    # tabMcEvent['emax'] = np.float32(0.0)
    # tabMcEvent['cmax'] = np.float32(0.0)

    tabMcEvent.append()
