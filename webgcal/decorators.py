# -*- coding: utf-8 -*-
from functools import update_wrapper 

def cache_property(func, name=None):
    """
    cache_property(func, name=None) -> a descriptor
        This decorator implements an object's property which is computed
        the first time it is accessed, and which value is then stored in
        the object's __dict__ for later use. If the attribute is deleted,
        the value will be recomputed the next time it is accessed.
        Usage:
            class X(object):
                @cachedProperty
                def foo(self):
                    return computation()
    """
    
    if name is None:
        name = func.__name__
    
    def _get(self):
        return self.__dict__.setdefault(name, func(self))
    
    def _del(self):
        return self.__dict__.pop(name, None)
    
    update_wrapper(_get, func)
    
    return property(_get, None, _del)
