# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

from .imdb import imdb
# from .pascal_voc import pascal_voc
from .soton_ear import soton_ear
from . import factory

import os.path as osp
import sys
if sys.platform == "linux" or sys.platform == "linux2":
    ROOT_DIR = osp.join("/home/harrysocool/Github/fast-rcnn")
elif sys.platform == "darwin":
    ROOT_DIR = osp.join("/Users/harrysocool/Github/fast-rcnn")

# We assume your matlab binary is in your path and called `matlab'.
# If either is not true, just add it to your path and alias it as matlab, or
# you could change this file.
MATLAB = 'matlab'

# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def _which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

if _which(MATLAB) is None:
    msg = ("MATLAB command '{}' not found. "
           "Please add '{}' to your PATH.").format(MATLAB, MATLAB)
    raise EnvironmentError(msg)
