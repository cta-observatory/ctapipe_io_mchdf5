"""
	Auteur : Pierre Aubert
	Mail : aubertp7@gmail.com
	Licence : CeCILL-C
"""


def get_camera_type_from_name(camera_name):
	"""
	Get the type of the given camera by its name
	------------------
	Parameters :
		camera_name : name of the given camera
	------------------
	Return :
		Corresponding type of the camera
	"""
	# print("get_camera_type_from_name : camera_name = '"+str(camera_name)+"'")
	if camera_name == "LSTCam":
		return 0
	elif camera_name == "NectarCam":
		return 1
	elif camera_name == "FlashCam":
		return 2
	elif camera_name == "SCTCam":
		return 3
	elif camera_name == "ASTRICam":
		return 4
	elif camera_name == "DigiCam":
		return 5
	elif camera_name == "CHEC":
		return 6
	else:
		return 7


def get_camera_name_from_type(cam_type):
	"""
	Get the name of the given camera by its type
	------------------
	Parameters :
		cam_type : type of the given camera
	------------------
	Return :
		Corresponding name of the camera
	"""
	if cam_type == 0:
		return "LSTCam"
	elif cam_type == 1:
		return "NectarCam"
	elif cam_type == 2:
		return "FlashCam"
	elif cam_type == 3:
		return "SCTCam"
	elif cam_type == 4:
		return "ASTRICam"
	elif cam_type == 5:
		return "DigiCam"
	elif cam_type == 6:
		return "CHEC"
	else:
		return "UNKNOWN_cameraType"


def get_telescope_type_str_from_camera_type(cam_type):
	"""
	Get the type of the given telescope by its camera type
	------------------
	Parameters :
		cam_type : type of the given camera
	------------------
	Return :
		Corresponding type of the telescope
	"""
	if cam_type == 0:
		return "LST"
	elif cam_type in [1, 2, 3]:
		return "MST"
	elif cam_type in [4, 5, 6]:
		return "SST"
	else:
		return "UNKNOWN_telescopeType"
