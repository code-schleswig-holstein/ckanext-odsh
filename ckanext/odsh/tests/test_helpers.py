import contextlib
import errno
import functools
from ckan.common import config


def odsh_test():
    return change_config()


def change_config():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with changed_config():
                return func(*args, **kwargs)
        return wrapper
    return decorator


@contextlib.contextmanager
def changed_config():
    _original_config = config.copy()
    config['ckanext.odsh.spatial.mapping'] = 'file:///usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/tests/spatial_mapping.csv'
    config['licenses_group_url']='file:///usr/lib/ckan/default/src/ckanext-odsh/licenses.json'
    try:
        yield
    finally:
        config.clear()
        config.update(_original_config)
