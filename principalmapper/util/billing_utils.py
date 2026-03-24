"""Utility functions for querying AWS Cost Explorer to identify active regions and services."""

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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import botocore.session
import botocore.exceptions


logger = logging.getLogger(__name__)

# Maps Cost Explorer service names to PMapper edge checker service keys
_CE_SERVICE_TO_PMAPPER = {
    'Amazon Elastic Compute Cloud - Compute': 'ec2',
    'Amazon EC2': 'ec2',
    'AWS Lambda': 'lambda',
    'Amazon SageMaker': 'sagemaker',
    'AWS CodeBuild': 'codebuild',
    'AWS CloudFormation': 'cloudformation',
    'Amazon EC2 Auto Scaling': 'autoscaling',
    'AWS Systems Manager': 'ssm',
    'AWS Identity and Access Management': 'iam',
    'AWS Security Token Service': 'sts',
    'Amazon Simple Storage Service': 's3',
    'Amazon Simple Notification Service': 'sns',
    'Amazon Simple Queue Service': 'sqs',
    'AWS Key Management Service': 'kms',
    'AWS Secrets Manager': 'secretsmanager',
}


def check_billing_access(session: botocore.session.Session) -> bool:
    """Check if the current credentials have permission to query Cost Explorer.

    Returns True if ce:GetCostAndUsage is accessible, False otherwise.
    """
    try:
        ce_client = session.create_client('ce', region_name='us-east-1')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        return True
    except botocore.exceptions.ClientError as ex:
        if 'AccessDenied' in str(ex) or 'OptIn' in str(ex):
            return False
        logger.debug('Unexpected error checking billing access: {}'.format(ex))
        return False
    except Exception as ex:
        logger.debug('Unexpected error checking billing access: {}'.format(ex))
        return False


def get_active_services_and_regions(session: botocore.session.Session,
                                     lookback_days: int = 30) -> Optional[Tuple[Set[str], Set[str]]]:
    """Query Cost Explorer for the last N days to find active services and regions.

    Returns a tuple of (active_services, active_regions) where:
    - active_services: set of PMapper service keys that had non-zero spend
    - active_regions: set of AWS region names that had non-zero spend

    Returns None if the query fails (permissions, etc).
    Always includes 'iam' and 'sts' in active_services since they are always relevant.
    """
    try:
        ce_client = session.create_client('ce', region_name='us-east-1')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

        # Query 1: Get active services
        service_response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        active_services = {'iam', 'sts'}  # Always include IAM and STS
        ce_service_names = set()
        for time_period in service_response['ResultsByTime']:
            for group in time_period['Groups']:
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0:
                    ce_service_names.add(service_name)
                    if service_name in _CE_SERVICE_TO_PMAPPER:
                        active_services.add(_CE_SERVICE_TO_PMAPPER[service_name])

        # Query 2: Get active regions
        region_response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'REGION'}]
        )

        active_regions = set()
        for time_period in region_response['ResultsByTime']:
            for group in time_period['Groups']:
                region_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0 and region_name and region_name != 'global' and region_name != 'NoRegion':
                    active_regions.add(region_name)

        logger.info('Billing data: {} active services, {} active regions (last {} days)'.format(
            len(active_services), len(active_regions), lookback_days))
        logger.debug('Active services: {}'.format(sorted(active_services)))
        logger.debug('Active regions: {}'.format(sorted(active_regions)))

        return active_services, active_regions

    except botocore.exceptions.ClientError as ex:
        logger.warning('Unable to query Cost Explorer: {}'.format(ex))
        return None
    except Exception as ex:
        logger.warning('Unexpected error querying Cost Explorer: {}'.format(ex))
        return None


def format_billing_summary(active_services: Set[str], active_regions: Set[str]) -> str:
    """Format the billing discovery results for display to the user."""
    lines = []
    lines.append('')
    lines.append('  ╔══════════════════════════════════════════════════════════════╗')
    lines.append('  ║  Billing-Aware Optimization                                 ║')
    lines.append('  ╠══════════════════════════════════════════════════════════════╣')

    lines.append('  ║  Active Regions ({:>2}):                                       ║'.format(len(active_regions)))
    # Show regions in sorted order, 3 per line
    sorted_regions = sorted(active_regions)
    for i in range(0, len(sorted_regions), 3):
        chunk = sorted_regions[i:i+3]
        region_str = ', '.join(chunk)
        lines.append('  ║    {:<56}║'.format(region_str))

    lines.append('  ║                                                              ║')
    lines.append('  ║  Active Services ({:>2}):                                      ║'.format(len(active_services)))
    sorted_services = sorted(active_services)
    for i in range(0, len(sorted_services), 4):
        chunk = sorted_services[i:i+4]
        service_str = ', '.join(chunk)
        lines.append('  ║    {:<56}║'.format(service_str))

    lines.append('  ╚══════════════════════════════════════════════════════════════╝')
    lines.append('')
    return '\n'.join(lines)
