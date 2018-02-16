import ctypes
from ctypes.util import find_library
import operator


def load_alpm(name=None):
    # Load the alpm library and set up some of the functions we might use
    if name is None:
        name = find_library('alpm')
    if name is None:
        # couldn't locate the correct library
        return None
    try:
        alpm = ctypes.cdll.LoadLibrary(name)
    except OSError:
        return None
    try:
        alpm.alpm_version.argtypes = ()
        alpm.alpm_version.restype = ctypes.c_char_p
        alpm.alpm_pkg_vercmp.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
        alpm.alpm_pkg_vercmp.restype = ctypes.c_int
    except AttributeError:
        return None

    return alpm


ALPM = load_alpm()

class AlpmAPI(object):
    OPERATOR_MAP = {
        '=':  operator.eq,
        '==': operator.eq,
        '!=': operator.ne,
        '<':  operator.lt,
        '<=': operator.le,
        '>':  operator.gt,
        '>=': operator.ge,
    }

    def __init__(self):
        self.alpm = ALPM
        self.available = ALPM is not None

    def version(self):
        if not self.available:
            return None
        return ALPM.alpm_version()

    def vercmp(self, ver1, ver2):
        if not self.available:
            return None
        return ALPM.alpm_pkg_vercmp(str(ver1), str(ver2))

    def compare_versions(self, ver1, oper, ver2):
        func = self.OPERATOR_MAP.get(oper, None)
        if func is None:
            raise Exception("Invalid operator %s specified" % oper)
        if not self.available:
            return None
        res = self.vercmp(ver1, ver2)
        return func(res, 0)


def main():
    api = AlpmAPI()
    print((api.version()))
    print((api.vercmp(1, 2)))
    print((api.compare_versions(1, '<', 2)))


if __name__ == '__main__':
    main()

# vim: set ts=4 sw=4 et:
