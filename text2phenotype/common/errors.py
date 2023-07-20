

############################################################
# Text2phenotype Errors

class Text2phenotypeError(Exception):

    def __init__(self, error=None, cause=None):
        self.error = error
        self.cause = cause

    def __str__(self):
        return str(self.__dict__)


class FileTypeError(Text2phenotypeError):
    pass


class ChecksumError(Text2phenotypeError):
    pass


class TransportError(Text2phenotypeError):
    pass


class CCDAError(Text2phenotypeError):
    pass


class MonitorError(Text2phenotypeError):
    pass


class EMRError(Text2phenotypeError):
    pass


class NLPError(Text2phenotypeError):
    pass


class FHIRError(Text2phenotypeError):
    pass
