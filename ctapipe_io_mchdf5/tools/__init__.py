'''
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
'''

from .telescope_copy import *
try:
	from .r1_utils import *
	from .r1_file import *
	from .dl0_utils import *
	from .simulation_utils import *
except:
	pass


def copyTelIntrSimuNode(fileOut, fileIn, r1NodeName="r1", docR1Node="Raw data waveform informations of the run", chunkshape=1):
	'''
	Create all the telescopes without the waveform
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		r1NodeName : name of the node to be created
		docR1Node : documentation of the created node
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	'''
	copyAllTelWithoutWaveform(fileOut, fileIn, r1NodeName=r1NodeName, docR1Node=docR1Node, chunkshape=chunkshape)
	#Copy the instrument and simulation groups
	try:
		fileOut.copy_node(fileIn.root.instrument, newparent=fileOut.root, recursive=True)
	except tables.exceptions.NoSuchNodeError as e:
		print("analysedInputFileHDF5 : no instrument in the file '",fileNameIn,"'")
		pass
	try:
		fileOut.copy_node(fileIn.root.simulation, newparent=fileOut.root, recursive=True)
	except tables.exceptions.NoSuchNodeError as e:
		print("analysedInputFileHDF5 : no simulation in the file '",fileNameIn,"'")
		pass
	


