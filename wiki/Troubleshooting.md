# Troubleshooting

Common issues and solutions when using PMapper.

---

## Installation Issues

### `graphviz` / `dot` not found

**Error:**
```
Error: The "dot" executable (part of Graphviz) was not found. Visualization requires Graphviz.
```

**Solution:**
```bash
# macOS
brew install graphviz

# Ubuntu / Debian
sudo apt install graphviz

# Amazon Linux / CentOS
sudo yum install graphviz

# Verify installation
dot -V
```

### `pydot` import errors

**Error:**
```
ModuleNotFoundError: No module named 'pydot'
```

**Solution:**
```bash
pip install pydot
```

---

## Credential Issues

### No credentials found

**Error:**
```
Error: Unable to establish a live AWS session (Unable to locate credentials).
```

**Solutions:**
1. Specify a profile: `pmapper --profile my-profile graph create`
2. Set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID="AKIA..."
   export AWS_SECRET_ACCESS_KEY="..."
   ```
3. Verify your credentials file exists at `~/.aws/credentials`

### Wrong account / profile

**Error:**
```
Error: Unable to load graph for account 123456789012
```

**Solutions:**
1. Check which graphs are stored: `pmapper graph list`
2. Ensure you've created the graph first: `pmapper --profile correct-profile graph create`
3. Use the correct account ID from the output of `graph list`

### Profile not picking up credentials

**Symptom:** Using `--profile default` doesn't load credentials properly.

**Solutions:**
1. Verify the profile exists in `~/.aws/credentials`:
   ```ini
   [default]
   aws_access_key_id = AKIA...
   aws_secret_access_key = ...
   ```
2. Check for config in `~/.aws/config`:
   ```ini
   [default]
   region = us-east-1
   ```
3. Try without `--profile` (PMapper uses the default profile automatically)

---

## Graph Issues

### Graph not found

**Error:**
```
Error: Unable to load graph for account 123456789012
```

**Solutions:**
1. Run `pmapper graph list` to see available graphs
2. Create the graph if it doesn't exist: `pmapper --profile my-profile graph create`
3. Verify the account ID is correct (12 digits)

### Graph creation hangs or is very slow

**Cause:** PMapper scans all regions and all edge services by default.

**Solutions:**
```bash
# Limit to specific regions
pmapper --profile my-profile graph create --include-regions us-east-1

# Limit to specific services
pmapper --profile my-profile graph create --include-services iam sts

# Skip Organizations checks
pmapper --profile my-profile graph create --ignore-orgs
```

### Insufficient permissions during graph creation

**Symptom:** Warnings about missing permissions for certain services.

**Solution:** Ensure the IAM principal has the required read permissions. See [Installation → IAM Permissions Required](Installation#iam-permissions-required).

You can also skip certain edge services if you lack permissions:
```bash
pmapper --profile my-profile graph create --exclude-services sagemaker codebuild
```

---

## Organizations Issues

### SCP errors during queries

**Error:**
```
ValueError: Graph for account 123456789012 does not have an associated OrganizationTree mapped
```

**Solution:**
1. Create the organization data: `pmapper --profile management orgs create`
2. Update existing graphs: `pmapper orgs update --org o-abc123def4`
3. Alternatively, don't use the `--scps` flag if you don't need SCP evaluation

### No orgs subcommand specified

**Error:**
```
Error: No orgs subcommand provided. Please select a subcommand (create, update, display, list).
```

**Solution:** Add a subcommand:
```bash
pmapper orgs create    # not: pmapper orgs
pmapper orgs list
```

---

## Query Issues

### No graph subcommand specified

**Error:**
```
Error: No graph subcommand provided. Please select a subcommand (create, display, list).
```

**Solution:** Add a subcommand:
```bash
pmapper graph create    # not: pmapper graph
```

### Argquery missing action or preset

**Error:**
```
Error: Must specify either an action (--action) or a preset query (--preset) to run a query.
```

**Solution:**
```bash
# Specify an action
pmapper --account 123456789012 argquery --action 'iam:CreateUser'

# Or use a preset
pmapper --account 123456789012 argquery --preset privesc
```

### `--profile` after subcommand

**Symptom:** `--profile` not recognized or credentials not loading.

**Solution:** Global flags must come **before** the subcommand:
```bash
# ✅ Correct
pmapper --profile prod graph create

# ❌ Wrong
pmapper graph create --profile prod
```

---

## Visualization Issues

### Empty or incomplete visualization

**Cause:** The graph may have very few edges if services were excluded during creation.

**Solution:** Re-create the graph with all services:
```bash
pmapper --profile my-profile graph create
```

### Large unreadable SVG

**Solution:** Use `--only-privesc` to focus on escalation paths:
```bash
pmapper --account 123456789012 visualize --only-privesc
```

Or export as GraphML and use a dedicated graph tool:
```bash
pmapper --account 123456789012 visualize --filetype graphml
```

---

## Debug Mode

For any issue, enable debug logging to get detailed information:

```bash
pmapper --debug --profile my-profile graph create
```

This outputs:
- API calls being made
- Edge checks being performed
- SCP evaluation details
- Error stack traces

---

[← REPL Mode](REPL-Mode) | [Home](Home)
