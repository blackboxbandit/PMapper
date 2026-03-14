# Graph Commands

The `graph` subcommand is used to create, inspect, and manage the IAM permission graphs that power all PMapper analysis.

---

## `pmapper graph create`

Creates a new graph by pulling IAM data from a live AWS account. This is always the **first step** when using PMapper.

### Basic Usage

```bash
pmapper --profile my-profile graph create
```

This will:
1. Authenticate using the specified AWS profile
2. Enumerate all IAM Users, Roles, Groups, and Policies
3. Identify privilege escalation edges across enabled services
4. Store the graph locally at `~/.local/share/principalmapper/<account-id>/`

### Filtering by Region

Some edge checks (e.g., Lambda, EC2, SSM) enumerate resources in specific regions. You can control which regions are scanned:

```bash
# Only scan US regions
pmapper --profile my-profile graph create --include-regions us-east-1 us-east-2 us-west-1 us-west-2

# Skip China regions
pmapper --profile my-profile graph create --exclude-regions cn-north-1 cn-northwest-1
```

> **Note:** `--include-regions` and `--exclude-regions` are mutually exclusive. The `global` region is always included.

### Filtering by Service

Control which edge-checking modules run. Useful for faster scans or when you lack permissions for certain services:

```bash
# Only check IAM and STS edges (fastest scan)
pmapper --profile my-profile graph create --include-services iam sts

# Skip slow services
pmapper --profile my-profile graph create --exclude-services sagemaker autoscaling
```

**Available edge-checking services:**

| Service | Checks For |
|---------|------------|
| `autoscaling` | Auto Scaling launch configurations that can pass roles to EC2 instances |
| `cloudformation` | CloudFormation stacks that create/modify IAM resources |
| `codebuild` | CodeBuild projects with attached service roles |
| `ec2` | EC2 instances with instance profiles (IAM roles) |
| `generic_passrole` | Generic `iam:PassRole` permissions to any service |
| `iam` | Direct IAM policy modifications (attach, put, create) |
| `lambda` | Lambda functions with execution roles |
| `sagemaker` | SageMaker notebooks and training jobs with roles |
| `ssm` | SSM documents and command execution on managed instances |
| `sts` | `sts:AssumeRole` trust policy relationships |

### Organizations / SCP Integration

By default, `graph create` checks for locally stored Organizations data and applies any applicable SCPs:

```bash
# Skip Organizations/SCP checks
pmapper --profile my-profile graph create --ignore-orgs
```

### LocalStack Testing

For local development and testing with [LocalStack](https://localstack.cloud/):

```bash
pmapper --profile my-profile graph create --localstack-endpoint http://localhost:4566
```

### All Flags

| Flag | Description |
|------|-------------|
| `--ignore-orgs` | Skip AWS Organizations SCP checks |
| `--localstack-endpoint URL` | LocalStack HTTP(S) endpoint |
| `--include-regions REGION [...]` | Allow-list of regions |
| `--exclude-regions REGION [...]` | Deny-list of regions |
| `--include-services SERVICE [...]` | Allow-list of edge services |
| `--exclude-services SERVICE [...]` | Deny-list of edge services |

---

## `pmapper graph display`

Displays summary information about a stored graph:

```bash
# Using live credentials to identify the account
pmapper --profile my-profile graph display

# Using a stored account ID (offline)
pmapper --account 123456789012 graph display
```

**Example output:**
```
Graph Data for Account 123456789012
  33 IAM Users
  47 IAM Roles
  12 IAM Groups
  89 Managed Policies
  142 Edges
```

---

## `pmapper graph list`

Lists all account graphs stored on the local machine:

```bash
pmapper graph list
```

**Example output:**
```
Account IDs:
---
123456789012 (PMapper Version 1.2.0)
987654321098 (PMapper Version 1.2.0)
```

### Storage Location

Graphs are stored at:
- **Linux**: `~/.local/share/principalmapper/`
- **macOS**: `~/Library/Application Support/principalmapper/`
- **Windows**: `%APPDATA%\principalmapper\`

Each account gets a subdirectory named by its 12-digit account ID.

---

[← Command Reference](Command-Reference) | [Query Commands →](Query-Commands)
