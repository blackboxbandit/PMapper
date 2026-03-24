"""Code to implement the CLI interface to the graphing component of Principal Mapper"""

#  Copyright (c) NCC Group and Erik Steringer 2020. This file is part of Principal Mapper.
#
#      Principal Mapper is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      Principal Mapper is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with Principal Mapper.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
import os
import re
import sys
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path

from ..common import OrganizationTree, OrganizationNode, Graph
from . import graph_actions
from .cross_account_edges import get_edges_between_graphs
from .gathering import get_organizations_data
from .edge_identification import checker_map
from ..querying import query_orgs
from ..util import botocore_tools
from ..util.billing_utils import check_billing_access, get_active_services_and_regions, format_billing_summary
from ..util.storage import get_storage_root


logger = logging.getLogger(__name__)


def provide_arguments(parser: ArgumentParser):
    """Given a parser object (which should be a subparser), add arguments to provide a CLI interface to the
    graphing component of Principal Mapper.
    """

    graph_subparser = parser.add_subparsers(
        title='graph_subcommand',
        description='The subcommand to use in the graphing component of Principal Mapper',
        dest='picked_graph_cmd',
        help='Select a graph-subcommand to execute'
    )

    # args for commands fitting the pattern "pmapper graph create ..."
    create_parser = graph_subparser.add_parser(
        'create',
        description='Creates a Graph object for a given AWS account',
        help='Creates a Graph object for a given AWS account'
    )
    create_parser.add_argument(
        '--ignore-orgs',
        action='store_true',
        help='If specified, skips the check for stored AWS Organizations data and ignores any potentially applicable SCPs during the graph creation process'
    )
    create_parser.add_argument(
        '--quick',
        action='store_true',
        help='If specified, skips resource policy gathering (S3, SNS, SQS, KMS, SecretsManager) for faster graph creation. Useful for quick security scans where resource policies are not needed.'
    )
    create_parser.add_argument(
        '--billing-optimize',
        action='store_true',
        help='If specified, checks AWS Cost Explorer for active services and regions first. '
             'Prompts you to limit scanning to only active resources + IAM. '
             'Requires ce:GetCostAndUsage permission. Falls back to full scan if access is denied.'
    )
    create_parser.add_argument(
        '--billing-lookback',
        type=int,
        default=30,
        help='Number of days to look back in billing data (default: 30). Only used with --billing-optimize.',
        metavar='DAYS'
    )

    # create cmd args for commands where we pull data other than from the AWS APIs
    # TODO: add args for Scout Suite, etc. here
    alt_data_source_group = create_parser.add_mutually_exclusive_group()
    alt_data_source_group.add_argument(
        '--localstack-endpoint',
        help='The HTTP(S) endpoint for a running instance of LocalStack'
    )

    # create cmd args for including/excluding regions
    region_args_group = create_parser.add_mutually_exclusive_group()
    region_args_group.add_argument(
        '--include-regions',
        nargs='*',
        help='An allow-list of regions to pull data from, cannot be combined with --exclude-regions, the `global` region is always included',
        metavar='REGION'
    )
    region_args_group.add_argument(
        '--exclude-regions',
        nargs='*',
        help='A deny-list of regions to pull data from, cannot be combined with --include-regions, the `global` region is always included',
        metavar='REGION'
    )

    service_args_group = create_parser.add_mutually_exclusive_group()
    service_args_group.add_argument(
        '--include-services',
        nargs='*',
        help='An allow-list of services to search for Edge objects, cannot be combined with --exclude-services',
        metavar='SERVICE'
    )
    service_args_group.add_argument(
        '--exclude-services',
        nargs='*',
        help='A deny-list of services to search for Edge objects, cannot be combined with --include-services',
        metavar='SERVICE'
    )

    # args for commands fitting the pattern "pmapper graph display ..."
    display_parser = graph_subparser.add_parser(
        'display',
        description='Displays information about a Graph object for a given AWS account',
        help='Displays information about a Graph object for a given AWS account'
    )

    # args for commands fitting the pattern "pmapper graph list ..."
    list_parser = graph_subparser.add_parser(
        'list',
        description='List the Account IDs of graphs stored on this computer',
        help='List the accounts stored on this computer'
    )


