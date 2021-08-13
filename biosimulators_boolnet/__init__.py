from .utils import get_boolnet


def get_simulator_version():
    """ Get the version of BoolNet

    Returns:
        :obj:`str`: version
    """
    pkg = get_boolnet()
    return pkg.__version__
