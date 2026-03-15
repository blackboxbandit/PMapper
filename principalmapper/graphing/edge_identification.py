"""Code to coordinate identifying edges between principals in an AWS account"""

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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import botocore.session

from principalmapper.common import Edge, Node
from principalmapper.graphing.autoscaling_edges import AutoScalingEdgeChecker
from principalmapper.graphing.cloudformation_edges import CloudFormationEdgeChecker
from principalmapper.graphing.codebuild_edges import CodeBuildEdgeChecker
from principalmapper.graphing.ec2_edges import EC2EdgeChecker
from principalmapper.graphing.generic_passrole_edges import GenericPassRoleEdgeChecker
from principalmapper.graphing.iam_edges import IAMEdgeChecker
from principalmapper.graphing.lambda_edges import LambdaEdgeChecker
from principalmapper.graphing.sagemaker_edges import SageMakerEdgeChecker
from principalmapper.graphing.ssm_edges import SSMEdgeChecker
from principalmapper.graphing.sts_edges import STSEdgeChecker


logger = logging.getLogger(__name__)


# Externally referable dictionary with all the supported edge-checking types
checker_map = {
    'autoscaling': AutoScalingEdgeChecker,
    'cloudformation': CloudFormationEdgeChecker,
    'codebuild': CodeBuildEdgeChecker,
    'ec2': EC2EdgeChecker,
    'generic_passrole': GenericPassRoleEdgeChecker,
    'iam': IAMEdgeChecker,
    'lambda': LambdaEdgeChecker,
    'sagemaker': SageMakerEdgeChecker,
    'ssm': SSMEdgeChecker,
    'sts': STSEdgeChecker
}


def obtain_edges(session: Optional[botocore.session.Session], checker_list: List[str], nodes: List[Node],
                 region_allow_list: Optional[List[str]] = None, region_deny_list: Optional[List[str]] = None,
                 scps: Optional[List[List[dict]]] = None, client_args_map: Optional[dict] = None) -> List[Edge]:
    """Given a list of nodes and a botocore Session, return a list of edges between those nodes. Only checks
    against services passed in the checker_list param. Runs edge checkers concurrently for speed."""

    logger.info('Initiating edge checks.')
    logger.debug('Services being checked for edges: {}'.format(checker_list))

    checker_objs = []
    for check in checker_list:
        if check in checker_map:
            checker_objs.append((check, checker_map[check](session)))

    def _run_checker(name_and_checker):
        """Execute a single edge checker and return its edges with timing info."""
        name, checker_obj = name_and_checker
        t0 = time.time()
        logger.info('[Edge Check] Starting: {}'.format(name))
        edges = checker_obj.return_edges(nodes, region_allow_list, region_deny_list, scps, client_args_map)
        elapsed = time.time() - t0
        logger.info('[Edge Check] {} finished: {} edges found in {:.1f}s'.format(name, len(edges), elapsed))
        return edges

    result = []

    # Run edge checkers concurrently — each checker is independent
    max_workers = min(len(checker_objs), 5) if checker_objs else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_checker, nc): nc[0] for nc in checker_objs}
        for future in as_completed(futures):
            service_name = futures[future]
            try:
                edges = future.result()
                result.extend(edges)
            except Exception as ex:
                logger.warning('[Edge Check] {} encountered an error: {}. Continuing.'.format(service_name, ex))
                logger.debug('Exception details:', exc_info=True)

    logger.info('[Edge Check] Total edges identified: {}'.format(len(result)))
    return result
