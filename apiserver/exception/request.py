class RequestError(Exception):
    pass


class TypeConvertError(RequestError):
    pass


class IncompleteParameterError(RequestError):
    pass
