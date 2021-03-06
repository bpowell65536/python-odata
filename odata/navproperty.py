# -*- coding: utf-8 -*-

try:
    # noinspection PyUnresolvedReferences
    from urllib.parse import urljoin
except ImportError:
    # noinspection PyUnresolvedReferences
    from urlparse import urljoin


class NavigationProperty(object):
    """
    A Property-like object for marking relationships between entities, but does
    not inherit from PropertyBase.
    """
    def __init__(self, name, entitycls, collection=False, foreign_key=None):
        from odata.property import PropertyBase
        self.name = name
        self.entitycls = entitycls
        self.is_collection = collection
        if isinstance(foreign_key, PropertyBase):
            self.foreign_key = foreign_key.name
        else:
            self.foreign_key = foreign_key

    def __repr__(self):
        return u'<NavigationProperty to {0}>'.format(self.entitycls)

    def instances_from_data(self, raw_data):
        if self.is_collection:
            return [self.entitycls.__new__(self.entitycls, from_data=d) for d in raw_data]
        else:
            return self.entitycls.__new__(self.entitycls, from_data=raw_data)

    def _get_parent_cache(self, instance):
        es = instance.__odata__
        ic = es.nav_cache
        if self.name not in ic:
            cache = {}
            ic[self.name] = cache
        else:
            cache = ic[self.name]
        return cache

    def __set__(self, instance, value):
        """
        :type instance: odata.entity.EntityBase
        """
        cache = self._get_parent_cache(instance)
        if self.is_collection:
            cache['collection'] = value
        else:
            cache['single'] = value
        instance.__odata__.set_property_dirty(self)

    def __get__(self, instance, owner):
        """
        :type instance: odata.entity.EntityBase
        """
        if instance is None:
            return self

        es = instance.__odata__
        parent_url = es.instance_url
        new_object = parent_url is None
        cache = self._get_parent_cache(instance)

        if new_object:
            if self.is_collection:
                return cache.get('collection', [])
            return cache.get('single', None)

        parent_url += '/'
        url = urljoin(parent_url, self.name)
        cnx = self.entitycls.__odata_connection__

        if self.is_collection:
            if 'collection' not in cache:
                raw_data = cnx.execute_get(url)
                if raw_data:
                    cache['collection'] = self.instances_from_data(raw_data['value'])
                else:
                    cache['collection'] = []
            return cache['collection']
        else:
            if 'single' not in cache:
                raw_data = cnx.execute_get(url)
                if raw_data:
                    cache['single'] = self.instances_from_data(raw_data)
                else:
                    cache['single'] = None
            return cache['single']
