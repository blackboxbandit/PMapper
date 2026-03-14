#!/usr/bin/env python3
"""
PMapper Test Environment — CLI wrapper for Terraform-based IAM privilege
escalation test scenarios.

Usage:
    pmapper_test_env.py list                          # List all groups and scenarios
    pmapper_test_env.py create --group sagemaker       # Deploy all SageMaker scenarios
    pmapper_test_env.py create --issue 5.2             # Deploy only scenario 5.2
    pmapper_test_env.py create --all                   # Deploy everything
    pmapper_test_env.py destroy                        # Tear down all resources
    pmapper_test_env.py status                         # Show what's currently deployed
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap

# ─── Scenario Registry ─────────────────────────────────────────────────────
# Maps section number → (group_name, group_description, {scenario_id: description})

SCENARIO_REGISTRY = {
    1: {
        "group": "iam",
        "title": "IAM — Direct IAM Privilege Escalation",
        "scenarios": {
            "1.1": "CreateAccessKey — User A can create access keys for User B",
            "1.2": "UpdateLoginProfile — User A can set password for User B",
            "1.3": "PutUserPolicy — User A can add inline policy to User B",
            "1.4": "AttachUserPolicy — User A can attach managed policy to User B",
            "1.5": "PutGroupPolicy — User A can add inline policy to Group containing User B",
            "1.6": "AttachGroupPolicy — User A can attach managed policy to Group containing User B",
            "1.7": "UpdateAssumeRolePolicy — User A can update trust policy of Role B",
            "1.8": "PutRolePolicy — User A can add inline policy to Role B",
            "1.9": "AttachRolePolicy — User A can attach managed policy to Role B",
        },
    },
    2: {
        "group": "sts",
        "title": "STS — AssumeRole Escalation",
        "scenarios": {
            "2.1": "AssumeRole (identity policy allows) — User A has sts:AssumeRole; Role B trusts User A",
            "2.2": "AssumeRole (trust policy NODE_MATCH) — Role B trusts account root",
        },
    },
    3: {
        "group": "ec2",
        "title": "EC2 — PassRole to EC2",
        "scenarios": {
            "3.1": "RunInstances + PassRole (existing instance profile)",
            "3.2": "RunInstances + AssociateIamInstanceProfile + CreateInstanceProfile (no existing IP)",
        },
    },
    4: {
        "group": "lambda",
        "title": "Lambda — PassRole to Lambda",
        "scenarios": {
            "4.1": "CreateFunction + PassRole — create new Lambda with target role",
            "4.2": "UpdateFunctionCode — modify existing Lambda's code",
        },
    },
    5: {
        "group": "sagemaker",
        "title": "SageMaker — PassRole to SageMaker",
        "scenarios": {
            "5.1": "CreateNotebookInstance + PassRole",
            "5.2": "CreateTrainingJob + PassRole",
            "5.3": "CreateProcessingJob + PassRole",
        },
    },
    6: {
        "group": "ssm",
        "title": "SSM — SendCommand / StartSession",
        "scenarios": {
            "6.1": "SendCommand — send commands to EC2 instances running target role",
            "6.2": "StartSession — start SSM session to EC2 instances running target role",
        },
    },
    7: {
        "group": "codebuild",
        "title": "CodeBuild — PassRole to CodeBuild",
        "scenarios": {
            "7.1": "CreateProject + StartBuild + PassRole",
            "7.2": "UpdateProject + StartBuild + PassRole",
        },
    },
    8: {
        "group": "cloudformation",
        "title": "CloudFormation — PassRole to CloudFormation",
        "scenarios": {
            "8.1": "CreateStack + PassRole",
            "8.2": "UpdateStack + PassRole",
        },
    },
    9: {
        "group": "autoscaling",
        "title": "AutoScaling — PassRole to EC2 Auto Scaling",
        "scenarios": {
            "9.1": "CreateAutoScalingGroup + existing LaunchConfig + ServiceLinkedRole",
            "9.2": "CreateLaunchConfiguration + CreateAutoScalingGroup + PassRole",
        },
    },
    10: {
        "group": "glue",
        "title": "Glue — PassRole to AWS Glue",
        "scenarios": {
            "10.1": "CreateDevEndpoint + PassRole",
            "10.2": "UpdateDevEndpoint + PassRole",
        },
    },
}

# Reverse lookup: group_name → section_number
GROUP_TO_SECTION = {info["group"]: section for section, info in SCENARIO_REGISTRY.items()}

# Reverse lookup: scenario_id → section_number
SCENARIO_TO_SECTION = {}
for section, info in SCENARIO_REGISTRY.items():
    for scenario_id in info["scenarios"]:
        SCENARIO_TO_SECTION[scenario_id] = section

# All valid group names
VALID_GROUPS = sorted(GROUP_TO_SECTION.keys())

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ─── Helpers ────────────────────────────────────────────────────────────────

def _colour(text: str, code: str) -> str:
    """ANSI colour wrapper."""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def _bold(text: str) -> str:
    return _colour(text, "1")


def _green(text: str) -> str:
    return _colour(text, "32")


def _yellow(text: str) -> str:
    return _colour(text, "33")


def _red(text: str) -> str:
    return _colour(text, "31")


def _cyan(text: str) -> str:
    return _colour(text, "36")


def _run_terraform(args: list, env_extra: dict = None) -> subprocess.CompletedProcess:
    """Run a terraform command from the terraform_tests directory."""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    cmd = ["terraform"] + args
    print(f"\n  {_cyan('$')} {' '.join(cmd)}\n")
    return subprocess.run(cmd, cwd=SCRIPT_DIR, env=env)


def _ensure_init():
    """Run terraform init if .terraform doesn't exist."""
    tf_dir = os.path.join(SCRIPT_DIR, ".terraform")
    if not os.path.isdir(tf_dir):
        print(_yellow("  ⚙  Running terraform init..."))
        result = _run_terraform(["init"])
        if result.returncode != 0:
            print(_red("  ✗  terraform init failed"))
            sys.exit(1)
        print(_green("  ✓  terraform init complete"))


