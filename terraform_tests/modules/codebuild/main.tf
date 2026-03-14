###############################################################################
# Section 7: CodeBuild — PassRole to CodeBuild Privilege Escalation
###############################################################################
#
# 7.1  CreateProject + StartBuild + PassRole
# 7.2  UpdateProject + StartBuild + PassRole
###############################################################################

locals {
  all_scenarios = ["7.1", "7.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s7_1 = contains(local.enabled, "7.1")
  s7_2 = contains(local.enabled, "7.2")
}

# ─── Target role trusting CodeBuild ────────────────────────────────────────
resource "aws_iam_role" "codebuild_target_role" {
  count = anytrue([local.s7_1, local.s7_2]) ? 1 : 0
  name  = "${var.name_prefix}-cb-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "codebuild.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "7.x-CodeBuild-target" }
}

resource "aws_iam_role_policy" "codebuild_target_elevated" {
  count = anytrue([local.s7_1, local.s7_2]) ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.codebuild_target_role[0].name

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
# 7.1 — CreateProject + StartBuild + PassRole
###############################################################################
resource "aws_iam_user" "attacker_7_1" {
  count = local.s7_1 ? 1 : 0
  name  = "${var.name_prefix}-cb-7-1-attacker"
  tags  = { Scenario = "7.1-CodeBuild-CreateProject" }
}

resource "aws_iam_user_policy" "attacker_7_1" {
  count = local.s7_1 ? 1 : 0
  name  = "codebuild-create-start-passrole"
  user  = aws_iam_user.attacker_7_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["codebuild:CreateProject", "codebuild:StartBuild"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.codebuild_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "codebuild.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 7.2 — UpdateProject + StartBuild + PassRole
###############################################################################
resource "aws_iam_user" "attacker_7_2" {
  count = local.s7_2 ? 1 : 0
  name  = "${var.name_prefix}-cb-7-2-attacker"
  tags  = { Scenario = "7.2-CodeBuild-UpdateProject" }
}

resource "aws_iam_user_policy" "attacker_7_2" {
  count = local.s7_2 ? 1 : 0
  name  = "codebuild-update-start-passrole"
  user  = aws_iam_user.attacker_7_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["codebuild:UpdateProject", "codebuild:StartBuild"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.codebuild_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "codebuild.amazonaws.com" }
        }
      }
    ]
  })
}
