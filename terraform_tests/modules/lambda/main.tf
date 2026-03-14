###############################################################################
# Section 4: Lambda — PassRole to Lambda Privilege Escalation
###############################################################################
#
# 4.1  CreateFunction + PassRole — attacker creates new Lambda with target role
# 4.2  UpdateFunctionCode — attacker modifies existing Lambda with target role
###############################################################################

locals {
  all_scenarios = ["4.1", "4.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s4_1 = contains(local.enabled, "4.1")
  s4_2 = contains(local.enabled, "4.2")
}

# ─── Target role trusting Lambda ───────────────────────────────────────────
resource "aws_iam_role" "lambda_target_role" {
  count = anytrue([local.s4_1, local.s4_2]) ? 1 : 0
  name  = "${var.name_prefix}-lambda-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "4.x-Lambda-target" }
}

resource "aws_iam_role_policy" "lambda_target_elevated" {
  count = anytrue([local.s4_1, local.s4_2]) ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.lambda_target_role[0].name

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
# 4.1 — CreateFunction + PassRole
###############################################################################
resource "aws_iam_user" "attacker_4_1" {
  count = local.s4_1 ? 1 : 0
  name  = "${var.name_prefix}-lambda-4-1-attacker"
  tags  = { Scenario = "4.1-Lambda-CreateFunction" }
}

resource "aws_iam_user_policy" "attacker_4_1" {
  count = local.s4_1 ? 1 : 0
  name  = "lambda-create-passrole"
  user  = aws_iam_user.attacker_4_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:CreateFunction", "lambda:InvokeFunction"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.lambda_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "lambda.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 4.2 — UpdateFunctionCode on existing function
###############################################################################
resource "aws_iam_user" "attacker_4_2" {
  count = local.s4_2 ? 1 : 0
  name  = "${var.name_prefix}-lambda-4-2-attacker"
  tags  = { Scenario = "4.2-Lambda-UpdateFunctionCode" }
}

resource "aws_iam_user_policy" "attacker_4_2" {
  count = local.s4_2 ? 1 : 0
  name  = "lambda-update-code"
  user  = aws_iam_user.attacker_4_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["lambda:UpdateFunctionCode", "lambda:InvokeFunction"]
      Resource = "*"
    }]
  })
}
