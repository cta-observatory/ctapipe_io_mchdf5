from setuptools import setup, find_packages
from os import path

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
	long_description = f.read()


entry_points = {}
entry_points['console_scripts'] = ['simtel2hdf5v1 = ctapipe_io_mchdf5.tools.simtel_2_hdf5_v1:main',
					'simtel2hdf5v2 = ctapipe_io_mchdf5.tools.simtel_2_hdf5_v2:main',
					'mchdf5v2minselection = ctapipe_io_mchdf5.tools.mchdf5_min_selection:main',
					'mchdf5v2sliceselection = ctapipe_io_mchdf5.tools.mchdf5_slice_selection:main',
					'mchdf5v2extractsignaltensor = ctapipe_io_mchdf5.tools.mchdf5_extract_signal_tensor:main',
					'mchdf5v2transpose = ctapipe_io_mchdf5.tools.mchdf5_transpose:main',
					'mchdf5v2meansigmasortpixelslice = ctapipe_io_mchdf5.tools.mchdf5_mean_sigma_sort:main',
					'mchdf5v2meansigmasortslicepixel = ctapipe_io_mchdf5.tools.mchdf5_mean_sigma_sort_slice_pixel:main',
					'mchdf5v2rangesort = ctapipe_io_mchdf5.tools.mchdf5_range_sort:main',
					]

setup(
	name='ctapipe_io_mchdf5',
	packages=find_packages(),
	version='0.1',
	description='ctapipe plugin for reading Monte-Carlo files (contains the same informations as Simtel files)',
	long_description=long_description,
	long_description_content_type='text/markdown',
	entry_points = entry_points,
	install_requires=[
		'numpy>=1.14.0', 
		'tables>=3.4.4',
		'ctapipe',
		'ctapipe-extra',
		'pytest-cov'
	],
	setup_requires=['pytest_runner'],
	package_data={
		'ctapipe_io_mchdf5': [
			'tests/resources/*'
		],
	},
	tests_require=['pytest'],
	author='Pierre Aubert',
	author_email='pierre.aubert@lapp.in2p3.fr',
	license='Cecil-C',
)
