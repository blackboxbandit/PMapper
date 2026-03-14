###############################################################################
# Section 8: CloudFormation — PassRole to CloudFormation Privilege Escalation
###############################################################################
#
# 8.1  CreateStack + PassRole
# 8.2  UpdateStack + PassRole
###############################################################################

locals {
  all_scenarios = ["8.1", "8.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s8_1 = contains(local.enabled, "8.1")
  s8_2 = contains(local.enabled, "8.2")
}

# ─── Target role trusting CloudFormation ───────────────────────────────────
resource "aws_iam_role" "cf_target_role" {
  count = anytrue([local.s8_1, local.s8_2]) ? 1 : 0
  name  = "${var.name_prefix}-cf-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "cloudformation.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "8.x-CloudFormation-target" }
}

resource "aws_iam_role_policy" "cf_target_elevated" {
  count = anytrue([local.s8_1, local.s8_2]) ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.cf_target_role[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "iam:*", "ec2:*"]
      Resource = "*"
    }]
  })
}

###############################################################################
# 8.1 — CreateStack + PassRole
###############################################################################
resource "aws_iam_user" "attacker_8_1" {
  count = local.s8_1 ? 1 : 0
  name  = "${var.name_prefix}-cf-8-1-attacker"
  tags  = { Scenario = "8.1-CloudFormation-CreateStack" }
}

resource "aws_iam_user_policy" "attacker_8_1" {
  count = local.s8_1 ? 1 : 0
  name  = "cf-create-stack-passrole"
  user  = aws_iam_user.attacker_8_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "cloudformation:CreateStack"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.cf_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "cloudformation.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 8.2 — UpdateStack + PassRole
###############################################################################
resource "aws_iam_user" "attacker_8_2" {
  count = local.s8_2 ? 1 : 0
  name  = "${var.name_prefix}-cf-8-2-attacker"
  tags  = { Scenario = "8.2-CloudFormation-UpdateStack" }
}

resource "aws_iam_user_policy" "attacker_8_2" {
  count = local.s8_2 ? 1 : 0
  name  = "cf-update-stack-passrole"
  user  = aws_iam_user.attacker_8_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "cloudformation:UpdateStack"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.cf_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "cloudformation.amazonaws.com" }
        }
      }
    ]
  })
}