def process_arguments(parsed_args: Namespace):
    """Given a namespace object generated from parsing args, perform the appropriate tasks. Returns an int
    matching expectations set by /usr/include/sysexits.h for command-line utilities."""

    if parsed_args.picked_graph_cmd is None:
        print('Error: No graph subcommand provided. Please select a subcommand (create, display, list).')
        return 64

    if parsed_args.picked_graph_cmd == 'create':
        logger.debug('Called create subcommand of graph')

        # filter the args first
        if parsed_args.account is not None:
            print('Cannot specify offline-mode param `--account` when calling `pmapper graph create`. If you have '
                  'credentials for a specific account to graph, you can use those credentials similar to how the '
                  'AWS CLI works (environment variables, profiles, EC2 instance metadata). In the case of using '
                  'a profile, use the `--profile [PROFILE]` argument before specifying the `graph` subcommand.')
            return 64

        service_list_base = list(checker_map.keys())
        if parsed_args.include_services is not None:
            service_list = [x for x in service_list_base if x in parsed_args.include_services]
        elif parsed_args.exclude_services is not None:
            service_list = [x for x in service_list_base if x not in parsed_args.exclude_services]
        else:
            service_list = service_list_base
        logger.debug('Service list after processing args: {}'.format(service_list))

        # need to know account ID to search potential SCPs
        if parsed_args.localstack_endpoint is not None:
            session = botocore_tools.get_session(parsed_args.profile, {'endpoint_url': parsed_args.localstack_endpoint})
        else:
            session = botocore_tools.get_session(parsed_args.profile)

        # Billing-aware optimization: check before anything else
        billing_region_list = None
        if getattr(parsed_args, 'billing_optimize', False):
            print('\n  Checking billing access...')
            if check_billing_access(session):
                lookback = getattr(parsed_args, 'billing_lookback', 30)
                billing_result = get_active_services_and_regions(session, lookback_days=lookback)
                if billing_result is not None:
                    active_services, active_regions = billing_result
                    print(format_billing_summary(active_services, active_regions))

                    # Ask user whether to limit scanning
                    try:
                        choice = input('  Limit scanning to these active services and regions? [Y/n/all] ').strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        choice = 'y'

                    if choice in ('', 'y', 'yes'):
                        # Filter service list to only active services (always keep iam, sts, generic_passrole)
                        always_include = {'iam', 'sts', 'generic_passrole'}
                        service_list = [s for s in service_list if s in active_services or s in always_include]
                        billing_region_list = sorted(active_regions)
                        print('  ✓ Limiting to {} services and {} regions'.format(
                            len(service_list), len(billing_region_list)))
                    elif choice in ('all',):
                        print('  → Scanning all services and regions')
                    else:
                        print('  → Scanning all services and regions')
                else:
                    print('  ⚠ Unable to retrieve billing data. Proceeding with full scan.')
            else:
                print('  ⚠ No billing access (ce:GetCostAndUsage). Proceeding with full scan.')
            print()

        # Determine region lists: billing override > CLI args
        region_allow_list = billing_region_list if billing_region_list else parsed_args.include_regions
        region_deny_list = None if billing_region_list else parsed_args.exclude_regions

        scps = None
        if not parsed_args.ignore_orgs:
            if parsed_args.localstack_endpoint is not None:
                stsclient = session.create_client('sts', endpoint_url=parsed_args.localstack_endpoint)
            else:
                stsclient = session.create_client('sts')
            caller_identity = stsclient.get_caller_identity()
            caller_account = caller_identity['Account']
            logger.debug("Caller Identity: {}".format(caller_identity))

            org_tree_search_dir = Path(get_storage_root())
            org_id_pattern = re.compile(r'^o-\w+$')
            for subdir in org_tree_search_dir.iterdir():
                if org_id_pattern.search(subdir.name) is not None:
                    logger.debug('Checking {} to see if account {} is a member'.format(str(subdir), caller_account))
                    org_tree = OrganizationTree.create_from_dir(str(subdir))
                    if caller_account in org_tree.accounts:
                        logger.info('Account {} is a member of Organization {}'.format(caller_account, org_tree.org_id))
                        if caller_account == org_tree.management_account_id:
                            logger.info('Account {} is the management account, SCPs do not apply'.format(caller_account))
                        else:
                            logger.info('Identifying and applying SCPs for the graphing process')
                            scps = query_orgs.produce_scp_list_by_account_id(caller_account, org_tree)
                        break

        if parsed_args.localstack_endpoint is not None:
            full_service_list = ('autoscaling', 'cloudformation', 'codebuild', 'ec2', 'iam', 'kms', 'lambda',
                                 'sagemaker', 's3', 'ssm', 'secretsmanager', 'sns', 'sts', 'sqs')

            client_args_map = {
                x: {'endpoint_url': parsed_args.localstack_endpoint} for x in full_service_list
            }
        else:
            client_args_map = None

        t_start = time.time()
        graph = graph_actions.create_new_graph(session, service_list, region_allow_list,
                                               region_deny_list, scps, client_args_map,
                                               skip_resource_policies=getattr(parsed_args, 'quick', False))
        elapsed = time.time() - t_start
        graph_actions.print_graph_data(graph)
        print('\n  Graph created in {:.1f} seconds.'.format(elapsed))
        if getattr(parsed_args, 'quick', False):
            print('  (Quick mode: resource policy gathering was skipped)')
        if billing_region_list:
            print('  (Billing-optimized: scanned {} regions only)'.format(len(billing_region_list)))
        graph.store_graph_as_json(os.path.join(get_storage_root(), graph.metadata['account_id']))

    elif parsed_args.picked_graph_cmd == 'display':
        if parsed_args.account is None:
            session = botocore_tools.get_session(parsed_args.profile)
        else:
            session = None

        graph = graph_actions.get_existing_graph(
            session,
            parsed_args.account
        )
        graph_actions.print_graph_data(graph)

    elif parsed_args.picked_graph_cmd == 'list':
        print("Account IDs:")
        print("---")
        storage_root = Path(get_storage_root())
        account_id_pattern = re.compile(r'\d{12}')
        for direct in storage_root.iterdir():
            if account_id_pattern.search(str(direct)) is not None:
                metadata_file = direct.joinpath(Path('metadata.json'))
                with open(str(metadata_file)) as fd:
                    account_metadata = json.load(fd)
                version = account_metadata['pmapper_version']
                print("{} (PMapper Version {})".format(direct.name, version))

    return 0
