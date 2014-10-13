#!/usr/bin/python3
"""
Ben's Deuce Testing Client
"""
from __future__ import print_function
import argparse
import json
import logging
import pprint
import sys

import deuceclient.client.deuce as client
import deuceclient.auth.nonauth as noauth
import deuceclient.auth.openstackauth as openstackauth
import deuceclient.auth.rackspaceauth as rackspaceauth


class ProgramArgumentError(ValueError):
    pass


def __api_operation_prep(log, arguments):
    """
    API Operation Common Functionality
    """
    # Parse the user data
    example_user_config_json = """
    {
        'user': <username>,
        'username': <username>,
        'user_name': <username>,
        'user_id': <userid>
        'tenant_name': <tenantname>,
        'tenant_id': <tenantid>,
        'apikey': <apikey>,
        'password': <password>,
        'token': <token>
    }

    Note: Only one of user, username, user_name, user_id, tenant_name,
          or tenant_id must be specified.

    Note: Only one of apikey, password, token must be specified.
        Token preferred over apikey or password.
        Apikey preferred over password.
    """
    auth_url = arguments.auth_service_url
    auth_provider = arguments.auth_service

    auth_data = {
        'user': {
            'value': None,
            'type': None
        },
        'credentials': {
            'value': None,
            'type': None
        }
    }

    def find_user(data):
        user_list = [
            ('user', 'user_name'),
            ('username', 'user_name'),
            ('user_name', 'user_name'),
            ('user_id', 'user_id'),
            ('tenant_name', 'tenant_name'),
            ('tenant_id', 'tenant_id'),
        ]

        for u in user_list:
            try:
                auth_data['user']['value'] = user_data[u[0]]
                auth_data['user']['type'] = u[1]
                return True
            except LookupError:
                pass

        return False

    def find_credentials(data):
        credential_list = ['token', 'password', 'apikey']
        for credential_type in credential_list:
            try:
                auth_data['credentials']['value'] = user_data[credential_type]
                auth_data['credentials']['type'] = credential_type
                return True
            except LookupError:
                pass

        return False

    user_data = json.load(arguments.user_config)
    if not find_user(user_data):
        sys.stderr.write('Unknown User Type.\n Example Config: {0:}'.format(
            example_user_config_json))
        sys.exit(-2)

    if not find_credentials(user_data):
        sys.stderr.write('Unknown Auth Type.\n Example Config: {0:}'.format(
            example_user_config_json))
        sys.exit(-3)

    # Setup the Authentication
    datacenter = arguments.datacenter

    asp = None
    if auth_provider == 'openstack':
        asp = openstackauth.OpenStackAuthentication

    elif auth_provider == 'rackspace':
        asp = rackspaceauth.RackspaceAuthentication

    elif auth_provider == 'none':
        asp = noauth.NonAuthAuthentication

    else:
        sys.stderr.write('Unknown Authentication Service Provider'
                         ': {0:}'.format(auth_provider))
        sys.exit(-4)

    auth_engine = asp(userid=auth_data['user']['value'],
                      usertype=auth_data['user']['type'],
                      credentials=auth_data['credentials']['value'],
                      auth_method=auth_data['credentials']['type'],
                      datacenter=datacenter,
                      auth_url=auth_url)

    # Deuce URL
    uri = arguments.url

    # Setup Agent Access
    deuce = client.DeuceClient(auth_engine, uri)

    return (auth_engine, deuce, uri)


def vault_create(log, arguments):
    """
    Create a vault with the given name
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    return not deuceclient.CreateVault(arguments.vault_name)


def vault_exists(log, arguments):
    """
    Determine whether or not a vault of the given name exists
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    result = deuceclient.VaultExists(arguments.vault_name)
    if result:
        print('Vault {0:} exists'.format(arguments.vault_name))
    else:
        print('Vault {0:} does NOT exist'.format(arguments.vault_name))


def vault_stats(log, arguments):
    """
    Get the Stats for the vault with the given name
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    stats = deuceclient.GetVaultStatistics(arguments.vault_name)
    for k in stats.keys():
        print('{0:} = {1:}'.format(k, stats[k]))


def vault_delete(log, arguments):
    """
    Delete the vault with the given name
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    deuceclient.DeleteVault(arguments.vault_name)


def block_list(log, arguments):
    """
    List the blocks in a vault
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    block_list = deuceclient.GetBlockList(arguments.vault_name,
                                          marker=arguments.marker,
                                          limit=arguments.limit)
    print('Block List:')
    pprint.pprint(block_list)


def block_upload(log, arguments):
    """
    Upload blocks to a vault
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    block_list = deuceclient.UploadBlock(arguments.vault_name,
                                         arguments.blockid,
                                         arguments.blockcontent)
    print('Block List:')
    pprint.pprint(block_list)


