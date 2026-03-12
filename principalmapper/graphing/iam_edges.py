"""Code to identify if a principal in an AWS account can use access to IAM to access other principals."""


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

import io
import logging
import os
from typing import List, Optional

from principalmapper.common import Edge, Node
from principalmapper.graphing.edge_checker import EdgeChecker
from principalmapper.querying import query_interface
from principalmapper.util import arns


logger = logging.getLogger(__name__)


class IAMEdgeChecker(EdgeChecker):
    """Class for identifying if IAM can be used by IAM principals to gain access to other IAM principals."""

    def return_edges(self, nodes: List[Node], region_allow_list: Optional[List[str]] = None,
                     region_deny_list: Optional[List[str]] = None, scps: Optional[List[List[dict]]] = None,
                     client_args_map: Optional[dict] = None) -> List[Edge]:
        """Fulfills expected method return_edges."""

        logger.info('Generating Edges based on IAM')
        result = generate_edges_locally(nodes, scps)

        for edge in result:
            logger.info("Found new edge: {}\n".format(edge.describe_edge()))

        return result


def generate_edges_locally(nodes: List[Node], scps: Optional[List[List[dict]]] = None) -> List[Edge]:
    """Generates and returns Edge objects. It is possible to use this method if you are operating offline (infra-as-code).
    """
    result = []

    for node_source in nodes:
        for node_destination in nodes:
            # skip self-access checks
            if node_source == node_destination:
                continue

            # check if source is an admin, if so it can access destination but this is not tracked via an Edge
            if node_source.is_admin:
                continue

            if ':user/' in node_destination.arn:
                # Change the user's access keys
                access_keys_mfa = False

                create_auth_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                    node_source,
                    'iam:CreateAccessKey',
                    node_destination.arn,
                    {},
                    service_control_policy_groups=scps
                )

                if mfa_res:
                    access_keys_mfa = True

                if node_destination.access_keys == 2:
                    # can have a max of two access keys, need to delete before making a new one
                    auth_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                        node_source,
                        'iam:DeleteAccessKey',
                        node_destination.arn,
                        {},
                        service_control_policy_groups=scps
                    )
                    if not auth_res:
                        create_auth_res = False  # can't delete target access key, can't generate a new one
                    if mfa_res:
                        access_keys_mfa = True

                if create_auth_res:
                    reason = 'can create access keys to authenticate as'
                    if access_keys_mfa:
                        reason = '(MFA required) ' + reason

                    target_user_name = arns.get_resource(node_destination.arn).split('/')[-1]
                    exploit_cmds = [
                        f'aws iam create-access-key --user-name {target_user_name} --profile attacker'
                    ]

                    result.append(
                        Edge(
                            node_source, node_destination, reason, 'IAM', exploit_cmds
                        )
                    )

                # Change the user's password
                if node_destination.active_password:
                    pass_auth_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                        node_source,
                        'iam:UpdateLoginProfile',
                        node_destination.arn,
                        {},
                        service_control_policy_groups=scps
                    )
                else:
                    pass_auth_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                        node_source,
                        'iam:CreateLoginProfile',
                        node_destination.arn,
                        {},
                        service_control_policy_groups=scps
                    )
                if pass_auth_res:
                    reason = 'can set the password to authenticate as'
                    if mfa_res:
                        reason = '(MFA required) ' + reason
                    
                    target_user_name = arns.get_resource(node_destination.arn).split('/')[-1]
                    exploit_cmds = [
                        f'aws iam update-login-profile --user-name {target_user_name} --password <new-password> --profile attacker'
                    ] if node_destination.active_password else [
                        f'aws iam create-login-profile --user-name {target_user_name} --password <new-password> --profile attacker'
                    ]

                    result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))

                # Check PutUserPolicy
                put_user_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                    node_source, 'iam:PutUserPolicy', node_destination.arn, {}, service_control_policy_groups=scps
                )
                if put_user_res:
                    reason = 'can add inline policies to'
                    if mfa_res: reason = '(MFA required) ' + reason
                    target_user_name = arns.get_resource(node_destination.arn).split('/')[-1]
                    exploit_cmds = [
                        f'aws iam put-user-policy --user-name {target_user_name} --policy-name pmapper-privesc --policy-document file://admin-policy.json --profile attacker'
                    ]
                    result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))

                # Check AttachUserPolicy
                attach_user_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                    node_source, 'iam:AttachUserPolicy', node_destination.arn, 
                    {'iam:PolicyARN': 'arn:aws:iam::aws:policy/AdministratorAccess'}, service_control_policy_groups=scps
                )
                if attach_user_res:
                    reason = 'can attach managed policies to'
                    if mfa_res: reason = '(MFA required) ' + reason
                    target_user_name = arns.get_resource(node_destination.arn).split('/')[-1]
                    exploit_cmds = [
                        f'aws iam attach-user-policy --user-name {target_user_name} --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile attacker'
                    ]
                    result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))

                # Check Group escalations
                for group in node_destination.group_memberships:
                    # PutGroupPolicy
                    put_group_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                        node_source, 'iam:PutGroupPolicy', group.arn, {}, service_control_policy_groups=scps
                    )
                    if put_group_res:
                        reason = f'can add inline policies to the group ({group.arn}) which contains'
                        if mfa_res: reason = '(MFA required) ' + reason
                        group_name = arns.get_resource(group.arn).split('/')[-1]
                        exploit_cmds = [
                            f'aws iam put-group-policy --group-name {group_name} --policy-name pmapper-privesc --policy-document file://admin-policy.json --profile attacker'
                        ]
                        result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))
                        break # Only need one group to escalate

                    # AttachGroupPolicy
                    attach_group_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                        node_source, 'iam:AttachGroupPolicy', group.arn, 
                        {'iam:PolicyARN': 'arn:aws:iam::aws:policy/AdministratorAccess'}, service_control_policy_groups=scps
                    )
                    if attach_group_res:
                        reason = f'can attach managed policies to the group ({group.arn}) which contains'
                        if mfa_res: reason = '(MFA required) ' + reason
                        group_name = arns.get_resource(group.arn).split('/')[-1]
                        exploit_cmds = [
                            f'aws iam attach-group-policy --group-name {group_name} --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile attacker'
                        ]
                        result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))
                        break # Only need one group to escalate

            if ':role/' in node_destination.arn:
                # Change the role's trust doc
                update_role_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                    node_source,
                    'iam:UpdateAssumeRolePolicy',
                    node_destination.arn,
                    {},
                    service_control_policy_groups=scps
                )
                if update_role_res:
                    reason = 'can update the trust document to access'
                    if mfa_res:
                        reason = '(MFA required) ' + reason
                    target_role_name = arns.get_resource(node_destination.arn).split('/')[-1]
                    source_arn = node_source.arn
                    exploit_cmds = [
                        'echo \'{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"AWS": "' + source_arn + '"},"Action": "sts:AssumeRole"}]}\' > new-trust-policy.json',
                        f'aws iam update-assume-role-policy --role-name {target_role_name} --policy-document file://new-trust-policy.json --profile attacker',
                        f'aws sts assume-role --role-arn {node_destination.arn} --role-session-name pmapper-privesc --profile attacker'
                    ]
                    result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))

                # Check PutRolePolicy
                put_role_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                    node_source, 'iam:PutRolePolicy', node_destination.arn, {}, service_control_policy_groups=scps
                )
                if put_role_res:
                    reason = 'can add inline policies to'
                    if mfa_res: reason = '(MFA required) ' + reason
                    target_role_name = arns.get_resource(node_destination.arn).split('/')[-1]
                    exploit_cmds = [
                        f'aws iam put-role-policy --role-name {target_role_name} --policy-name pmapper-privesc --policy-document file://admin-policy.json --profile attacker',
                        f'aws sts assume-role --role-arn {node_destination.arn} --role-session-name pmapper-privesc --profile attacker'
                    ]
                    result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))

                # Check AttachRolePolicy
                attach_role_res, mfa_res = query_interface.local_check_authorization_handling_mfa(
                    node_source, 'iam:AttachRolePolicy', node_destination.arn, 
                    {'iam:PolicyARN': 'arn:aws:iam::aws:policy/AdministratorAccess'}, service_control_policy_groups=scps
                )
                if attach_role_res:
                    reason = 'can attach managed policies to'
                    if mfa_res: reason = '(MFA required) ' + reason
                    target_role_name = arns.get_resource(node_destination.arn).split('/')[-1]
                    exploit_cmds = [
                        f'aws iam attach-role-policy --role-name {target_role_name} --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile attacker',
                        f'aws sts assume-role --role-arn {node_destination.arn} --role-session-name pmapper-privesc --profile attacker'
                    ]
                    result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))

            # Check CreatePolicyVersion / SetDefaultPolicyVersion on attached managed policies
            # We must check policies attached to the destination node AND policies attached to its groups
            attached_policies = list(node_destination.attached_policies)
            for group in node_destination.group_memberships:
                attached_policies.extend(group.attached_policies)
            
            for policy in attached_policies:
                # AWS managed policies cannot be edited by customers
                if policy.arn.startswith('arn:aws:iam::aws:policy/'):
                    continue
                
                # Check both permissions on the policy ARN
                create_policy_res, mfa_res1 = query_interface.local_check_authorization_handling_mfa(
                    node_source, 'iam:CreatePolicyVersion', policy.arn, {}, service_control_policy_groups=scps
                )
                if not create_policy_res:
                    continue
                    
                set_default_res, mfa_res2 = query_interface.local_check_authorization_handling_mfa(
                    node_source, 'iam:SetDefaultPolicyVersion', policy.arn, {}, service_control_policy_groups=scps
                )
                if set_default_res:
                    reason = f'can create a new default policy version for ({policy.arn}) which is attached to'
                    mfa_required = mfa_res1 or mfa_res2
                    if mfa_required: reason = '(MFA required) ' + reason
                    
                    exploit_cmds = [
                        f'aws iam create-policy-version --policy-arn {policy.arn} --policy-document file://admin-policy.json --set-as-default --profile attacker'
                    ]
                    result.append(Edge(node_source, node_destination, reason, 'IAM', exploit_cmds))
                    break # We only need one exploitable policy to establish the edge

    return result
