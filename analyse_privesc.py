#!/usr/bin/env python3
"""
Comprehensive analysis of all 20,444 AWS IAM permissions across 444 services.
Identifies ALL privilege escalation paths by examining:
1. Services whose resource ARNs reference IAM roles (arn:...role/...)
2. Services whose privilege resource_types reference role resources
3. Keyword analysis of privilege descriptions for role-passing/code-exec patterns
4. Cross-reference to find uncovered service combinations
"""
import json
import re
from collections import defaultdict

with open('iam_definition.json') as f:
    data = json.load(f)

# Build a quick lookup
svc_map = {s['prefix']: s for s in data}

CREATE_KW = {'Create','Run','Start','Launch','Submit','Register','Deploy','Invoke','Execute','Activate','Put','Import'}
MODIFY_KW = {'Update','Modify','Set','Change','Replace','Associate','Attach','Add','Configure',
             'Override','Patch','Enable','Disable','Restart','Reboot','Upgrade','Send'}

ROLE_TERMS = ['role', 'instance-profile', 'instanceprofile', 'execution role', 'service role',
              'task role', 'job role', 'instance role', 'iam role']

###############################################################################
# STEP 1: Find services whose resource ARN patterns contain "role"
###############################################################################
print("=" * 120)
print("STEP 1: Services with IAM role/instance-profile as a resource ARN")
print("=" * 120)

svc_has_role_resource = {}
for svc in data:
    prefix = svc['prefix']
    for res in svc.get('resources', []):
        arn = res.get('arn', '').lower()
        res_name = res.get('resource', '').lower()
        if ':role/' in arn or 'instance-profile' in arn or 'role' in res_name:
            if prefix not in svc_has_role_resource:
                svc_has_role_resource[prefix] = []
            svc_has_role_resource[prefix].append(f"{res.get('resource')}: {res.get('arn')}")

print(f"\nServices with role-type resources ({len(svc_has_role_resource)}):")
for prefix in sorted(svc_has_role_resource):
    print(f"\n  [{prefix}]")
    for r in svc_has_role_resource[prefix]:
        print(f"    {r}")

###############################################################################
# STEP 2: Services whose PRIVILEGES reference a role resource_type
###############################################################################
print("\n\n" + "=" * 120)
print("STEP 2: Service privileges that reference role resource_types")
print("=" * 120)

svc_priv_role = defaultdict(lambda: {'create': [], 'modify': [], 'other': []})
for svc in data:
    prefix = svc['prefix']
    for priv in svc.get('privileges', []):
        action = priv.get('privilege', '')
        access_level = priv.get('access_level', '')
        desc = priv.get('description', '')
        if access_level not in ('Write', 'Permissions management'):
            continue
        
        # Check if any resource_type looks like a role
        for rt in priv.get('resource_types', []):
            rt_name = rt.get('resource_type', '').lower().rstrip('*')
            if rt_name and ('role' in rt_name or 'instance-profile' in rt_name or 'execution' in rt_name):
                action_kw = action.split('_')[0] if '_' in action else ''.join(c for c in action if c.isupper())
                first_kw = next((c for c in CREATE_KW if action.startswith(c)), None)
                mod_kw = next((c for c in MODIFY_KW if action.startswith(c)), None)
                entry = f"  {prefix}:{action} [rt={rt_name}]: {desc[:100]}"
                if first_kw:
                    svc_priv_role[prefix]['create'].append(entry)
                elif mod_kw:
                    svc_priv_role[prefix]['modify'].append(entry)
                else:
                    svc_priv_role[prefix]['other'].append(entry)
                break

print(f"\nServices with role-referencing privileges ({len(svc_priv_role)}):")
for prefix in sorted(svc_priv_role):
    info = svc_priv_role[prefix]
    print(f"\n[{prefix}]")
    if info['create']:
        print("  NEW PASSROLE (create/run):")
        for e in info['create']: print(e)
    if info['modify']:
        print("  EXISTING PASSROLE (modify):")
        for e in info['modify']: print(e)
    if info['other']:
        print("  OTHER:")
        for e in info['other']: print(e)

###############################################################################
# STEP 3: Description-based role-passing detection (supplementary)
###############################################################################
print("\n\n" + "=" * 120)
print("STEP 3: Privilege descriptions mentioning execution/task/service role")
print("=" * 120)

