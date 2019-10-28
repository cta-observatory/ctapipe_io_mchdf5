"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

import os
import sys

import argparse

import numpy as np
import tables
import hipecta.hdf5_utils as hdu
import hipecta.pixelselection as pixselec
import hipecta.core as core
from ctapipe_io_mchdf5.tools import copyAllTelWithoutWaveform, createWaveformTel


def computeSelectionTailCutDilation(fileOut, telNodeOut, telNodeIn, tabFocalTel, nbGain, center=4, neighbours=2,
                                    min_number_picture_neighbors=2, dilationThreshold=0):
    '''
	Compute the true and false positive for the pixel selection
	------------
	Parameters:
		telNodeOut : telescope node to be used
		telNodeIn : telescope of input data to be used for the selection
		tabFocalTel : table fo the focal tel of all telescopes
		nbGain : number of gain recorded on the camera
		center : float - center threshold parameter
		neighbours : float - neighbours threshold parameter
		min_number_picture_neighbors : minimum number of selected neighbours of the current pixel
		dilationThreshold : number of rows to be added around the selected pixel
	'''
    telType = np.uint64(telNodeOut.telType.read())
    print("computeSelectionTailCutDilation : start telescope :", telNodeOut._v_name, " of type", telType, ", with",
          nbGain, "channels")
    print("\tInitialise temporary reco")
    reco_temporary = hdu.createTemporaryRecoR1V2(fileOut, telNodeOut, tabFocalTel, 0.1)
    print("\tget waveform hi")
    tabDataWaveformHi = telNodeIn.waveformHi.col("waveformHi")
    tableOutWaveforHi = telNodeOut.waveformHi
    rowOutWaveformHi = tableOutWaveforHi.row

    if nbGain > 1:
        print("\tget waveform lo")
        tabDataWaveformLo = telNodeIn.waveformLo.col("waveformLo")
        tableOutWaveforLo = telNodeOut.waveformLo
        rowOutWaveformLo = tableOutWaveforLo.row

        i = 0
        for signalHi, signalLo in zip(tabDataWaveformHi, tabDataWaveformLo):
            print("\tcomputeSelectionTailCutDilation : hi telescope :", telNodeOut._v_name, ", event no", i)
            tabCalibIntegrateSignal = core.fullCalibIntegration(signalHi, reco_temporary)
            cleaned = hdu.tailcut_cleaning(telType, tabCalibIntegrateSignal, center, neighbours, False,
                                           min_number_picture_neighbors)
            maskSelection = hdu.dilation(telType, tabCalibIntegrateSignal, cleaned, dilationThreshold,
                                         center / 3)  # center/3 From Lenka presentation about Intelligent cleaning

            selectedWaveFormHi = pixselec.selectPixelWaveform(signalHi, maskSelection)
            rowOutWaveformHi["waveformHi"] = selectedWaveFormHi
            rowOutWaveformHi.append()

            selectedWaveFormLo = pixselec.selectPixelWaveform(signalLo, maskSelection)
            rowOutWaveformLo["waveformLo"] = selectedWaveFormLo
            rowOutWaveformLo.append()
            i += 1
        print("\tcomputeSelectionTailCutDilation :  hi flush telescope :", telNodeOut._v_name)
        tableOutWaveforHi.flush()
        tableOutWaveforLo.flush()
    else:
        i = 0
        for signalHi in tabDataWaveformHi:
            print("\tcomputeSelectionTailCutDilation : lo telescope :", telNodeOut._v_name, ", event no", i)
            tabCalibIntegrateSignal = core.fullCalibIntegration(signalHi, reco_temporary)
            cleaned = hdu.tailcut_cleaning(telType, tabCalibIntegrateSignal, center, neighbours, False,
                                           min_number_picture_neighbors)
            maskSelection = hdu.dilation(telType, tabCalibIntegrateSignal, cleaned, dilationThreshold,
                                         center / 3)  # center/3 From Lenka presentation about Intelligent cleaning

            selectedWaveFormHi = pixselec.selectPixelWaveform(signalHi, maskSelection)
            rowOutWaveformHi["waveformHi"] = selectedWaveFormHi
            rowOutWaveformHi.append()
            i += 1
        print("\tcomputeSelectionTailCutDilation : lo flush telescope :", telNodeOut._v_name)
        tableOutWaveforHi.flush()

    print("\tcomputeSelectionTailCutDilation : finish telescope :", telNodeOut._v_name)


def tailcutDilationSelectionTel(fileOut, telNodeOut, telNodeIn, tabFocalTel, center, neighbours,
                                min_number_picture_neighbors, dilation):
    '''
	Select the pixel, with a tailcut/dilation method, of the current telescope
	-----------------
	Parameters:
		fileOut : output hdf5 file
		telNodeOut : output telescope node
		telNodeIn : input telescope node
		tabFocalTel : table of the focal lenght of all telescopes
		center : float - center threshold parameter
		neighbours : float - neighbours threshold parameter
		min_number_picture_neighbors : minimum number of neighbours to be around a pixel to keep it
		dilation : threshold to be used at the dilation step
	'''
    nbSlice = np.uint64(telNodeOut.nbSlice.read())
    nbPixel = np.uint64(telNodeOut.nbPixel.read())
    image_shape = (nbSlice, nbPixel)

    nbGain = np.uint64(telNodeOut.nbGain.read())
    createWaveformTel(fileOut, telNodeOut, nbGain, image_shape)

    computeSelectionTailCutDilation(fileOut, telNodeOut, telNodeIn, tabFocalTel, nbGain, center, neighbours,
                                    min_number_picture_neighbors, dilation)



