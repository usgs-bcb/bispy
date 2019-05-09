# BIS PACKAGE

import pkg_resources  # part of setuptools


# Import bis objects
from . import aws
from . import itis
from . import worms
from . import natureserve
from . import tess
from . import xdd
from . import gap

# provide version, PEP - three components ("major.minor.micro")
__version__ = pkg_resources.require("bispy")[0].version


# metadata retrieval
def get_package_metadata():
    d = pkg_resources.get_distribution('bispy')
    for i in d._get_metadata(d.PKG_INFO):
        print(i)