desc_role_svcs = defaultdict(list)
for svc in data:
    prefix = svc['prefix']
    for priv in svc.get('privileges', []):
        action = priv.get('privilege', '')
        access_level = priv.get('access_level', '')
        desc = priv.get('description', '').lower()
        
        if access_level not in ('Write', 'Permissions management'):
            continue
        # Skip if already captured in step 2
        already_in_step2 = any(
            f"{prefix}:{action}" in e
            for cat in svc_priv_role.get(prefix, {}).values()
            for e in cat
        )
        if already_in_step2:
            continue
        
        role_in_desc = (
            ('passrole' in desc or 'pass role' in desc) or
            ('execution role' in desc and ('specify' in desc or 'attach' in desc or 'provide' in desc)) or
            ('service role' in desc and ('specify' in desc or 'attach' in desc)) or
            ('iam role' in desc and ('specify' in desc or 'attach' in desc or 'associate' in desc)) or
            ('task role' in desc) or
            ('instance role' in desc and 'associate' in desc)
        )
        if role_in_desc:
            first_kw = next((c for c in CREATE_KW if action.startswith(c)), None)
            mod_kw = next((c for c in MODIFY_KW if action.startswith(c)), None)
            tag = "CREATE" if first_kw else ("MODIFY" if mod_kw else "OTHER")
            desc_role_svcs[prefix].append(f"  [{tag}] {prefix}:{action}: {priv.get('description','')[:110]}")

print(f"\nAdditional services found via description analysis ({len(desc_role_svcs)}):")
for prefix in sorted(desc_role_svcs):
    print(f"\n[{prefix}]")
    for e in desc_role_svcs[prefix]:
        print(e)

###############################################################################
# STEP 4: Complete merged list of ALL potential PassRole-consuming services
###############################################################################
print("\n\n" + "=" * 120)
print("STEP 4: MERGED — ALL services that can consume iam:PassRole")
print("=" * 120)

pmapper_covered = {
    'iam', 'ec2', 'lambda', 'sts', 'ssm', 'sagemaker',
    'cloudformation', 'codebuild', 'autoscaling'
}

all_passrole_svcs = (
    set(svc_has_role_resource.keys()) |
    set(svc_priv_role.keys()) |
    set(desc_role_svcs.keys())
)

missing = all_passrole_svcs - pmapper_covered

print(f"\nTotal PassRole-consuming services: {len(all_passrole_svcs)}")
print(f"Covered by PMapper: {len(pmapper_covered & all_passrole_svcs)}")
print(f"NOT covered: {len(missing)}")

print(f"\nNOT COVERED by PMapper:")
for prefix in sorted(missing):
    svc_name = svc_map.get(prefix, {}).get('service_name', prefix)
    create_actions = [e.split(':')[1].split(' ')[0] for e in svc_priv_role.get(prefix, {}).get('create', [])]
    modify_actions = [e.split(':')[1].split(' ')[0] for e in svc_priv_role.get(prefix, {}).get('modify', [])]
    desc_create = [e for e in desc_role_svcs.get(prefix, []) if '[CREATE]' in e]
    desc_modify = [e for e in desc_role_svcs.get(prefix, []) if '[MODIFY]' in e]
    
    print(f"\n  [{prefix}] {svc_name}")
    if create_actions:
        print(f"    New PassRole:      {', '.join(create_actions)}")
    if desc_create:
        for e in desc_create: print(f"    + {e.strip()}")
    if modify_actions:
        print(f"    Existing PassRole: {', '.join(modify_actions)}")
    if desc_modify:
        for e in desc_modify: print(f"    + {e.strip()}")

###############################################################################
# STEP 5: Extract all actions for key services
###############################################################################
print("\n\n" + "=" * 120)
print("STEP 5: All Write-level actions for key uncovered services")
print("=" * 120)

key_uncovered = [
    'glue', 'ecs', 'batch', 'states', 'events', 'elasticmapreduce', 'eks',
    'apprunner', 'codepipeline', 'codedeploy', 'emr-serverless', 'fis',
    'airflow', 'greengrass', 'iot', 'imagebuilder', 'lightsail',
    'bedrock', 'bedrock-agentcore', 'gamelift', 'opsworks', 'proton',
    'datapipeline', 'elastictranscoder', 'iotanalytics', 'iotfleetwise',
    'omics', 'finspace', 'deadline', 'datasync', 'drs', 'mgn', 'ebs',
    'rds', 'redshift', 'elasticbeanstalk', 'cloudshell', 'ssm-quicksetup',
]

for prefix in key_uncovered:
    svc = svc_map.get(prefix)
    if not svc: continue
    write_privs = [
        p for p in svc.get('privileges', [])
        if p.get('access_level') in ('Write', 'Permissions management')
    ]
    if not write_privs: continue
    print(f"\n[{prefix}] {svc.get('service_name','')} — {len(write_privs)} write actions:")
    for p in write_privs:
        action = p.get('privilege', '')
        desc = p.get('description', '')[:100]
        # Mark resource types
        rts = [rt.get('resource_type','').rstrip('*') for rt in p.get('resource_types', []) if rt.get('resource_type','')]
        rt_str = f" [res: {','.join(rts)}]" if rts else ""
        print(f"    {prefix}:{action}{rt_str}: {desc}")
