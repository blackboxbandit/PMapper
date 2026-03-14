###############################################################################
# Section 1: IAM — Direct IAM Privilege Escalation Scenarios
###############################################################################
#
# 1.1  CreateAccessKey         — User A can create access keys for User B
# 1.2  UpdateLoginProfile      — User A can set password for User B
# 1.3  PutUserPolicy           — User A can add inline policy to User B
# 1.4  AttachUserPolicy        — User A can attach managed policy to User B
# 1.5  PutGroupPolicy          — User A can add inline policy to Group containing User B
# 1.6  AttachGroupPolicy       — User A can attach managed policy to Group containing User B
# 1.7  UpdateAssumeRolePolicy  — User A can update trust policy of Role B
# 1.8  PutRolePolicy           — User A can add inline policy to Role B
# 1.9  AttachRolePolicy        — User A can attach managed policy to Role B
###############################################################################

locals {
  all_scenarios = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s1_1 = contains(local.enabled, "1.1")
  s1_2 = contains(local.enabled, "1.2")
  s1_3 = contains(local.enabled, "1.3")
  s1_4 = contains(local.enabled, "1.4")
  s1_5 = contains(local.enabled, "1.5")
  s1_6 = contains(local.enabled, "1.6")
  s1_7 = contains(local.enabled, "1.7")
  s1_8 = contains(local.enabled, "1.8")
  s1_9 = contains(local.enabled, "1.9")
}

# ─── Shared target user for scenarios 1.1–1.6 ──────────────────────────────
resource "aws_iam_user" "target_user" {
  count = anytrue([local.s1_1, local.s1_2, local.s1_3, local.s1_4, local.s1_5, local.s1_6]) ? 1 : 0
  name  = "${var.name_prefix}-iam-target-user"

  tags = { Scenario = "1.x-target" }
}

# Give the target user a login profile so UpdateLoginProfile path works
resource "aws_iam_user_login_profile" "target_user_login" {
  count                   = local.s1_2 ? 1 : 0
  user                    = aws_iam_user.target_user[0].name
  password_reset_required = false
}

# ─── Shared target role for scenarios 1.7–1.9 ──────────────────────────────
resource "aws_iam_role" "target_role" {
  count = anytrue([local.s1_7, local.s1_8, local.s1_9]) ? 1 : 0
  name  = "${var.name_prefix}-iam-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${var.account_id}:root" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "1.x-target" }
}

# ─── Shared group for scenarios 1.5–1.6 ────────────────────────────────────
resource "aws_iam_group" "target_group" {
  count = anytrue([local.s1_5, local.s1_6]) ? 1 : 0
  name  = "${var.name_prefix}-iam-target-group"
}

resource "aws_iam_group_membership" "target_group_membership" {
  count = anytrue([local.s1_5, local.s1_6]) ? 1 : 0
  name  = "${var.name_prefix}-iam-target-group-membership"
  group = aws_iam_group.target_group[0].name
  users = [aws_iam_user.target_user[0].name]
}

###############################################################################
# 1.1 — CreateAccessKey
###############################################################################
resource "aws_iam_user" "attacker_1_1" {
  count = local.s1_1 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-1-attacker"
  tags  = { Scenario = "1.1-CreateAccessKey" }
}

resource "aws_iam_user_policy" "attacker_1_1" {
  count = local.s1_1 ? 1 : 0
  name  = "create-access-key"
  user  = aws_iam_user.attacker_1_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["iam:CreateAccessKey", "iam:DeleteAccessKey"]
      Resource = aws_iam_user.target_user[0].arn
    }]
  })
}

###############################################################################
# 1.2 — UpdateLoginProfile
###############################################################################
resource "aws_iam_user" "attacker_1_2" {
  count = local.s1_2 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-2-attacker"
  tags  = { Scenario = "1.2-UpdateLoginProfile" }
}

resource "aws_iam_user_policy" "attacker_1_2" {
  count = local.s1_2 ? 1 : 0
  name  = "update-login-profile"
  user  = aws_iam_user.attacker_1_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["iam:UpdateLoginProfile", "iam:CreateLoginProfile"]
      Resource = aws_iam_user.target_user[0].arn
    }]
  })
}

