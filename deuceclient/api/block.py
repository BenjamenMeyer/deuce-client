"""
Deuce Client - Block API
"""
import hashlib

from stoplight import validate

from deuceclient.common.validation import *


class Block(object):

    @staticmethod
    def make_id(data):
        sha1 = hashlib.sha1()
        sha1.update(data)
        return sha1.hexdigest().lower()

    # TODO: Add a validator for data, ref_count, ref_modified
    @validate(project_id=ProjectIdRule,
              vault_id=VaultIdRule,
              block_id=MetadataBlockIdRule,
              storage_id=StorageBlockIdRuleNoneOkay)
    def __init__(self, project_id, vault_id, block_id,
                 storage_id=None, data=None,
                 ref_count=None, ref_modified=None):
        self.__properties = {
            'project_id': project_id,
            'vault_id': vault_id,
            'block_id': block_id,
            'storage_id': storage_id,
            'data': data,
            'references': {
                'count': ref_count,
                'modified': ref_modified
            }
        }

    @property
    def project_id(self):
        return self.__properties['project_id']

    @property
    def vault_id(self):
        return self.__properties['vault_id']

    @property
    def block_id(self):
        return self.__properties['block_id']

    @property
    def storage_id(self):
        return self.__properties['storage_id']

    @storage_id.setter
    @validate(value=StorageBlockIdRule)
    def storage_id(self, value):
        self.__properties['storage_id'] = value

    @property
    def data(self):
        return self.__properties['data']

    # TODO: Add a validator
    @data.setter
    def data(self, value):
        self.__properties['data'] = value

    def __len__(self):
        if self.data is None:
            return 0
        else:
            return len(self.data)

    @property
    def ref_count(self):
        return self.__properties['references']['count']

    # TODO: Add a validator
    @ref_count.setter
    def ref_count(self, value):
        self.__properties['references']['count'] = value

    @property
    def ref_modified(self):
        return self.__properties['references']['modified']

    # TODO: Add a validator
    @ref_modified.setter
    def ref_modified(self, value):
        self.__properties['references']['modified'] = value
