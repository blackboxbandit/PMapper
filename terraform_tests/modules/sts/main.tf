###############################################################################
# Section 2: STS — AssumeRole Privilege Escalation
###############################################################################
#
# 2.1  AssumeRole (identity policy allows) — User A has sts:AssumeRole; Role B trusts User A
# 2.2  AssumeRole (trust policy NODE_MATCH) — User A has no explicit allow; Role B trusts account root
###############################################################################

locals {
  all_scenarios = ["2.1", "2.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s2_1 = contains(local.enabled, "2.1")
  s2_2 = contains(local.enabled, "2.2")
}

# ─── Target role for 2.1 — trusts a specific user ─────────────────────────
resource "aws_iam_role" "target_role_2_1" {
  count = local.s2_1 ? 1 : 0
  name  = "${var.name_prefix}-sts-2-1-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = aws_iam_user.attacker_2_1[0].arn }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "2.1-AssumeRole-IdentityPolicy" }
}

# Give target role some permissions so it's an interesting escalation target
resource "aws_iam_role_policy" "target_role_2_1" {
  count = local.s2_1 ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.target_role_2_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "ec2:Describe*"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_user" "attacker_2_1" {
  count = local.s2_1 ? 1 : 0
  name  = "${var.name_prefix}-sts-2-1-attacker"
  tags  = { Scenario = "2.1-AssumeRole-IdentityPolicy" }
}

resource "aws_iam_user_policy" "attacker_2_1" {
  count = local.s2_1 ? 1 : 0
  name  = "assume-specific-role"
  user  = aws_iam_user.attacker_2_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sts:AssumeRole"
      Resource = aws_iam_role.target_role_2_1[0].arn
    }]
  })
}

# ─── Target role for 2.2 — trusts account root (NODE_MATCH) ───────────────
resource "aws_iam_role" "target_role_2_2" {
  count = local.s2_2 ? 1 : 0
  name  = "${var.name_prefix}-sts-2-2-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${var.account_id}:root" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "2.2-AssumeRole-NodeMatch" }
}

resource "aws_iam_role_policy" "target_role_2_2" {
  count = local.s2_2 ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.target_role_2_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "ec2:Describe*"]
      Resource = "*"
    }]
  })
}

# Attacker for 2.2 — no sts:AssumeRole in identity policy, relies on trust policy
resource "aws_iam_user" "attacker_2_2" {
  count = local.s2_2 ? 1 : 0
  name  = "${var.name_prefix}-sts-2-2-attacker"
  tags  = { Scenario = "2.2-AssumeRole-NodeMatch" }
}

# Give attacker minimal read-only so they are not totally empty
resource "aws_iam_user_policy" "attacker_2_2" {
  count = local.s2_2 ? 1 : 0
  name  = "minimal-read"
  user  = aws_iam_user.attacker_2_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sts:GetCallerIdentity"
      Resource = "*"
    }]
  })
}
