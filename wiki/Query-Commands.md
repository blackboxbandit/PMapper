# Query Commands

PMapper provides two query interfaces: `query` (human-readable) and `argquery` (structured/scriptable). Both simulate AWS authorization locally using the stored graph.

---

## `pmapper query` — Human-Readable Queries

### Query Syntax

The `query` subcommand accepts natural-language-style queries in these forms:

| Pattern | Example |
|---------|---------|
| `who can do <action>` | `'who can do iam:CreateUser'` |
| `who can do <action> with <resource>` | `'who can do s3:GetObject with arn:aws:s3:::my-bucket/*'` |
| `can <principal> do <action>` | `'can arn:aws:iam::123456789012:user/dev do iam:CreateUser'` |
| `can <principal> do <action> with <resource>` | `'can arn:aws:iam::123456789012:role/lambda-role do s3:PutObject with arn:aws:s3:::logs/*'` |
| `preset <preset_name> <principal>` | `'preset privesc *'` |

### Examples

```bash
# Who can create IAM users?
pmapper --account 123456789012 query 'who can do iam:CreateUser'

# Can a specific user read from an S3 bucket?
pmapper --account 123456789012 query \
  'can arn:aws:iam::123456789012:user/attacker do s3:GetObject with arn:aws:s3:::secret-bucket/*'

# Find all privilege escalation paths (skip known admins)
pmapper --account 123456789012 query -s 'preset privesc *'

# Show who CANNOT perform an action
pmapper --account 123456789012 query -u 'who can do iam:CreateUser'
```

### Resource Policy Support

```bash
# Auto-fetch the resource policy from AWS (S3, IAM, SNS, SQS, KMS)
pmapper --profile my-profile query \
  --with-resource-policy \
  'who can do s3:GetObject with arn:aws:s3:::my-bucket/*'

# Provide resource policy inline
pmapper --account 123456789012 query \
  --resource-policy-text '{"Version":"2012-10-17","Statement":[...]}' \
  'who can do s3:GetObject with arn:aws:s3:::my-bucket/*'

# S3 requires specifying the resource owner
pmapper --profile my-profile query \
  --with-resource-policy \
  --resource-owner 123456789012 \
  'who can do s3:GetObject with arn:aws:s3:::my-bucket/*'
```

### SCP Support

```bash
# Apply stored SCPs (requires prior `pmapper orgs create/update`)
pmapper --account 123456789012 query --scps 'who can do iam:CreateUser'
```

### All Flags

| Flag | Description |
|------|-------------|
| `-s`, `--skip-admin` | Omit admin-level principals from results |
| `-u`, `--include-unauthorized` | Include principals that do NOT have access |
| `--with-resource-policy` | Auto-fetch the resource policy (live AWS call) |
| `--resource-policy-text TEXT` | Inline resource policy JSON |
| `--resource-owner ACCOUNT_ID` | Resource owner account ID (required for S3) |
| `--session-policy TEXT` | Session policy JSON to evaluate |
| `--scps` | Apply stored SCPs during evaluation |

---

## `pmapper argquery` — Structured Queries

The `argquery` subcommand provides a structured, flag-based interface that's easier to script and automate.

### Basic Usage

```bash
# Who can run EC2 instances?
pmapper --account 123456789012 argquery -s --action 'ec2:RunInstances'

# Check a specific principal
pmapper --account 123456789012 argquery \
  --principal 'arn:aws:iam::123456789012:user/dev' \
  --action 's3:GetObject' \
  --resource 'arn:aws:s3:::prod-data/*'
```

### Using Conditions

Conditions let you test specific scenarios (e.g., instance types, source IPs):

```bash
# Who can launch expensive EC2 instances?
pmapper --account 123456789012 argquery -s \
  --action 'ec2:RunInstances' \
  --condition 'ec2:InstanceType=c6gd.16xlarge'

# Multiple conditions
pmapper --account 123456789012 argquery -s \
  --action 'ec2:RunInstances' \
  --condition 'ec2:InstanceType=c6gd.16xlarge' \
  --condition 'aws:RequestedRegion=us-east-1'
```

### Preset Queries

```bash
# Privilege escalation check
pmapper --account 123456789012 argquery --preset privesc

# With admin principals skipped
pmapper --account 123456789012 argquery -s --preset privesc
```

### Exploit Generation

The `--exploit` flag outputs the exact AWS CLI commands needed to execute an identified attack path:

```bash
pmapper --account 123456789012 argquery -s --preset privesc --exploit
```

**Example output:**
```
[!] user/attacker can mass-escalate via iam:AttachUserPolicy to become admin
    Exploit:
    aws iam attach-user-policy --user-name attacker --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

### All Flags

| Flag | Description |
|------|-------------|
| `--principal PRINCIPAL` | IAM principal ARN or `*` for all (default: `*`) |
| `--action ACTION` | AWS API action (e.g., `s3:GetObject`). Required if `--preset` not set |
| `--resource RESOURCE` | Resource ARN (default: `*`) |
| `--condition KEY=VALUE` | Condition pair (repeatable for multiple conditions) |
| `--preset PRESET` | Preset query name (e.g., `privesc`) |
| `--exploit` | Generate AWS CLI exploit commands |
| `-s`, `--skip-admin` | Skip admin-level principals |
| `-u`, `--include-unauthorized` | Show unauthorized principals |
| `--with-resource-policy` | Auto-fetch resource policy |
| `--resource-policy-text TEXT` | Inline resource policy JSON |
| `--resource-owner ACCOUNT_ID` | Resource owner for S3 |
| `--session-policy TEXT` | Session policy JSON |
| `--scps` | Apply stored SCPs |

---

## `query` vs `argquery`: When to Use Which

| Scenario | Use |
|----------|-----|
| Quick ad-hoc investigation | `query` |
| Shell scripts and automation | `argquery` |
| Testing with conditions | `argquery` |
| Preset queries (privesc) | Either (both support presets) |
| Generating exploit commands | `argquery` (has `--exploit` flag) |
| Complex queries with multiple flags | `argquery` |

---

[← Graph Commands](Graph-Commands) | [Organizations Commands →](Organizations-Commands)