def file_create(log, arguments):
    """
    Creates a file
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    location = deuceclient.CreateFile(arguments.vault_name)
    print ("Location where file is create {0:}".format(location))


def file_assign_blocks(log, arguments):
    """
    Assign blocks to a file
    NEED to check the way value is passed in the command line,
    right now it does not accept it.
    """
    auth_engine, deuceclient, api_url = __api_operation_prep(log, arguments)

    result = deuceclient.AssignBlocksToFile(arguments.vaultname,
                                            arguments.fileid,
                                            arguments.value)
    print(result)


def main():
    arg_parser = argparse.ArgumentParser(
        description="Cloud Backup Agent Status")
    arg_parser.add_argument('--user-config',
                            default=None,
                            type=argparse.FileType('r'),
                            required=True,
                            help='JSON file containing username and API Key')
    arg_parser.add_argument('--url',
                            default='127.0.0.1:8080',
                            type=str,
                            required=False,
                            help="Network Address for the Deuce Server."
                                 " Default: 127.0.0.1:8080")
    arg_parser.add_argument('-lg', '--log-config',
                            default=None,
                            type=str,
                            dest='logconfig',
                            help='log configuration file')
    arg_parser.add_argument('-dc', '--datacenter',
                            default='ord',
                            type=str,
                            dest='datacenter',
                            required=True,
                            help='Datacenter the system is in',
                            choices=['lon', 'syd', 'hkg', 'ord', 'iad', 'dfw'])
    arg_parser.add_argument('--auth-service',
                            default='rackspace',
                            type=str,
                            required=False,
                            help='Authentication Service Provider',
                            choices=['openstack', 'rackspace', 'none'])
    arg_parser.add_argument('--auth-service-url',
                            default=None,
                            type=str,
                            required=False,
                            help='Authentication Service Provider URL')
    sub_argument_parser = arg_parser.add_subparsers(title='subcommands')

    vault_parser = sub_argument_parser.add_parser('vault')
    vault_parser.add_argument('--vault-name',
                              default=None,
                              required=True,
                              help="Vault Name")
    vault_subparsers = vault_parser.add_subparsers(title='operations',
                                                   help='Vault Operations')

    vault_create_parser = vault_subparsers.add_parser('create')
    vault_create_parser.set_defaults(func=vault_create)

    vault_exists_parser = vault_subparsers.add_parser('exists')
    vault_exists_parser.set_defaults(func=vault_exists)

    vault_stats_parser = vault_subparsers.add_parser('stats')
    vault_stats_parser.set_defaults(func=vault_stats)

    vault_delete_parser = vault_subparsers.add_parser('delete')
    vault_delete_parser.set_defaults(func=vault_delete)

    block_parser = sub_argument_parser.add_parser('blocks')
    block_parser.add_argument('--vault-name',
                              default=None,
                              required=True,
                              help="Vault Name")
    block_subparsers = block_parser.add_subparsers(title='operations',
                                                   help='Block Operations')

    block_list_parser = block_subparsers.add_parser('list')
    block_list_parser.add_argument('--marker',
                                   default=None,
                                   required=False,
                                   type=str,
                                   help="Marker for retrieving partial "
                                        "contents. Unspecified means "
                                        "return everything.")
    block_list_parser.add_argument('--limit',
                                   default=None,
                                   required=False,
                                   type=int,
                                   help="Number of entries to return at most")
    block_list_parser.set_defaults(func=block_list)

    block_upload_parser = block_subparsers.add_parser('upload')
    block_upload_parser.add_argument('--blockid',
                                     default=None,
                                     required=True,
                                     type=str,
                                     help="sha1 of the block to be uploaded.")
    block_upload_parser.add_argument('--blockcontent',
                                     default=None,
                                     required=True,
                                     type=argparse.FileType('r'),
                                     help="The block to be uploaded")
    block_upload_parser.set_defaults(func=block_upload)

    file_parser = sub_argument_parser.add_parser('files')
    file_parser.add_argument('--vault-name',
                             default=None,
                             required=True,
                             help="Vault Name")
    file_subparsers = file_parser.add_subparsers(title='operations',
                                                 help='File Operations')

    file_create_parser = file_subparsers.add_parser('create')
    file_create_parser.set_defaults(func=file_create)

    file_assign_parser = file_subparsers.add_parser('assign_data')
    file_assign_parser.add_argument('--fileid',
                                    default=None,
                                    required=True,
                                    type=str,
                                    help="File to assign it to.")
    file_assign_parser.add_argument('--value',
                                    default=None,
                                    required=True,
                                    type=dict,
                                    help="Value passed in as a dict "
                                         "with offset and size")
    file_assign_parser.set_defaults(func=file_assign_blocks)
    arguments = arg_parser.parse_args()

    # If the caller provides a log configuration then use it
    # Otherwise we'll add our own little configuration as a default
    # That captures stdout and outputs to output/integration-slave-server.out
    if arguments.logconfig is not None:
        logging.config.fileConfig(arguments.logconfig)
    else:
        lf = logging.FileHandler('.deuce_client-py.log')
        lf.setLevel(logging.DEBUG)

        log = logging.getLogger()
        log.addHandler(lf)
        log.setLevel(logging.DEBUG)

    # Build the logger
    log = logging.getLogger()

    arguments.func(log, arguments)


if __name__ == "__main__":
    sys.exit(main())
