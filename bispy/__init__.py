# BIS PACKAGE

import pkg_resources  # part of setuptools


# Import bis objects
from . import bis
from . import aws
from . import itis
from . import worms
from . import natureserve
from . import ecos
from . import xdd
from . import gap
from . import iucn
from . import sgcn
from . import gbif

# provide version, PEP - three components ("major.minor.micro")
__version__ = pkg_resources.require("bispy")[0].version


# metadata retrieval
def get_package_metadata():
    d = pkg_resources.get_distribution('bispy')
    for i in d._get_metadata(d.PKG_INFO):
        print(i)
