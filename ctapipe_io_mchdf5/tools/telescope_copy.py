"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

import tables


def copy_telescope_without_waveform(outFile, telNode, r1NodeName="r1", chunkshape=1):
	"""
	Copy the telescope node but not the waveform ones
	Parameters:
	-----------
		outFile : HDF5 file to be used
		telNode : telescope node to be copied
		r1NodeName : name of the node to be used
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	Return:
	-------
		created camera node
	"""
	nbPixel = telNode.nbPixel
	telGroupName = telNode._v_name
	print("copy_telescope_without_waveform : telName = '",telGroupName,"'")

	cam_tel_group = outFile.create_group("/"+r1NodeName, telGroupName, 'Data of telescopes '+telGroupName)

	outFile.copy_node(nbPixel, newparent=cam_tel_group, recursive=True)
	outFile.copy_node(telNode.nbSlice, newparent=cam_tel_group, recursive=True)
	outFile.copy_node(telNode.nbGain, newparent=cam_tel_group, recursive=True)
	outFile.copy_node(telNode.telIndex, newparent=cam_tel_group, recursive=True)
	outFile.copy_node(telNode.telType, newparent=cam_tel_group, recursive=True)
	outFile.copy_node(telNode.telId, newparent=cam_tel_group, recursive=True)
	try:
		outFile.copy_node(telNode.tabRefShape, newparent=cam_tel_group, recursive=True)
	except tables.exceptions.NoSuchNodeError as e:
		pass
	try:
		outFile.copy_node(telNode.tabGain, newparent=cam_tel_group, recursive=True)
	except tables.exceptions.NoSuchNodeError as e:
		pass

	outFile.copy_node(telNode.trigger, newparent=cam_tel_group, recursive=True)
	outFile.copy_node(telNode.pedestal, newparent=cam_tel_group, recursive=True)
	try:
		outFile.copy_node(telNode.photo_electron_image, newparent=cam_tel_group, recursive=True)
	except tables.exceptions.NoSuchNodeError as e:
		pass
	return cam_tel_group


def copy_all_tel_without_waveform(outFile, inFile, r1NodeName="r1", docR1Node="Raw data waveform informations of the run", chunkshape=1):
	"""
	Create all the telescopes without the waveform
	Parameters:
	-----------
		outFile : output file
		inFile : input file
		r1NodeName : name of the node to be created
		docR1Node : documentation of the created node
		chunkshape : shape of the chunk to be used to store the data of waveform and minimum
	"""
	outFile.create_group("/", r1NodeName, docR1Node)
	for telNode in inFile.walk_nodes("/r1", "Group"):
		try:
			copy_telescope_without_waveform(outFile, telNode, r1NodeName=r1NodeName, chunkshape=chunkshape)
		except tables.exceptions.NoSuchNodeError as e:
			pass

