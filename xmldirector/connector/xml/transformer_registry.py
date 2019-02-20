# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import six
import operator
import datetime

from zope.interface import implementer

from .interfaces import ITransformerRegistry
from ..logger import LOG


@implementer(ITransformerRegistry)
class TransformerRegistry(object):

    registry = {}

    def register_transformation(self, family, transformer_name, transformer_path, transformer_type='XSLT1'):
        """ Register a Transformation as tuple (``family``, ``transformer_name``).
            ``transformer_path`` is either an URI to the related transformation file on the filesystem (XSLT1)
            or a Python function implementing the IWrapper.

            Supported ``transformer_type``s so far: 'XSLT1', 'python'
        """

        if transformer_type == 'python':
            # ``transformer_path`` is Python function here
            transform = transformer_path
            if six.PY2:
                transformer_path = '{}(), {}'.format(transformer_path.__name__, transformer_path.__code__.co_filename)
            else:
                transformer_path = '{}(), {}'.format(transformer_path.__name__, transformer_path.__code__.co_filename)

        else:
            raise ValueError('Unsupported transformer type "{}"'.format(transformer_type))

        key = '{}::{}'.format(family, transformer_name)
        if key in self.registry:
            raise ValueError('Transformation {}/{} already registered'.format(family, transformer_name))

        self.registry[key] = dict(
            transform=transform,
            path=transformer_path,
            type=transformer_type,
            family=family,
            name=transformer_name,
            registered=datetime.datetime.utcnow())

        LOG.debug('Transformer registered ({}, {})'.format(key, transformer_path))

    def entries(self):
        """ Return all entries of the registry sorted by family + name """
        result = list(self.registry.values())
        return sorted(result, key=operator.itemgetter('family', 'name'))

    def clear(self):
        """ Remove all entries """
        self.registry.clear()

    def __len__(self):
        """ Return number of registered transformations """
        return len(self.registry)

    def get_transformation(self, family, transformer_name):
        """ Return a transformer by (family, transformer_name) """

        key = '{}::{}'.format(family, transformer_name)
        if key not in self.registry:
            raise ValueError('Transformation {}/{} not registered'.format(family, transformer_name))
        d = self.registry[key]
        if d['type'] == 'python':
            return d['transform']
        else:
            raise ValueError('Unsupported transformation type "{}"'.format(d['type']))


#        elif d['type'] == 'XSLT1':
#            return XSLT1Wrapper(d)
#        elif d['type'] in ('XSLT2', 'XSLT3'):
#            return SaxonWrapper(d)

TransformerRegistryUtility = TransformerRegistry()
