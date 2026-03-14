# Organizations Commands

The `orgs` subcommand manages AWS Organizations data, including Service Control Policies (SCPs) and cross-account edge analysis.

---

## Overview

PMapper's Organizations support enables:
- **SCP enforcement**: Apply Service Control Policies during query evaluation
- **Cross-account edges**: Discover lateral movement paths between accounts
- **OU visualization**: Display the organizational hierarchy with SCP inheritance

---

## `pmapper orgs create`

Creates and stores an OrganizationTree by pulling data from a live AWS Organization.

```bash
pmapper --profile management-account orgs create
```

### What it does

1. Authenticates with the management account credentials
2. Enumerates all accounts, OUs, and SCPs in the organization
3. Maps each graphed account to its OU path
4. Computes cross-account edges between all locally stored graphs
5. Stores the organization data to disk

### Required Permissions

The credentials must have:
- `organizations:DescribeOrganization`
- `organizations:ListAccounts`
- `organizations:ListRoots`
- `organizations:ListOrganizationalUnitsForParent`
- `organizations:ListPolicies`
- `organizations:DescribePolicy`
- `organizations:ListTargetsForPolicy`
- `organizations:ListAccountsForParent`

### Important Notes

> **Cannot use `--account`**: This command requires a live AWS session and does not support offline mode.

> **Graph first, then org**: You should create graphs for individual accounts (`pmapper graph create`) before running `pmapper orgs create`. The orgs command will cross-reference locally stored graphs when computing cross-account edges.

---

## `pmapper orgs update`

Updates all locally stored graphs with the latest Organizations metadata and recomputes cross-account edges. This is an **offline operation** that uses previously stored data.

```bash
pmapper orgs update --org o-abc123def4
```

### When to use

- After creating new account graphs to include them in cross-account analysis
- After modifying SCPs in the AWS console (re-run `orgs create` first, then `update`)
- To refresh OU-path mappings

| Flag | Description |
|------|-------------|
| `--org ORG_ID` | **(Required)** Organization ID (format: `o-xxxxxxxxxx`) |

---

## `pmapper orgs display`

Displays the full organizational tree structure, including accounts, OUs, and SCP assignments:

```bash
pmapper orgs display --org o-abc123def4
```

### Example Output

```
Organization o-abc123def4:
"Root" (r-ab12):
  Accounts:
    111111111111:
      Directly Attached SCPs: ['FullAWSAccess']
      Inherited SCPs:         []
  Directly Attached SCPs: ['FullAWSAccess']
  Inherited SCPs:         []
  Child OUs:
    "Production" (ou-ab12-prod1234):
      Accounts:
        222222222222:
          Directly Attached SCPs: ['DenyLeaveOrg']
          Inherited SCPs:         ['FullAWSAccess']
      Directly Attached SCPs: ['DenyLeaveOrg', 'DenyS3Delete']
      Inherited SCPs:         ['FullAWSAccess']
      Child OUs:
    "Development" (ou-ab12-dev56789):
      Accounts:
        333333333333:
          Directly Attached SCPs: ['FullAWSAccess']
          Inherited SCPs:         ['FullAWSAccess']
      Directly Attached SCPs: ['FullAWSAccess']
      Inherited SCPs:         ['FullAWSAccess']
      Child OUs:
```

| Flag | Description |
|------|-------------|
| `--org ORG_ID` | **(Required)** Organization ID to display |

---

## `pmapper orgs list`

Lists all locally stored Organizations:

```bash
pmapper orgs list
```

### Example Output

```
Organization IDs:
---
o-abc123def4 (PMapper Version 1.2.0)
```

---

## End-to-End Workflow

```bash
# 1. Graph individual accounts
pmapper --profile dev graph create
pmapper --profile staging graph create
pmapper --profile prod graph create

# 2. Create the organization tree (from management account)
pmapper --profile management orgs create

# 3. Run queries with SCP enforcement
pmapper --account 222222222222 query --scps 'who can do iam:CreateUser'

# 4. Re-graph an account and update the org
pmapper --profile dev graph create
pmapper orgs update --org o-abc123def4
```

---

### Storage Location

Organization data is stored alongside account graphs:
- **Linux**: `~/.local/share/principalmapper/o-xxxxxxxxxx/`
- **macOS**: `~/Library/Application Support/principalmapper/o-xxxxxxxxxx/`

---

[← Query Commands](Query-Commands) | [Visualization Commands →](Visualization-Commands)
