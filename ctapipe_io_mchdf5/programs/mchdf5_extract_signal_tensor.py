'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

import tables
import numpy as np
import argparse

def tensorShapeToString(shape):
	'''
	Convert a tensor shape into a string
	Parameters:
		shape : shape to be converted into a string
	Return:
		corresponding string by respect to the shape
	'''
	strOut = ""
	for i,val in enumerate(shape):
		if i != 0:
			strOut += "_"
		strOut += str(val)
	return strOut


def signalESPtoPES(waveformHi):
	'''
	Convert the signal from Event Slice Pixel, to Pixel Event Slice 
	Parameters:
		waveformHi : input waveform (Event Slice Pixel)
	Return:
		tensor : Pixel Event Slice
	'''
	waveformHiSEP = waveformHi.swapaxes(0, 1)
	waveformHiPES = waveformHiSEP.swapaxes(0, 2)
	return waveformHiPES


def saveTensorSignalInFile(baseFileName, waveformHi):
	'''
	Save the tensors signal (for one channel) in sevral order (Event Slice pixel, Pixel Event Slice and Event Pixel Slice)
	Parameters:
		baseFileName : base name of the output file
		waveformHi : waveform to be saved for one channel
	'''
	waveformHi.tofile(baseFileName+"_"+tensorShapeToString(waveformHi.shape)+"_uint16.npybin")
	waveformHiPES = signalESPtoPES(waveformHi)
	waveformHiPES.tofile(baseFileName+"_"+tensorShapeToString(waveformHiPES.shape)+"_uint16.npybin")
	waveformHiEPS = waveformHiPES.swapaxes(0, 1)
	waveformHiEPS.tofile(baseFileName+"_"+tensorShapeToString(waveformHiEPS.shape)+"_uint16.npybin")


def extractSignalTensorTel(telNode, baseOutputFile):
	'''
	Extract the signal tensor of a whole file
	Parameters:
		telNode : telescope node to be used
		baseOutputFile : base of the output file name of the tensor to be saved
	'''
	telGroupName = telNode._v_name
	outputFileName = baseOutputFile + "_" + telGroupName
	
	waveformHi = telNode.waveformHi.col("waveformHi")
	saveTensorSignalInFile(outputFileName + "_Hi", waveformHi)
	
	try:
		waveformLo = telNode.waveformLo.col("waveformLo")
		saveTensorSignalInFile(outputFileName + "_Lo", waveformLo)
	except:
		pass
	


def extractSignalTensorFile(fileName):
	'''
	Extract the signal tensor of a whole file
	'''
	inFile = tables.open_file(inputFileName, "r")
	
	baseOutputFile = fileName.replace(".h5", "")
	
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			extractSignalTensorTel(telNode, baseOutputFile)
		except tables.exceptions.NoSuchNodeError as e:
			pass
	
	inFile.close()


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', help="hdf5 r1 v2 output file", required=True)
	
	args = parser.parse_args()

	inputFileName = args.input
	
	processSliceSelectionFile(inputFileName, outputFileName, firstSliceIndex, lastSliceIndex)


