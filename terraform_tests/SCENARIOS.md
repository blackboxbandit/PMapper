# PMapper Test Environment — Scenario Reference

Terraform-based test environment for PMapper privilege escalation detection. Each scenario creates IAM resources that represent a known privesc path PMapper can identify.

## Quick Start

```bash
# List all scenarios
python3 pmapper_test_env.py list

# Deploy all SageMaker scenarios
python3 pmapper_test_env.py create --group sagemaker

# Deploy a single scenario
python3 pmapper_test_env.py create --issue 5.2

# Deploy everything
python3 pmapper_test_env.py create --all

# Check what's deployed
python3 pmapper_test_env.py status

# Tear down
python3 pmapper_test_env.py destroy
```

After deploying, run PMapper:
```bash
pmapper graph --create
pmapper analysis
```

---

## Section 1: IAM — Direct IAM Privilege Escalation

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 1.1 | CreateAccessKey | `iam:CreateAccessKey` on User B | "can create access keys to authenticate as" |
| 1.2 | UpdateLoginProfile | `iam:UpdateLoginProfile` on User B | "can set the password to authenticate as" |
| 1.3 | PutUserPolicy | `iam:PutUserPolicy` on User B | "can add inline policies to" |
| 1.4 | AttachUserPolicy | `iam:AttachUserPolicy` on User B | "can attach managed policies to" |
| 1.5 | PutGroupPolicy | `iam:PutGroupPolicy` on Group containing User B | "can add inline policies to the group which contains" |
| 1.6 | AttachGroupPolicy | `iam:AttachGroupPolicy` on Group containing User B | "can attach managed policies to the group which contains" |
| 1.7 | UpdateAssumeRolePolicy | `iam:UpdateAssumeRolePolicy` on Role B | "can update the trust document to access" |
| 1.8 | PutRolePolicy | `iam:PutRolePolicy` on Role B | "can add inline policies to" |
| 1.9 | AttachRolePolicy | `iam:AttachRolePolicy` on Role B | "can attach managed policies to" |

---

## Section 2: STS — AssumeRole Escalation

| ID  | Scenario | Setup | Expected PMapper Edge |
|-----|----------|-------|-----------------------|
| 2.1 | AssumeRole (identity policy) | User A has `sts:AssumeRole`; Role B trusts User A | "can access via sts:AssumeRole" |
| 2.2 | AssumeRole (NODE_MATCH) | Role B trusts account root; User A has no explicit AssumeRole | "can access via sts:AssumeRole" |

---

## Section 3: EC2 — PassRole to EC2

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 3.1 | RunInstances + existing IP | `ec2:RunInstances` + `iam:PassRole`; Role B has instance profile | "can use EC2 to run an instance with an existing instance profile to access" |
| 3.2 | RunInstances + new IP | `ec2:RunInstances` + `ec2:AssociateIamInstanceProfile` + `iam:PassRole` + `iam:CreateInstanceProfile` + `iam:AddRoleToInstanceProfile` | "can use EC2 to run an instance with a newly created instance profile to access" |

---

## Section 4: Lambda — PassRole to Lambda

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 4.1 | CreateFunction + PassRole | `lambda:CreateFunction` + `lambda:InvokeFunction` + `iam:PassRole` | "can use Lambda to create a new function with arbitrary code, then pass and access" |
| 4.2 | UpdateFunctionCode | `lambda:UpdateFunctionCode` + `lambda:InvokeFunction` | "can use Lambda to edit an existing function to access" |

---

## Section 5: SageMaker — PassRole to SageMaker

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 5.1 | CreateNotebookInstance | `sagemaker:CreateNotebookInstance` + `iam:PassRole` | "can use SageMaker to launch a notebook and access" |
| 5.2 | CreateTrainingJob | `sagemaker:CreateTrainingJob` + `iam:PassRole` | "can use SageMaker to create a training job and access" |
| 5.3 | CreateProcessingJob | `sagemaker:CreateProcessingJob` + `iam:PassRole` | "can use SageMaker to create a processing job and access" |

---

## Section 6: SSM — SendCommand / StartSession

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 6.1 | SendCommand | `ssm:SendCommand`; Role B trusts EC2 with instance profile + `ssmmessages:CreateControlChannel` | "can call ssm:SendCommand to access an EC2 instance with access to" |
| 6.2 | StartSession | `ssm:StartSession`; same target setup as 6.1 | "can call ssm:StartSession to access an EC2 instance with access to" |

---

## Section 7: CodeBuild — PassRole to CodeBuild

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 7.1 | CreateProject + StartBuild | `codebuild:CreateProject` + `codebuild:StartBuild` + `iam:PassRole` | "can create a project in CodeBuild to access" |
| 7.2 | UpdateProject + StartBuild | `codebuild:UpdateProject` + `codebuild:StartBuild` + `iam:PassRole` | "can update a project in CodeBuild to access" |

---

## Section 8: CloudFormation — PassRole to CloudFormation

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 8.1 | CreateStack | `cloudformation:CreateStack` + `iam:PassRole` | "can create a stack in CloudFormation to access" |
| 8.2 | UpdateStack | `cloudformation:UpdateStack` + `iam:PassRole` | "can update the CloudFormation stack to access" |

---

## Section 9: AutoScaling — PassRole to EC2 Auto Scaling

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 9.1 | Existing LaunchConfig | `autoscaling:CreateAutoScalingGroup` + `iam:CreateServiceLinkedRole`; existing launch config uses target role's IP | "can use the EC2 Auto Scaling service role and an existing Launch Configuration to access" |
| 9.2 | New LaunchConfig | `autoscaling:CreateLaunchConfiguration` + `autoscaling:CreateAutoScalingGroup` + `iam:PassRole` | "can use the EC2 Auto Scaling service role and create a launch configuration to access" |

---

## Section 10: Glue — PassRole to AWS Glue

| ID  | Scenario | Attacker Permissions | Expected PMapper Edge |
|-----|----------|---------------------|-----------------------|
| 10.1 | CreateDevEndpoint | `glue:CreateDevEndpoint` + `iam:PassRole` | "can execute glue:CreateDevEndpoint and pass the role to glue.amazonaws.com" |
| 10.2 | UpdateDevEndpoint | `glue:UpdateDevEndpoint` + `iam:PassRole` | "can execute glue:UpdateDevEndpoint and pass the role to glue.amazonaws.com" |

---

## Resource Naming Convention

All resources use the prefix `pmapper-test-` (configurable via `--name-prefix`):

- **Attacker users**: `pmapper-test-<group>-<section>-<scenario>-attacker`
- **Target roles/users**: `pmapper-test-<group>-target-role` / `pmapper-test-<group>-target-user`
- **Instance profiles**: `pmapper-test-<group>-target-ip`
- **Groups**: `pmapper-test-<group>-target-group`

## Cleanup

Always destroy resources after testing:

```bash
python3 pmapper_test_env.py destroy
```

If the wrapper fails, use Terraform directly:
```bash
cd terraform_tests
terraform destroy -auto-approve
```
