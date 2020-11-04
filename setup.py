# -*- coding: utf-8 -*-

# A simple setup script to create an executable using PyQt5. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# Run the build process by running the command
#
# C:\Python36\python.exe setup.py build_exe
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

import sys, os.path
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'packages':['atexit', 'serial'],
    }
}

executables = [
    Executable( os.path.abspath('RMA_T0_Test.py'), base = base, icon = '11.ico')
]

setup(name='RMA_T0_Test',
      version='1.00',
      description='RMA_T0_Test',
      options=options,
      executables=executables
      )
