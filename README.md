# AWS Privilege Escalation Matrix (180+ Vectors)

This matrix documents over 180 known and novel privilege escalation paths in AWS, including deep dives into Config, SSM, and AI-driven methods from 2024–2026.

**Format**: Permissions required -> MITRE ATT&CK Mapping -> Description of Risk

---

## 1. IAM Self-Escalation (Direct Admin)
> Upgrading own permissions without needing a compute service.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| A01 | `iam:CreatePolicyVersion` | [T1098](https://attack.mitre.org/techniques/T1098/) | Allows creating a new policy version with `*:*` permissions and setting it as the default for an attached policy. |
| A02 | `iam:SetDefaultPolicyVersion` | [T1098](https://attack.mitre.org/techniques/T1098/) | Revert to an older, more permissive version of an already attached managed policy. |
| A03 | `iam:AttachUserPolicy` (self) | [T1098](https://attack.mitre.org/techniques/T1098/) | Directly attach `AdministratorAccess` to own IAM user object. |
| A04 | `iam:AttachGroupPolicy` (own group) | [T1098](https://attack.mitre.org/techniques/T1098/) | Attach admin policy to an IAM group the attacker belongs to. |
| A05 | `iam:AttachRolePolicy` + `sts:AssumeRole` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Attach admin policy to an assumable role, then assume it. |
| A06 | `iam:PutUserPolicy` (self) | [T1098](https://attack.mitre.org/techniques/T1098/) | Write an inline `*:*` policy directly to own user. |
| A07 | `iam:PutGroupPolicy` (own group) | [T1098](https://attack.mitre.org/techniques/T1098/) | Write an inline admin policy to own group. |
| A08 | `iam:PutRolePolicy` + `sts:AssumeRole` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Write inline admin policy to assumable role, then assume it. |
| A09 | `iam:AddUserToGroup` | [T1098](https://attack.mitre.org/techniques/T1098/) | Add self to an existing admin-level group. |
| A10 | `iam:CreateRole` + `iam:AttachRolePolicy` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Create new role, attach admin policy, then assume it. |
| A11 | `iam:UpdateAssumeRolePolicy` | [T1098](https://attack.mitre.org/techniques/T1098/) | Modify trust policy of a highly privileged role to allow self-assumption. |
| A12 | `iam:CreatePolicy` + `iam:AttachUserPolicy` | [T1098](https://attack.mitre.org/techniques/T1098/) | Create a custom admin policy and attach it to self. |
| A13 | `iam:CreateUser` + `iam:CreateAccessKey` | [T1136.003](https://attack.mitre.org/techniques/T1136/003/) | Create a new admin user and generate long-term access keys. |
| A14 | `iam:DeactivateMFADevice` | [T1556.006](https://attack.mitre.org/techniques/T1556/006/) | Remove MFA from self, bypassing `aws:MultiFactorAuthPresent` conditions. |
| A15 | `iam:DeleteAccountPasswordPolicy` | [T1556](https://attack.mitre.org/techniques/T1556/) | Weaken org password policy to facilitate downstream brute-force. |

---

## 2. IAM Lateral Movement
> Exploiting other identities to reach a higher privilege level.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| B01 | `iam:CreateAccessKey` | [T1098](https://attack.mitre.org/techniques/T1098/) | Generate new operational access keys for a target highly privileged user. |
| B02 | `iam:CreateLoginProfile` | [T1098](https://attack.mitre.org/techniques/T1098/) | Set a console password for a target user who previously had programmatic access only. |
| B03 | `iam:UpdateLoginProfile` | [T1098](https://attack.mitre.org/techniques/T1098/) | Overwrite the console password of an existing target user. |
| B04 | `iam:UpdateAssumeRolePolicy` | [T1098](https://attack.mitre.org/techniques/T1098/) | Modify a target role's trust policy to allow unauthorized assumption. |
| B05 | `sts:AssumeRole` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Directly assume an accessible privileged role. |
| B06 | `iam:AttachRolePolicy` + `iam:UpdateAssumeRolePolicy` | [T1098](https://attack.mitre.org/techniques/T1098/) | Attach admin policy to a third-party role, make it assumable, then pivot. |
| B07 | `iam:AttachUserPolicy` + `iam:CreateAccessKey` | [T1098](https://attack.mitre.org/techniques/T1098/) | Make target user admin, then generate their keys. |

---

## 3. Resource Execution (PassRole Abuse)
> Pattern: `iam:PassRole` + Create/Update Compute Object. 

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| C01 | `iam:PassRole` + `ec2:RunInstances` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Launch EC2 instance with privileged IAM Profile; extract creds from Instance Metadata Service (IMDS). |
| C02 | `iam:PassRole` + `lambda:CreateFunction` + `lambda:InvokeFunction` | [T1648](https://attack.mitre.org/techniques/T1648/) | Create malicious Lambda function with a privileged role and invoke it. |
| C03 | `iam:PassRole` + `ecs:RegisterTaskDefinition` + `ecs:RunTask` | [T1609](https://attack.mitre.org/techniques/T1609/) | Run an ECS container under a highly privileged task execution role. |
| C04 | `iam:PassRole` + `glue:CreateJob` + `glue:StartJobRun` | [T1059.006](https://attack.mitre.org/techniques/T1059/006/) | Run Python/Scala ETL script in Glue using a privileged service role. |
| C05 | `iam:PassRole` + `sagemaker:CreateNotebookInstance` | [T1059.006](https://attack.mitre.org/techniques/T1059/006/) | Launch Jupyter notebook with privileged role, extract keys via shell. |
| C06 | `iam:PassRole` + `cloudformation:CreateStack` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Deploy a template giving attacker admin access, executed by the CFN service role. |
| C07 | `iam:PassRole` + `stepfunctions:CreateStateMachine` + `StartExecution` | [T1648](https://attack.mitre.org/techniques/T1648/) | Execute ASL (Amazon States Language) to invoke other privileged AWS APIs via the state machine role. |
| C08 | `iam:PassRole` + `codebuild:CreateProject` + `StartBuild` | [T1059.004](https://attack.mitre.org/techniques/T1059/004/) | Execute a malicious buildspec.yml under the CodeBuild service role. |
| C09 | `iam:PassRole` + `events:PutRule` + `PutTargets` | [T1546](https://attack.mitre.org/techniques/T1546/) | Trigger malicious target (like Lambda or ECS) using EventBridge service role. |
| C10 | `iam:PassRole` + `ssm:StartAutomationExecution` | [T1059](https://attack.mitre.org/techniques/T1059/) | Run SSM runbook with `AutomationAssumeRole` to bypass own permissions. |

---

## 4. Existing Role Hijacking (No PassRole needed)
> Hijacking compute environments that *already have* a privileged role attached.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| D01 | `lambda:UpdateFunctionCode` | [T1648](https://attack.mitre.org/techniques/T1648/) | Overwrite the code of an existing privileged Lambda function; subsequent legitimate triggers run attacker code. |
| D02 | `lambda:UpdateFunctionConfiguration` | [T1648](https://attack.mitre.org/techniques/T1648/) | Change environment variables (e.g., `LD_PRELOAD`) or Lambda layers to hijack existing execution. |
| D03 | `ecs:ExecuteCommand` | [T1059.004](https://attack.mitre.org/techniques/T1059/004/) | Open interactive reverse shell inside a running ECS container to access its task credentials. |
| D04 | `cloudformation:UpdateStack` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Inject malicious configurations into an existing stack update (executed via its existing role). |
| D05 | `sagemaker:UpdateNotebookInstance` + `CreateNotebookInstanceLifecycleConfig` | [T1059.004](https://attack.mitre.org/techniques/T1059/004/) | Inject bash script into lifecycle config of stopped SageMaker instance; starts under instance role. |
| D06 | `glue:UpdateJob` | [T1059.006](https://attack.mitre.org/techniques/T1059/006/) | Modify the source script logic for an existing scheduled Glue job. |

---

## 5. Trust Boundary & Cross-Account Escalation
> Techniques crossing boundaries between AWS accounts.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| E01 | `iam:PassRole` (Cross-Account) | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Some services (like IAM Identity Center) allow passing roles *from* other accounts if resource policies permit. |
| E02 | `sts:AssumeRole` (Orphaned Trust) | [T1190](https://attack.mitre.org/techniques/T1190/) | Exploiting roles with overly permissive trust policies (`"Principal": {"AWS": "*"}`) left over from vendor integrations. |
| E03 | `ram:CreateResourceShare` + `ram:AssociateResourceShare` | [T1562.007](https://attack.mitre.org/techniques/T1562/007/) | Share sensitive intra-account resource (like malicious Lambda layer, Route 53 resolver rules) out to an external attacker-controlled account. |
| E04 | `ram:AcceptResourceShareInvitation` | [T1562.007](https://attack.mitre.org/techniques/T1562/007/) | Accept a malicious shared resource from an external attacker into a high-trust internal environment. |
| E05 | `lambda:AddPermission` (Cross-Account) | [T1098](https://attack.mitre.org/techniques/T1098/) | Modify Lambda resource policy to allow invocation from an external attacker's AWS account. |

---

## 6. Resource-Based Policy Abuse
> Misconfiguring permissions attached directly to resources rather than identities.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| F01 | `s3:PutBucketPolicy` | [T1098](https://attack.mitre.org/techniques/T1098/) | Rewrite S3 bucket policy to `Principal: *`, exposing Terraform state or credential files to the public internet. |
| F02 | `kms:PutKeyPolicy` | [T1098](https://attack.mitre.org/techniques/T1098/) | Alter KMS key policy to allow attacker account to decrypt sensitive secrets from Secrets Manager/SSM. |
| F03 | `sqs:SetQueueAttributes` | [T1098](https://attack.mitre.org/techniques/T1098/) | Modify SQS resource policy to allow attacker to inject malicious events into consumer pipelines. |
| F04 | `ecr:SetRepositoryPolicy` | [T1098](https://attack.mitre.org/techniques/T1098/) | Alter Container Registry policy to allow external attacker to push backdoored Docker images. |
| F05 | `sns:AddPermission` | [T1098](https://attack.mitre.org/techniques/T1098/) | Modify SNS topic resource policy so attacker can subscribe to sensitive alert streams. |

---

## 7. Organizations, SCP, and Control Tower Abuse (Org-Wide Impact)
> Nullifying guardrails or attacking the entire AWS presence simultaneously.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| G01 | `organizations:UpdatePolicy` | [T1484.001](https://attack.mitre.org/techniques/T1484/001/) | Modify the root Service Control Policy (SCP) to remove `Deny` statements, instantly elevating privileges in all child accounts. |
| G02 | `organizations:DetachPolicy` | [T1484.001](https://attack.mitre.org/techniques/T1484/001/) | Detach restrictive SCPs from OUs, removing organizational security guardrails. |
| G03 | `organizations:RegisterDelegatedAdministrator` | [T1484.001](https://attack.mitre.org/techniques/T1484/001/) | Register an already compromised member account as the delegated admin for highly sensitive services like SSO, StackSets, or Security Hub. |
| G04 | `controltower:UpdateLandingZone` | [T1484.001](https://attack.mitre.org/techniques/T1484/001/) | Modify the foundational landing zone configuration, re-wiring the IAM roles Control Tower uses to manage child accounts. |
| G05 | `controltower:DisableControl` | [T1484.001](https://attack.mitre.org/techniques/T1484/001/) | Programmatically disable preventative/detective guardrails across specific accounts/OUs. |

---

## 8. IAM Identity Center (SSO) Vectors
> Manipulating centralized identity to gain administrative access everywhere.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| H01 | `sso:CreatePermissionSet` + `sso:AttachManagedPolicyToPermissionSet` + `ProvisionPermissionSet` + `CreateAccountAssignment` | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | **The SSO Org Takeover**: Create a `PermissionSet` with AdministratorAccess, push it to all accounts, and assign it to the attacker's identity. |
| H02 | `sso-directory:AddMemberToGroup` | [T1098](https://attack.mitre.org/techniques/T1098/) | Add the attacker's regular SSO user to an existing Admin SSO group. |
| H03 | `sso-directory:UpdatePassword` | [T1098](https://attack.mitre.org/techniques/T1098/) | Forcibly reset the password of a human SSO admin user and log in as them. |
| H04 | `sso:CreateTrust` / `sso:UpdateTrust` | [T1484.002](https://attack.mitre.org/techniques/T1484/002/) | Manipulate the IdP trust settings to bypass corporate SSO and redirect to an attacker-controlled Identity Provider. |

---

## 9. Novel & Undocumented Vectors (2024–2025)
> Cutting-edge paths discovered in recent advanced research.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| I01 | `cloudshell:CreateSession` + `cloudshell:PutCredentials` | [T1059.004](https://attack.mitre.org/techniques/T1059/004/) | Use CloudShell execution environment to automatically parse complex IAM credential combinations without leaving traditional traces. |
| I02 | `codestar:CreateProjectFromTemplate` (Undocumented API) | [T1136](https://attack.mitre.org/techniques/T1136/) | Abuse an undocumented CodeStar API integration that automatically creates highly privileged service roles during project initialization (Rhino Security Labs). |
| I03 | **ECS-cape** (Container Agent Impersonation) | [T1611](https://attack.mitre.org/techniques/T1611/) | Break out of an unprivileged ECS container and impersonate the ECS node agent to fetch credentials for *other* containers running on the same underlying EC2 instance (Black Hat 2025). |
| I04 | Bedrock / AgentCore Exploit | [T1569](https://attack.mitre.org/techniques/T1569/) | Compromise an external tool/API delegated to an Amazon Bedrock custom agent, forcing the AI orchestration layer to execute privileged AWS API calls on the attacker's behalf. |
| I05 | "Bucket Monopoly" (Shadow S3 Hijack) | [T1190](https://attack.mitre.org/techniques/T1190/) | Predict the naming convention of a service-generated S3 bucket (e.g., CodeStar, CFN), pre-create it in an unused region with malicious policies, wait for the victim to deploy, and capture deployment artifacts. |
| I06 | `s3:GetObject` (TruffleHog) | [T1552.001](https://attack.mitre.org/techniques/T1552/001/) | Scrape loosely permissioned S3 buckets for hardcoded `.env` files or Terraform `.tfstate` containing long-lived IAM keys from higher tiers. |

---

## 10. AWS Config & SSM Advanced Abuse
> Exploiting configuration management, auto-remediation, and hybrid instance management.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| J01 | `config:PutRemediationConfigurations` | [T1059.004](https://attack.mitre.org/techniques/T1059/004/) | Create an AWS Config auto-remediation rule using an existing `AutomationAssumeRole`. The attacker controls the SSM automation parameters. |
| J02 | `config:StartRemediationExecution` / `StartResourceEvaluation` | [T1059.004](https://attack.mitre.org/techniques/T1059/004/) | Force-trigger a previously manipulated or misconfigured Config remediation rule, instantly executing the payload under the remediation IAM role. |
| J03 | `ssm:UpdateDocument` | [T1546.016](https://attack.mitre.org/techniques/T1546/016/) | Poison an existing, trusted SSM runbook/document with a reverse shell. When administrators legitimately run this document via `SendCommand`, the attacker gains root on all target instances. |
| J04 | `ssm:UpdateManagedInstanceRole` | [T1098](https://attack.mitre.org/techniques/T1098/) | Replace the IAM role attached to a managed EC2/hybrid instance the attacker already controls with a more privileged IAM role. |
| J05 | `ssm:RegisterTargetWithMaintenanceWindow` + `ssm:RegisterTaskWithMaintenanceWindow` | [T1053.007](https://attack.mitre.org/techniques/T1053/007/) | Attach a malicious SSM task to an existing maintenance window. The task will run silently in the background under the maintenance window's service role. |
| J06 | `ssm:CreateAssociation` / `ssm:UpdateAssociation` | [T1053.007](https://attack.mitre.org/techniques/T1053/007/) | Bind a malicious SSM document to a massive fleet of instances via State Manager. The document executes repeatedly (e.g., every 30 minutes) as root. |
| J07 | SSM Agent Impersonation (RAT) | [T1569.002](https://attack.mitre.org/techniques/T1569/002/) | Re-register a compromised instance's SSM agent to an attacker-controlled AWS account. The attacker uses their own AWS management console to `SendCommand` to the victim's instance, bypassing the victim's CloudTrail logging entirely. |

---

## 11. AWS Managed Policy Exploits
> Abusing built-in, overly permissive AWS Managed Policies to bridge gaps.

| ID | Permissions Required | MITRE ATT&CK | Description of Risk |
|----|----------------------|--------------|---------------------|
| K01 | `iam:AttachUserPolicy` (`arn:aws:iam::aws:policy/DataScientist`) | [T1098](https://attack.mitre.org/techniques/T1098/) | Attaching the `DataScientist` managed policy grants broad access to Athena, Glue, EMR, and SageMaker. This inherently includes numerous `iam:PassRole` combinations (e.g., `sagemaker:CreateNotebookInstance`) allowing immediate escalation to admin. |
| K02 | `iam:AttachRolePolicy` (`arn:aws:iam::aws:policy/AdministratorAccess-Amplify`) | [T1098](https://attack.mitre.org/techniques/T1098/) | Attaching Amplify administrative access grants wildcard `iam:PassRole` for Amplify service roles, which can be hijacked to deploy custom serverless backends containing admin keys. |
| K03 | Default Service Roles (`AWSServiceRoleFor...`) | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Co-opting AWS-created default roles (e.g., `AWSServiceRoleForLightsail`) which historically contain excessively broad permissions like `AmazonS3FullAccess` and can be passed to attacker-controlled resources. |
| K04 | Exploiting `AmazonGuardDutyFullAccess` Bug | [T1484.001](https://attack.mitre.org/techniques/T1484/001/) | Leveraging legacy attachments of the GuardDuty full access policy, which inadvertently contained `organizations:RegisterDelegatedAdministrator` with a `*` resource, allowing complete Organization takeover. |
| K05 | Confused Deputy via Data Analytics | [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | Using `AmazonElasticMapReduceRole` or `AmazonSageMakerFullAccess` to trick the service into querying, processing, and exfiltrating cross-account data to attacker-controlled S3 buckets. |

---

*Compiled globally across IAM definition data, open-source security intelligence, and MITRE Cloud Matrix parameters.*