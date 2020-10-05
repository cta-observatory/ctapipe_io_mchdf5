"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

from ctapipe.io import event_source


def getNbTel(inputFileName):
	"""
	Get the number of telescope in the simulation file
	Parameters:
		inputFileName : name of the input file to be used

	Return:
		number of telescopes in the simulation file
	"""
	with event_source(inputFileName) as source:
		nbTel = source.subarray.num_tels
		return nbTel
