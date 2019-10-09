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
