# Command Reference

Complete reference for every `pmapper` command, subcommand, and flag.

---

## Global Options

These flags apply to **all** subcommands and must be placed **before** the subcommand name:

```
pmapper [GLOBAL OPTIONS] <subcommand> [SUBCOMMAND OPTIONS]
```

| Flag | Description |
|------|-------------|
| `--profile PROFILE` | AWS CLI profile to use for API calls |
| `--account ACCOUNT_ID` | Work with a stored graph offline (12-digit AWS account ID) |
| `--debug` | Enable debug-level logging output |

---

## Subcommands at a Glance

| Subcommand | Sub-subcommands | Description | Detailed Page |
|------------|-----------------|-------------|---------------|
| `graph` | `create`, `display`, `list` | Build and manage IAM graphs | [Graph Commands](Graph-Commands) |
| `orgs` | `create`, `update`, `display`, `list` | AWS Organizations and SCPs | [Organizations Commands](Organizations-Commands) |
| `query` | — | Human-readable queries | [Query Commands](Query-Commands) |
| `argquery` | — | Structured/argument-based queries | [Query Commands](Query-Commands) |
| `repl` | — | Interactive query shell | [REPL Mode](REPL-Mode) |
| `analysis` | — | Automated risk analysis | [Analysis Commands](Analysis-Commands) |
| `visualize` | — | Generate graph images | [Visualization Commands](Visualization-Commands) |

---

## Full Flag Reference

### `pmapper graph create`

| Flag | Type | Description |
|------|------|-------------|
| `--ignore-orgs` | boolean | Skip AWS Organizations/SCP checks |
| `--localstack-endpoint URL` | string | HTTP(S) endpoint for LocalStack |
| `--include-regions REGION [...]` | list | Allow-list of AWS regions to scan |
| `--exclude-regions REGION [...]` | list | Deny-list of AWS regions to skip |
| `--include-services SERVICE [...]` | list | Allow-list of edge-checking services |
| `--exclude-services SERVICE [...]` | list | Deny-list of edge-checking services |

**Available services:** `autoscaling`, `cloudformation`, `codebuild`, `ec2`, `generic_passrole`, `iam`, `lambda`, `sagemaker`, `ssm`, `sts`

### `pmapper graph display`

No additional flags. Uses `--profile` or `--account` from global options.

### `pmapper graph list`

No additional flags.

---

### `pmapper query`

| Flag | Type | Description |
|------|------|-------------|
| `-s`, `--skip-admin` | boolean | Skip admin-level principals |
| `-u`, `--include-unauthorized` | boolean | Show unauthorized principals too |
| `--with-resource-policy` | boolean | Auto-fetch resource policy for the target |
| `--resource-policy-text TEXT` | string | Inline resource policy JSON |
| `--resource-owner ACCOUNT_ID` | string | Resource owner account (required for S3) |
| `--session-policy TEXT` | string | Session policy JSON |
| `--scps` | boolean | Apply stored SCPs |
| `QUERY` | positional | The query string |

---

### `pmapper argquery`

| Flag | Type | Description |
|------|------|-------------|
| `-s`, `--skip-admin` | boolean | Skip admin-level principals |
| `-u`, `--include-unauthorized` | boolean | Show unauthorized principals too |
| `--principal PRINCIPAL` | string | Principal ARN or `*` (default: `*`) |
| `--action ACTION` | string | AWS action to test (e.g., `s3:GetObject`) |
| `--resource RESOURCE` | string | Resource ARN (default: `*`) |
| `--condition KEY=VALUE` | string (repeatable) | Condition key-value pair |
| `--preset PRESET` | string | Preset query name (e.g., `privesc`) |
| `--exploit` | boolean | Output exploit AWS CLI commands |
| `--with-resource-policy` | boolean | Auto-fetch resource policy |
| `--resource-policy-text TEXT` | string | Inline resource policy JSON |
| `--resource-owner ACCOUNT_ID` | string | Resource owner |
| `--session-policy TEXT` | string | Session policy JSON |
| `--scps` | boolean | Apply stored SCPs |

---

### `pmapper analysis`

| Flag | Type | Description |
|------|------|-------------|
| `--output-type text\|json` | choice | Output format (default: `text`) |
| `--exploit` | boolean | Include AWS CLI exploit commands |

---

### `pmapper visualize`

| Flag | Type | Description |
|------|------|-------------|
| `--filetype svg\|png\|dot\|graphml` | choice | Output file format (default: `svg`) |
| `--only-privesc` | boolean | Only show privilege escalation edges |
| `--with-services` | boolean | Include service principals |

---

### `pmapper orgs create`

No additional flags (uses `--profile` from global options).

### `pmapper orgs update`

| Flag | Type | Description |
|------|------|-------------|
| `--org ORG_ID` | string (required) | Organization ID to update |

### `pmapper orgs display`

| Flag | Type | Description |
|------|------|-------------|
| `--org ORG_ID` | string (required) | Organization ID to display |

### `pmapper orgs list`

No additional flags.

---

### `pmapper repl`

No additional flags. Uses `--profile` or `--account` from global options.

---

[← Installation](Installation) | [Graph Commands →](Graph-Commands)