def tailcutDilationSelectionAllTelescopes(fileOut, fileIn, center, neighbours, min_number_picture_neighbors, dilation):
    '''
	Select the pixel, with a tailcut/dilation method, of the file
	-----------------
	Parameters:
		fileOut : output hdf5 file
		fileIn : input hdf5 file
		center : float - center threshold parameter
		neighbours : float - neighbours threshold parameter
		min_number_picture_neighbors : minimum number of neighbours to be around a pixel to keep it
		dilation : threshold to be used at the dilation step
	'''
    print("tailcutDilationSelectionAllTelescopes : copy telescope data without waveform")
    copyAllTelWithoutWaveform(fileOut, fileIn)

    tabFocalTel = fileIn.root.instrument.subarray.telescope.optics.col("equivalent_focal_length")

    # fullTabTruePositive = np.empty(0)
    # fullTabFalsePositive = np.empty(0)
    print("tailcutDilationSelectionAllTelescopes : Make selection")
    for telNodeIn, telNodeOut in zip(fileIn.walk_nodes("/r1", "Group"), fileOut.walk_nodes("/r1", "Group")):
        try:
            tailcutDilationSelectionTel(fileOut, telNodeOut, telNodeIn, tabFocalTel, center, neighbours,
                                        min_number_picture_neighbors, dilation)

        # fullTabTruePositive = np.concatenate((fullTabTruePositive, tabTruePositive))
        # fullTabFalsePositive = np.concatenate((fullTabFalsePositive, tabFalsePositive))
        except tables.exceptions.NoSuchNodeError as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e, exc_type, fname, exc_tb.tb_lineno)


# print("Nb points :",len(fullTabTruePositive))
# plt.figure(figsize=(20,10))
# ax = pixselec.plotTrueFalsePositive(fullTabTruePositive, fullTabFalsePositive, bins=3)

# ax.grid()
# plt.savefig("zstd9_TCDSelection_"+str(len(fullTabTruePositive))+"_pointsPerColor_cleaningTailcut_"+str(center)+"_"+str(neighbours)+"_"+str(min_number_picture_neighbors)+"_dilation_"+str(dilation)+".png")
# plt.clf()


def getFileSize(fileNameOut):
    '''
	Get the size of the output file in bytes
	Parameters:
	-----------
		fileNameOut : file to be opened
	Return:
	-------
		size of the file in bytes
	'''
    hfile = tables.open_file(fileNameOut, "r")
    fileSize = hfile.get_filesize()
    hfile.close()
    return fileSize


def tailcutDilationSelectionRunFile(fileNameOut, fileNameIn, center, neighbours, min_number_picture_neighbors,
                                    dilation, compression_level):
    '''
	Select the pixel, with a tailcut/dilation method, of the run file
	-----------------
	Parameters:
		fileNameOut : output hdf5 file name
		fileNameIn : input hdf5 file name
		center : float - center threshold parameter
		neighbours : float - neighbours threshold parameter
		min_number_picture_neighbors : minimum number of neighbours to be around a pixel to keep it
		dilation : threshold to be used at the dilation step
		compression_level : compression level to be used with zstd
	'''
    fileIn = tables.open_file(fileNameIn, "r")

    zstdFilter = tables.Filters(complevel=compression_level, complib='blosc:zstd', shuffle=False,
                                bitshuffle=False, fletcher32=False)
    fileOut = tables.open_file(fileNameOut, mode="w", filters=zstdFilter)

    # Copy the instrument and simulation groups
    try:
        fileOut.copy_node(fileIn.root.instrument, newparent=fileOut.root, recursive=True)
    except tables.exceptions.NoSuchNodeError as e:
        print("tailcutDilationSelectionRunFile : no instrument in the file '", fileNameIn, "'")
        pass
    try:
        fileOut.copy_node(fileIn.root.simulation, newparent=fileOut.root, recursive=True)
    except tables.exceptions.NoSuchNodeError as e:
        print("tailcutDilationSelectionRunFile : no simulation in the file '", fileNameIn, "'")
        pass

    tailcutDilationSelectionAllTelescopes(fileOut, fileIn, center, neighbours, min_number_picture_neighbors, dilation)

    fileOut.close()
    fileIn.close()

    fileSize = getFileSize(fileNameOut)
    print("Cleaning center = {}, neighbours = {}, min_number_picture_neighbors {}, dilation = {} produce a file \
	of {} bytes or {} MB".format(center, neighbours, min_number_picture_neighbors, dilation,
                                 fileSize, fileSize / 1000000))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help="MC hdf5 input file", required=True)
    parser.add_argument('-o', '--output', help="hdf5 v1 (selection convert to average) output file", required=True)
    parser.add_argument('-c', '--center', help="Center threshold for the tailcut cleaning", required=True, type=float)
    parser.add_argument('-n', '--neighbours', help="Neighbour threshold for the tailcut cleaning", required=True,
                        type=float)
    parser.add_argument('-d', '--dilation', help="Number of rings of dilation", required=True, type=int)
    parser.add_argument('-m', '--min_number_picture_neighbors',
                        help="Minimum number of neighbours to be consider around a pixel", required=True, type=int)
    parser.add_argument('-z', '--compressionlevel', help="Compression level to be used (from 1 to 9). Default = 1",
                        required=False, type=int, default=1)

    args = parser.parse_args()

    inputFileName = args.input
    outputFileName = args.output
    center = args.center
    neighbours = args.neighbours
    dilation = args.dilation
    min_number_picture_neighbors = args.min_number_picture_neighbors
    compression_level = args.compressionlevel

    tailcutDilationSelectionRunFile(outputFileName, inputFileName, center, neighbours, min_number_picture_neighbors,
                                    dilation, compression_level)
