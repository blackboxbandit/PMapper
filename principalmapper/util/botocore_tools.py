"""Utility functions for working with botocore"""

#  Copyright (c) NCC Group and Erik Steringer 2019. This file is part of Principal Mapper.
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

import logging
from typing import Dict, List, Optional, Set

import botocore.session
import botocore.exceptions


logger = logging.getLogger(__name__)

# Module-level cache: maps session id -> set of enabled region names
_enabled_regions_cache: Dict[int, Set[str]] = {}


def get_session(profile_arg: Optional[str], stsargs: Optional[dict] = None) -> botocore.session.Session:
    """Returns a botocore Session object taking into consideration Env-vars, etc.

    Tries to follow order from: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
    """
    # get default session which handles Env-vars, etc.
    result = botocore.session.get_session()

    # command-line args (--profile)
    if profile_arg is not None:
        result.set_config_variable('profile', profile_arg)

    # handles args for creating the STS client
    if stsargs is None:
        processed_stsargs = {}
    else:
        processed_stsargs = stsargs

    stsclient = result.create_client('sts', **processed_stsargs)
    stsclient.get_caller_identity()  # raises error if it's not workable
    return result


def get_enabled_regions(session: botocore.session.Session, client_args_map: Optional[dict] = None) -> Optional[Set[str]]:
    """Calls EC2 describe_regions(AllRegions=False) to get only the regions enabled in this account.

    A disabled region won't have ANY regional service available (ECS, SageMaker, Lambda, etc.),
    so this single EC2 call lets us skip disabled regions for all services.

    Returns a set of enabled region names, or None if the call fails (in which case the caller
    should fall back to the full botocore list).

    Results are cached per session so this API is called at most once per run.
    """
    cache_key = id(session)
    if cache_key in _enabled_regions_cache:
        return _enabled_regions_cache[cache_key]

    try:
        ec2args = (client_args_map or {}).get('ec2', {})
        ec2client = session.create_client('ec2', region_name='us-east-1', **ec2args)
        response = ec2client.describe_regions(AllRegions=False)
        enabled = {r['RegionName'] for r in response['Regions']}
        _enabled_regions_cache[cache_key] = enabled
        logger.info('Account has {} enabled regions (disabled regions will be skipped)'.format(len(enabled)))
        logger.debug('Enabled regions: {}'.format(sorted(enabled)))
        return enabled
    except (botocore.exceptions.ClientError, botocore.exceptions.NoCredentialsError, Exception) as ex:
        logger.warning('Unable to determine enabled regions via EC2 describe_regions. '
                       'All regions will be checked. Error: {}'.format(ex))
        return None


def get_regions_to_search(session: botocore.session.Session, service_name: str,
                          region_allow_list: Optional[List[str]] = None,
                          region_deny_list: Optional[List[str]] = None,
                          client_args_map: Optional[dict] = None) -> List[str]:
    """Using a botocore Session object, the name of a service, and either an allow-list or a deny-list (but not both),
    return a list of regions to be used during the gathering process.

    This first gets the service's available regions via botocore, then filters them against the
    account's enabled regions (via EC2 describe_regions). Disabled regions are automatically
    excluded since no regional service is available in a disabled region.

    If the allow-list is specified, the returned list is the intersection of the base list and the allow-list.
    If the deny-list is specified, the returned list is the base list minus the elements of the deny-list.
    A ValueError is thrown if the allow-list AND deny-list are both not None.
    """

    if region_allow_list is not None and region_deny_list is not None:
        raise ValueError('This function allows only either the allow-list or the deny-list, but NOT both.')

    # Start with all regions botocore knows about for this service
    all_service_regions = session.get_available_regions(service_name)

    # Filter out disabled regions (this is the key optimization)
    enabled = get_enabled_regions(session, client_args_map)
    if enabled is not None:
        base_list = [r for r in all_service_regions if r in enabled]
        skipped = len(all_service_regions) - len(base_list)
        if skipped > 0:
            logger.debug('Skipping {} disabled regions for {}'.format(skipped, service_name))
    else:
        base_list = all_service_regions

    # Apply allow/deny list filtering
    result = []

    if region_allow_list is not None:
        for element in base_list:
            if element in region_allow_list:
                result.append(element)
    elif region_deny_list is not None:
        for element in base_list:
            if element not in region_deny_list:
                result.append(element)
    else:
        result = base_list

    logger.debug('Final list of regions for {}: {}'.format(service_name, result))

    return result
