# coding: utf-8

'''
    Auteur : Pierre Aubert
    Mail : aubertp7@gmail.com
    Licence : CeCILL-C
'''

import tables
import numpy as np
from tables import open_file
from ctapipe.io import event_source
import argparse

# from .get_telescope_info import *
from ctapipe_io_mchdf5.tools.get_telescope_info import *
# from .simulation_utils import *
from ctapipe_io_mchdf5.tools.simulation_utils import *
# from .get_nb_tel import getNbTel
from ctapipe_io_mchdf5.tools.get_nb_tel import getNbTel
# from .instrument_utils import *
from ctapipe_io_mchdf5.tools.instrument_utils import *
# from .r1_utils import *
from ctapipe_io_mchdf5.tools.r1_utils import *
# from .r1_file import *
from ctapipe_io_mchdf5.tools.r1_file import *
from ctapipe.calib import CameraCalibrator
from ctapipe.utils import get_dataset_path
from lstchain.calib.camera.r0 import LSTR0Corrections
from lstchain.calib.camera.calibrator import LSTCameraCalibrator
from traitlets.config.loader import Config
import json
import time
from ctapipe.image.cleaning import tailcuts_clean, dilate


def apply_manual_calibration(event, cam_config):  # tel_id, cam_config):
    path_calib_r1_dl1 = "/Users/garciaenrique/CTA/cta-lstchain-extra/calib/camera/calibration_472_maxeve2100_stat1000.hdf5"
    img_extractor = "LocalPeakWindowSum"  # TODO  Same as in image_extractor ?? IF so, change it so that it can be: OUI
    # TODO, but if oui, why there is not a 'NeighborPeakWindowSum' option under camera_calibration_param.json ??
    # read directly from the file
    cam_config_formating = Config({img_extractor: {**cam_config[img_extractor]}})

    r0_r1_calibrator = LSTR0Corrections(**cam_config['LSTR0Corrections'])
    r1_dl1_calibrator = LSTCameraCalibrator(calibration_path=path_calib_r1_dl1,
                                            image_extractor=img_extractor,
                                            config=cam_config_formating
                                            )
    # calibrate r0 --> r1
    r0_r1_calibrator.calibrate(event)

    # If triggered event
    #if event.r0.tel[0].trigger_type != 32:
    #    r1_dl1_calibrator(event)
    # TODO : If there are more telescopes, there should be a for for all of them. Not really sure
    # if this is should be applied here !
    for tel_id in event.r0.tels_with_data:
        # If triggered event
        #if tel_id != 0:
        #    print(" ! TEL_ID", tel_id)
        if event.r0.tel[tel_id].trigger_type != 32:
            r1_dl1_calibrator(event)

    #print(" Manual calibration correctly passed")


def get_camera_calib_config(
        pathfile="/Users/garciaenrique/CTA/cta-lstchain/lstchain/tools/camera_calib_param_ZFITS_HDF5.json"):
    camera_config_path = pathfile
    with open(camera_config_path) as json_file:
        cam_conf = json.load(json_file)

    return cam_conf


def apply_zero_suppression(event):
    camera = event.inst.subarray.tel[0].camera
    # ASSUMING HIGH GAIN
    image_dl1 = event.dl1.tel[0].image[0]
    waveform_dl0 = event.dl0.tel[0].waveform[0]

    # Get the mask from the integrated waveform - found in dl1 container and previous filled by the LST calibration -
    # and apply the mask to each slide of dl0, where later the code is going to look to create the HDF5 output.
    num_pix = tailcuts_data_volume_reducer_and_application_to_waveform(camera, image_dl1, waveform_dl0)

    return num_pix


    #print(" ok apply zero suppresion")


