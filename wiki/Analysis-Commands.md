# Analysis Commands

The `analysis` subcommand runs all built-in risk checks against a stored graph and reports findings. This is the recommended way to get a comprehensive security assessment.

---

## Basic Usage

```bash
# Text output (human-readable, default)
pmapper --account 123456789012 analysis

# Using live credentials
pmapper --profile my-profile analysis
```

---

## Output Formats

### Text (Default)

```bash
pmapper --account 123456789012 analysis --output-type text
```

Human-readable output ideal for manual review and terminal display.

### JSON

```bash
pmapper --account 123456789012 analysis --output-type json
```

Machine-readable output ideal for:
- CI/CD pipeline integration
- SIEM ingestion
- Custom reporting scripts
- Automated alerting

```bash
# Save to file
pmapper --account 123456789012 analysis --output-type json > findings.json

# Pipe to jq for filtering
pmapper --account 123456789012 analysis --output-type json | jq '.[] | select(.severity == "HIGH")'
```

---

## Exploit Generation

The `--exploit` flag enhances findings with the exact AWS CLI commands an attacker would use to exploit each identified path:

```bash
pmapper --account 123456789012 analysis --exploit
```

This maps to PMapper's database of **180+ privilege escalation vectors** aligned with the MITRE ATT&CK framework.

### Combined with JSON

```bash
pmapper --account 123456789012 analysis --output-type json --exploit > full-report.json
```

---

## All Flags

| Flag | Description |
|------|-------------|
| `--output-type text\|json` | Output format (default: `text`) |
| `--exploit` | Include AWS CLI exploit commands for each finding |

---

## What Gets Checked

The analysis command runs the following checks against the stored graph:

| Check | Description |
|-------|-------------|
| **Admin identification** | Identifies all principals with effective admin access |
| **Privilege escalation** | Discovers paths from non-admin to admin via IAM, passrole, STS, etc. |
| **Cross-service escalation** | Finds paths through Lambda, EC2, CloudFormation, CodeBuild, etc. |
| **Resource exposure** | Identifies resources with overly permissive policies |

---

## Common Workflows

### Security Audit Report

```bash
# Generate comprehensive report
pmapper --profile target graph create
ACCT=$(pmapper graph list | grep -oP '\d{12}' | head -1)

# Text report for stakeholders
pmapper --account $ACCT analysis --exploit > audit-report.txt

# JSON report for tracking
pmapper --account $ACCT analysis --output-type json --exploit > audit-report.json

# Visual diagram
pmapper --account $ACCT visualize --only-privesc --filetype svg
```

### Continuous Monitoring

```bash
#!/bin/bash
# Run weekly and diff against previous results
DATE=$(date +%Y-%m-%d)
pmapper --profile prod graph create
pmapper --account 123456789012 analysis --output-type json > "findings-$DATE.json"

# Compare with last week
diff <(jq -S . findings-last.json) <(jq -S . "findings-$DATE.json")
```

---

[← Visualization Commands](Visualization-Commands) | [REPL Mode →](REPL-Mode)