###############################################################################
# 1.3 — PutUserPolicy
###############################################################################
resource "aws_iam_user" "attacker_1_3" {
  count = local.s1_3 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-3-attacker"
  tags  = { Scenario = "1.3-PutUserPolicy" }
}

resource "aws_iam_user_policy" "attacker_1_3" {
  count = local.s1_3 ? 1 : 0
  name  = "put-user-policy"
  user  = aws_iam_user.attacker_1_3[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:PutUserPolicy"
      Resource = aws_iam_user.target_user[0].arn
    }]
  })
}

###############################################################################
# 1.4 — AttachUserPolicy
###############################################################################
resource "aws_iam_user" "attacker_1_4" {
  count = local.s1_4 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-4-attacker"
  tags  = { Scenario = "1.4-AttachUserPolicy" }
}

resource "aws_iam_user_policy" "attacker_1_4" {
  count = local.s1_4 ? 1 : 0
  name  = "attach-user-policy"
  user  = aws_iam_user.attacker_1_4[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:AttachUserPolicy"
      Resource = aws_iam_user.target_user[0].arn
    }]
  })
}

###############################################################################
# 1.5 — PutGroupPolicy
###############################################################################
resource "aws_iam_user" "attacker_1_5" {
  count = local.s1_5 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-5-attacker"
  tags  = { Scenario = "1.5-PutGroupPolicy" }
}

resource "aws_iam_user_policy" "attacker_1_5" {
  count = local.s1_5 ? 1 : 0
  name  = "put-group-policy"
  user  = aws_iam_user.attacker_1_5[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:PutGroupPolicy"
      Resource = aws_iam_group.target_group[0].arn
    }]
  })
}

###############################################################################
# 1.6 — AttachGroupPolicy
###############################################################################
resource "aws_iam_user" "attacker_1_6" {
  count = local.s1_6 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-6-attacker"
  tags  = { Scenario = "1.6-AttachGroupPolicy" }
}

resource "aws_iam_user_policy" "attacker_1_6" {
  count = local.s1_6 ? 1 : 0
  name  = "attach-group-policy"
  user  = aws_iam_user.attacker_1_6[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:AttachGroupPolicy"
      Resource = aws_iam_group.target_group[0].arn
    }]
  })
}

###############################################################################
# 1.7 — UpdateAssumeRolePolicy
###############################################################################
resource "aws_iam_user" "attacker_1_7" {
  count = local.s1_7 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-7-attacker"
  tags  = { Scenario = "1.7-UpdateAssumeRolePolicy" }
}

resource "aws_iam_user_policy" "attacker_1_7" {
  count = local.s1_7 ? 1 : 0
  name  = "update-assume-role-policy"
  user  = aws_iam_user.attacker_1_7[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:UpdateAssumeRolePolicy"
      Resource = aws_iam_role.target_role[0].arn
    }]
  })
}

###############################################################################
# 1.8 — PutRolePolicy
###############################################################################
resource "aws_iam_user" "attacker_1_8" {
  count = local.s1_8 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-8-attacker"
  tags  = { Scenario = "1.8-PutRolePolicy" }
}

resource "aws_iam_user_policy" "attacker_1_8" {
  count = local.s1_8 ? 1 : 0
  name  = "put-role-policy"
  user  = aws_iam_user.attacker_1_8[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:PutRolePolicy"
      Resource = aws_iam_role.target_role[0].arn
    }]
  })
}

###############################################################################
# 1.9 — AttachRolePolicy
###############################################################################
resource "aws_iam_user" "attacker_1_9" {
  count = local.s1_9 ? 1 : 0
  name  = "${var.name_prefix}-iam-1-9-attacker"
  tags  = { Scenario = "1.9-AttachRolePolicy" }
}

resource "aws_iam_user_policy" "attacker_1_9" {
  count = local.s1_9 ? 1 : 0
  name  = "attach-role-policy"
  user  = aws_iam_user.attacker_1_9[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:AttachRolePolicy"
      Resource = aws_iam_role.target_role[0].arn
    }]
  })
}