def tailcuts_data_volume_reducer_and_application_to_waveform(
        geom,
        image,
        waveforms,
        end_dilates=1,
        picture_thresh=7,
        boundary_thresh=5,
        iteration_thresh=5,
        keep_isolated_pixels=True,
        min_number_picture_neighbors=0,
    ):
        """
        Reduce the image in 3 Steps:
        1) Select pixels with tailcuts_clean.
        2) Add iteratively all pixels with Signal S >= iteration_thresh
           with ctapipe module dilate until no new pixels were added.
        3) Adding new pixels with dilate to get more conservative.
        Parameters
        ----------
        geom: `ctapipe.instrument.CameraGeometry`
            Camera geometry information
        waveforms: ndarray
            Waveforms stored in a numpy array of shape
            (n_pix, n_samples).
        picture_thresh: float or array
            threshold for tailcuts_clean above which all pixels are retained
        boundary_thresh: float or array.
            threshold for tailcuts_clean above which pixels are retained if
            they have a neighbor already above the picture_thresh.
        keep_isolated_pixels: bool
            For tailcuts_clean: If True, pixels above the picture threshold
            will be included always, if not they are only included if a
            neighbor is in the picture or boundary.
        min_number_picture_neighbors: int
            For tailcuts_clean: A picture pixel survives cleaning only if it
            has at least this number of picture neighbors. This has no effect
            in case keep_isolated_pixels is True
        iteration_thresh: float
            Threshold for the iteration step 2), above which pixels are
            selected.
        end_dilates: int
            Number of how many times to dilate at the end in Step 3).
        Returns
        -------
        reduced_waveforms : ndarray
            Reduced waveforms stored in a numpy array of shape
            (n_pix, n_samples).
        """
        #reduced_waveforms_mask = np.empty([waveforms.shape[0], 0], dtype=bool)
        reduced_waveforms_mask = np.empty([image.shape[0], 0], dtype=bool)

        #for i in range(waveforms.shape[1]):
        #    image = waveforms[:, [i]]

        # 1) Step: TailcutCleaning at first
        mask = tailcuts_clean(
            geom=geom,
            image=image,
            picture_thresh=picture_thresh,
            boundary_thresh=boundary_thresh,
            keep_isolated_pixels=keep_isolated_pixels,
            min_number_picture_neighbors=min_number_picture_neighbors
        )
        pixels_above_iteration_thresh = image >= iteration_thresh
        mask_for_loop = np.array([])
        # 2) Step: Add iteratively all pixels with Signal
        #          S > iteration_thresh with ctapipe module
        #          'dilate' until no new pixels were added.
        while not np.array_equal(mask, mask_for_loop):
            mask_for_loop = mask
            mask = dilate(geom, mask) & pixels_above_iteration_thresh

        # 3) Step: Adding Pixels with 'dilate' to get more conservative.
        for p in range(end_dilates):
            mask = dilate(geom, mask)

        reduced_waveforms_mask = np.column_stack((reduced_waveforms_mask,
                                                  mask))[:, 0]

        #return np.ma.masked_array(waveforms, mask=reduced_waveforms_mask)

        if np.sum(reduced_waveforms_mask) > 1755:
            return np.sum(reduced_waveforms_mask)

        # Apply mask to dl0
        for i in range(waveforms.shape[1]):
            waveforms[:, i][~reduced_waveforms_mask] = 0
            # If we want to do the SUM OF THE SLIDES, NOT all ZERO !
            # for j in range(len(waveforms.shape[0])):
            #     if not mask[j]:
            #         waveforms[i, j] = waveforms[j, :].sum()

        return np.sum(reduced_waveforms_mask)



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
    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help="simtel r1 input file",
                        required=False,
                        default='/Users/garciaenrique/CTA/data/data_notebooks/LST-1.1.Run00251.0000.fits.fz'
                        # default=get_dataset_path('gamma_test_large.simtel.gz')
                        )
    parser.add_argument('-o', '--output', help="hdf5 r1 output file",
                        required=False,
                        default='/Users/garciaenrique/CTA/output_mchdf5/dl0_251_manCal_DEBUG.h5')
    parser.add_argument('-m', '--max_event', help="maximum event to reconstuct",
                        required=False, type=int)
    parser.add_argument('-cl', '--compression_level', help="Compression level for the HDF5 file [0-9].",
                        required=False,
                        default=0, type=int)
    args = parser.parse_args()

    inputFileName = args.input
    nbTel = getNbTel(inputFileName)
    print("Number of telescope : ", nbTel)

    # Increase the number of nodes in cache if necessary (avoid warning about nodes reopening)
    tables.parameters.NODE_CACHE_SLOTS = max(tables.parameters.NODE_CACHE_SLOTS, 3 * nbTel + 20)

    telInfo_from_evt, nbEvent = getTelescopeInfoFromEvent(inputFileName, nbTel)
    print("Found", nbEvent, "events")
    hfile = openOutputFile(args.output, compressionLevel=args.compression_level)

    print('Create file structure')
    tableMcCorsikaEvent = createFileStructure(hfile, telInfo_from_evt)

    print('Fill the subarray layout informations')
    fillSubarrayLayout(hfile, telInfo_from_evt, nbTel)

    isSimulationMode = checkIsSimulationFile(telInfo_from_evt)

    # calib = CameraCalibrator()

    if isSimulationMode:
        print('Fill the optic description of the telescopes')
        fillOpticDescription(hfile, telInfo_from_evt, nbTel)

        print('Fill the simulation header informations')
        fillSimulationHeaderInfo(hfile, inputFileName)

    source = event_source(inputFileName)

    nb_event = 0
    max_event = 10000000
    if args.max_event != None:
        max_event = int(args.max_event)
    else:
        max_event = nbEvent
    print("\n")

    #source.allowed_tels = {1, 2 }
    for event in source:

        # calib(event)
        camera_config = get_camera_calib_config()
        apply_manual_calibration(event, camera_config)

        #print(event.dl1.tel[0].image.shape)
        num_selet_pix = apply_zero_suppression(event)
        if num_selet_pix > 1755:
            continue

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

    print("")
    end = time.time()
    print((end-start)/60., " min")

    print("")
    print("     PHOTO ELECTRON UNIT IN CENT - p.e  !!!!!, i.e. p.e / 100 !!! ")


if __name__ == '__main__':
    main()
