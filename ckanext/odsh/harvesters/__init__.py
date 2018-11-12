# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

from ckanext.odsh.harvesters.statistikamtnordharvester import StatistikamtNordHarvester
from ckanext.odsh.harvesters.kielharvester import KielHarvester
from ckanext.odsh.harvesters.base import ODSHBaseHarvester
