# PMapper (Principal Mapper) Wiki

Welcome to the PMapper wiki — your comprehensive guide to identifying and analyzing IAM privilege escalation risks in AWS.

## What is PMapper?

PMapper models IAM Users and Roles in an AWS account as a **directed graph**, enabling automated checks for privilege escalation and lateral movement paths. It locally simulates AWS authorization to determine not just what a principal can do directly, but what they could do by pivoting through other principals.

**Key capabilities:**
- 🔍 Discover privilege escalation paths across 10 AWS services
- 🗺️ Visualize IAM relationships as interactive graphs
- 🏢 Map multi-account AWS Organizations with SCP analysis
- 💥 Generate exploit commands for identified attack paths (180+ vectors)
- 📊 Export findings as JSON for SIEM/pipeline integration

---

## 📚 Wiki Pages

| Page | Description |
|------|-------------|
| [Installation](Installation) | pip, source, Docker setup, and prerequisites |
| [Command Reference](Command-Reference) | Master table of all commands, subcommands, and flags |
| [Graph Commands](Graph-Commands) | `pmapper graph create\|display\|list` |
| [Query Commands](Query-Commands) | `pmapper query` and `pmapper argquery` |
| [Organizations Commands](Organizations-Commands) | `pmapper orgs create\|update\|display\|list` |
| [Visualization Commands](Visualization-Commands) | `pmapper visualize` with all output formats |
| [Analysis Commands](Analysis-Commands) | `pmapper analysis` with `--exploit` |
| [REPL Mode](REPL-Mode) | Interactive querying session |
| [Troubleshooting](Troubleshooting) | Common errors and solutions |

---

## Quick Start

```bash
pip install principalmapper
pmapper --profile my-profile graph create
pmapper --account 123456789012 query -s 'preset privesc *'
pmapper --account 123456789012 analysis --exploit
pmapper --account 123456789012 visualize --filetype svg
```

See the [README](https://github.com/nccgroup/PMapper#-quick-start-tldr) for the full quick-start guide.
