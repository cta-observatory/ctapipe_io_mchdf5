"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""

from ctapipe.io.eventsource import EventSource


def getNbTel(inputFileName):
	"""
	Get the number of telescope in the simulation file
	Parameters:
		inputFileName : name of the input file to be used

	Return:
		number of telescopes in the simulation file
	"""
	with EventSource(input_url=inputFileName) as source:
		nbTel = source.subarray.num_tels
		return nbTel