def _build_tfvars(groups: dict) -> str:
    """
    Build a .tfvars file content from a dict of {group_name: [scenario_ids] or None}.
    If scenario_ids is None, all scenarios for the group are enabled.
    """
    lines = []
    for group_name, scenarios in sorted(groups.items()):
        lines.append(f'enable_{group_name} = true')
        if scenarios:
            scenario_list = ', '.join(f'"{s}"' for s in sorted(scenarios))
            lines.append(f'{group_name}_scenarios = [{scenario_list}]')
        else:
            lines.append(f'{group_name}_scenarios = []')
        lines.append("")
    return "\n".join(lines)


def _resolve_groups(args) -> dict:
    """
    Resolve --group, --issue, --all into a dict of {group_name: [scenario_ids] or None}.
    Returns None if nothing to deploy.
    """
    groups = {}

    if getattr(args, 'all', False):
        for section, info in SCENARIO_REGISTRY.items():
            groups[info["group"]] = None  # None = all scenarios
        return groups

    if getattr(args, 'group', None):
        for group_name in args.group:
            group_name = group_name.lower()
            if group_name not in GROUP_TO_SECTION:
                print(_red(f"  ✗  Unknown group: '{group_name}'"))
                print(f"     Valid groups: {', '.join(VALID_GROUPS)}")
                sys.exit(1)
            groups[group_name] = None

    if getattr(args, 'issue', None):
        for issue_id in args.issue:
            if issue_id not in SCENARIO_TO_SECTION:
                # Maybe user passed just a section number like "5"
                try:
                    section = int(issue_id)
                    if section in SCENARIO_REGISTRY:
                        group_name = SCENARIO_REGISTRY[section]["group"]
                        groups[group_name] = None
                        continue
                except ValueError:
                    pass
                print(_red(f"  ✗  Unknown issue: '{issue_id}'"))
                print(f"     Use 'list' to see valid issue IDs")
                sys.exit(1)

            section = SCENARIO_TO_SECTION[issue_id]
            group_name = SCENARIO_REGISTRY[section]["group"]
            if group_name not in groups:
                groups[group_name] = []
            if groups[group_name] is not None:
                groups[group_name].append(issue_id)

    return groups if groups else None


# ─── Commands ───────────────────────────────────────────────────────────────

def cmd_list(args):
    """List all available scenario groups and individual issues."""
    print()
    print(_bold("  PMapper Test Environment — Scenario Reference"))
    print(_bold("  " + "=" * 60))

    total = 0
    for section in sorted(SCENARIO_REGISTRY.keys()):
        info = SCENARIO_REGISTRY[section]
        print()
        print(f"  {_bold(_cyan(f'Section {section}'))} — {_bold(info['title'])}")
        print(f"  Group: {_green(info['group'])}")
        print()
        for scenario_id in sorted(info["scenarios"].keys(), key=lambda x: list(map(int, x.split('.')))):
            desc = info["scenarios"][scenario_id]
            print(f"    {_yellow(scenario_id):>8s}  {desc}")
            total += 1
        print()

    print(f"  {_bold(f'Total: {total} scenarios across {len(SCENARIO_REGISTRY)} groups')}")
    print()
    print(_bold("  Usage Examples:"))
    print(f"    {_cyan('pmapper_test_env.py create --group sagemaker')}      Deploy all SageMaker scenarios")
    print(f"    {_cyan('pmapper_test_env.py create --issue 5.2')}            Deploy scenario 5.2 only")
    print(f"    {_cyan('pmapper_test_env.py create --issue 5')}              Deploy all of section 5")
    print(f"    {_cyan('pmapper_test_env.py create --group iam --group sts')} Deploy IAM + STS")
    print(f"    {_cyan('pmapper_test_env.py create --all')}                  Deploy everything")
    print(f"    {_cyan('pmapper_test_env.py destroy')}                       Tear down all resources")
    print(f"    {_cyan('pmapper_test_env.py status')}                        Show deployed resources")
    print()


