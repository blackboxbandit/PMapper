###############################################################################
# Section 10: Glue — PassRole to Glue Privilege Escalation
###############################################################################
#
# 10.1  CreateDevEndpoint + PassRole
# 10.2  UpdateDevEndpoint + PassRole
###############################################################################

locals {
  all_scenarios = ["10.1", "10.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s10_1 = contains(local.enabled, "10.1")
  s10_2 = contains(local.enabled, "10.2")
}

# ─── Target role trusting Glue ─────────────────────────────────────────────
resource "aws_iam_role" "glue_target_role" {
  count = anytrue([local.s10_1, local.s10_2]) ? 1 : 0
  name  = "${var.name_prefix}-glue-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "10.x-Glue-target" }
}

resource "aws_iam_role_policy" "glue_target_elevated" {
  count = anytrue([local.s10_1, local.s10_2]) ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.glue_target_role[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "iam:List*"]
      Resource = "*"
    }]
  })
}

###############################################################################
# 10.1 — CreateDevEndpoint + PassRole
###############################################################################
resource "aws_iam_user" "attacker_10_1" {
  count = local.s10_1 ? 1 : 0
  name  = "${var.name_prefix}-glue-10-1-attacker"
  tags  = { Scenario = "10.1-Glue-CreateDevEndpoint" }
}

resource "aws_iam_user_policy" "attacker_10_1" {
  count = local.s10_1 ? 1 : 0
  name  = "glue-create-endpoint-passrole"
  user  = aws_iam_user.attacker_10_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "glue:CreateDevEndpoint"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.glue_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "glue.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 10.2 — UpdateDevEndpoint + PassRole
###############################################################################
resource "aws_iam_user" "attacker_10_2" {
  count = local.s10_2 ? 1 : 0
  name  = "${var.name_prefix}-glue-10-2-attacker"
  tags  = { Scenario = "10.2-Glue-UpdateDevEndpoint" }
}

resource "aws_iam_user_policy" "attacker_10_2" {
  count = local.s10_2 ? 1 : 0
  name  = "glue-update-endpoint-passrole"
  user  = aws_iam_user.attacker_10_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "glue:UpdateDevEndpoint"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.glue_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "glue.amazonaws.com" }
        }
      }
    ]
  })
}
