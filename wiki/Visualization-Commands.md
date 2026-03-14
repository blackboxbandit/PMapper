# Visualization Commands

The `visualize` subcommand generates graph images showing IAM relationships and privilege escalation paths.

---

## Prerequisites

Visualization requires **Graphviz** to be installed:

```bash
# macOS
brew install graphviz

# Ubuntu / Debian
sudo apt install graphviz

# Amazon Linux / CentOS
sudo yum install graphviz
```

---

## Basic Usage

```bash
# Default: SVG output
pmapper --account 123456789012 visualize
# Creates: ./123456789012.svg

# With live credentials
pmapper --profile my-profile visualize
```

---

## Output Formats

| Format | Flag | Best For |
|--------|------|----------|
| **SVG** (default) | `--filetype svg` | Web embedding, scalable viewing |
| **PNG** | `--filetype png` | Reports, presentations |
| **DOT** | `--filetype dot` | Custom rendering with Graphviz tools |
| **GraphML** | `--filetype graphml` | Graph analysis tools (Gephi, yEd, etc.) |

```bash
pmapper --account 123456789012 visualize --filetype png
pmapper --account 123456789012 visualize --filetype dot
pmapper --account 123456789012 visualize --filetype graphml
```

---

## Visualization Modes

### Full Graph

Shows all IAM principals (Users and Roles) with edges representing access paths:

```bash
pmapper --account 123456789012 visualize
# Output: ./123456789012.svg
```

### Privilege Escalation Only

Shows only the edges that represent privilege escalation paths:

```bash
pmapper --account 123456789012 visualize --only-privesc
# Output: ./123456789012-privesc-risks.svg
```

This is particularly useful for executive reports and focused security reviews.

### Including Service Principals

Shows which AWS services can assume which roles:

```bash
pmapper --account 123456789012 visualize --with-services
```

---

## Output Files

| Mode | Filename Pattern |
|------|-----------------|
| Full graph | `./<account-id>.<filetype>` |
| Privesc only | `./<account-id>-privesc-risks.<filetype>` |

Files are always created in the **current working directory**.

---

## All Flags

| Flag | Description |
|------|-------------|
| `--filetype svg\|png\|dot\|graphml` | Output format (default: `svg`) |
| `--only-privesc` | Only render privilege escalation edges |
| `--with-services` | Include AWS service principals in the graph |

---

## Tips

- **Large accounts**: For accounts with many principals, use `--only-privesc` to reduce visual clutter
- **Reports**: Generate both the full graph and privesc-only view for comprehensive reporting
- **Custom styling**: Export as DOT format and customize the graph using Graphviz attributes
- **Graph analysis**: Export as GraphML and import into Gephi or yEd for interactive exploration

---

[← Organizations Commands](Organizations-Commands) | [Analysis Commands →](Analysis-Commands)