def cmd_create(args):
    """Create (deploy) scenarios."""
    groups = _resolve_groups(args)
    if not groups:
        print(_red("  ✗  No scenarios specified. Use --group, --issue, or --all"))
        sys.exit(1)

    # Show what will be deployed
    print()
    print(_bold("  Deploying scenarios:"))
    for group_name, scenarios in sorted(groups.items()):
        section = GROUP_TO_SECTION[group_name]
        info = SCENARIO_REGISTRY[section]
        if scenarios is None:
            print(f"    {_green(f'Section {section}')} — {info['title']} ({_yellow('all scenarios')})")
        else:
            for s in sorted(scenarios, key=lambda x: list(map(int, x.split('.')))):
                desc = info["scenarios"].get(s, "")
                print(f"    {_green(s)} — {desc}")

    # Write tfvars
    tfvars_content = _build_tfvars(groups)
    tfvars_path = os.path.join(SCRIPT_DIR, "active.auto.tfvars")
    with open(tfvars_path, "w") as f:
        f.write(tfvars_content)
    print(f"\n  {_cyan('Wrote')} {tfvars_path}")

    # Run terraform
    _ensure_init()
    result = _run_terraform(["apply", "-auto-approve"])
    if result.returncode != 0:
        print(_red("\n  ✗  terraform apply failed"))
        sys.exit(1)

    print(_green("\n  ✓  Scenarios deployed successfully!"))
    print(f"\n  Next steps:")
    print(f"    1. Run {_cyan('pmapper graph --create')} to collect the IAM graph")
    print(f"    2. Run {_cyan('pmapper analysis')} to identify privilege escalation edges")
    print(f"    3. When done, run {_cyan('pmapper_test_env.py destroy')} to clean up")
    print()


def cmd_destroy(args):
    """Destroy all deployed resources."""
    print()
    print(_yellow("  ⚠  This will destroy ALL test resources"))

    _ensure_init()

    # Remove the auto.tfvars so terraform doesn't try to enable modules
    tfvars_path = os.path.join(SCRIPT_DIR, "active.auto.tfvars")
    if os.path.exists(tfvars_path):
        os.remove(tfvars_path)
        print(f"  {_cyan('Removed')} {tfvars_path}")

    result = _run_terraform(["destroy", "-auto-approve"])
    if result.returncode != 0:
        print(_red("\n  ✗  terraform destroy failed"))
        sys.exit(1)

    print(_green("\n  ✓  All test resources destroyed"))
    print()


def cmd_status(args):
    """Show currently deployed scenarios."""
    _ensure_init()

    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(_red("  ✗  Failed to get terraform output"))
        print(result.stderr)
        sys.exit(1)

    try:
        outputs = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(_yellow("  No scenarios currently deployed"))
        return

    print()
    print(_bold("  Currently Deployed Scenarios"))
    print(_bold("  " + "=" * 60))

    any_deployed = False
    for key, data in sorted(outputs.items()):
        value = data.get("value", {})
        if not value:
            continue

        any_deployed = True
        group_name = key.replace("_scenarios", "")
        section = GROUP_TO_SECTION.get(group_name)
        info = SCENARIO_REGISTRY.get(section, {})
        print(f"\n  {_bold(_cyan(info.get('title', group_name)))}")

        for scenario_id, details in sorted(value.items()):
            if isinstance(details, dict):
                print(f"    {_green(scenario_id)} — {details.get('name', '')}")
                print(f"           Attacker: {details.get('attacker', 'N/A')}")
                print(f"           Target:   {details.get('target', 'N/A')}")
                print(f"           Edge:     {_yellow(details.get('edge', 'N/A'))}")

    if not any_deployed:
        print(_yellow("\n  No scenarios currently deployed"))

    print()


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PMapper Test Environment — Deploy IAM privilege escalation scenarios for PMapper testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s list                          List all groups and scenarios
              %(prog)s create --group sagemaker      Deploy all SageMaker scenarios (section 5)
              %(prog)s create --issue 5.2            Deploy only scenario 5.2
              %(prog)s create --issue 5              Deploy all scenarios in section 5
              %(prog)s create --all                  Deploy everything
              %(prog)s destroy                       Tear down all resources
              %(prog)s status                        Show what's deployed
        """),
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list
    subparsers.add_parser("list", help="List all available scenario groups and issues")

    # create
    create_parser = subparsers.add_parser("create", help="Deploy test scenarios")
    create_group = create_parser.add_mutually_exclusive_group()
    create_parser.add_argument(
        "--group", action="append", metavar="NAME",
        help=f"Deploy all scenarios in a group. Valid groups: {', '.join(VALID_GROUPS)}"
    )
    create_parser.add_argument(
        "--issue", action="append", metavar="ID",
        help="Deploy a specific scenario by ID (e.g. 5.2) or all in a section (e.g. 5)"
    )
    create_parser.add_argument(
        "--all", action="store_true",
        help="Deploy all scenarios"
    )

    # destroy
    subparsers.add_parser("destroy", help="Destroy all deployed test resources")

    # status
    subparsers.add_parser("status", help="Show currently deployed scenarios")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "list": cmd_list,
        "create": cmd_create,
        "destroy": cmd_destroy,
        "status": cmd_status,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
