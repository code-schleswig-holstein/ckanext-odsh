from pylons import config


class PreconditionViolated(Exception):
    def __init__(self, message):
        super(PreconditionViolated, self).__init__(message)


def not_on_slave(func):
    def wrapped(*args, **kwargs):
        if config.get('ckanext.odsh.slave', False):
            raise PreconditionViolated('not allowed on slave')
        return func(*args, **kwargs)

    if config.get('ckanext.odsh.debug', False):
        return wrapped
    return func
