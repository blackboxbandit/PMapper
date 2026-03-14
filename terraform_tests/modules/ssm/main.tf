###############################################################################
# Section 6: SSM — SendCommand / StartSession Privilege Escalation
###############################################################################
#
# 6.1  SendCommand — attacker can send commands to EC2 instances running target role
# 6.2  StartSession — attacker can start SSM session to EC2 instances running target role
###############################################################################

locals {
  all_scenarios = ["6.1", "6.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s6_1 = contains(local.enabled, "6.1")
  s6_2 = contains(local.enabled, "6.2")
}

# ─── Target role trusting EC2, with SSM permissions and instance profile ───
resource "aws_iam_role" "ssm_target_role" {
  count = anytrue([local.s6_1, local.s6_2]) ? 1 : 0
  name  = "${var.name_prefix}-ssm-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "6.x-SSM-target" }
}

resource "aws_iam_role_policy" "ssm_target_elevated" {
  count = anytrue([local.s6_1, local.s6_2]) ? 1 : 0
  name  = "elevated-with-ssm"
  role  = aws_iam_role.ssm_target_role[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:*", "iam:List*"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel",
          "ssm:UpdateInstanceInformation"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ssm_target" {
  count = anytrue([local.s6_1, local.s6_2]) ? 1 : 0
  name  = "${var.name_prefix}-ssm-target-ip"
  role  = aws_iam_role.ssm_target_role[0].name
}

###############################################################################
# 6.1 — SendCommand
###############################################################################
resource "aws_iam_user" "attacker_6_1" {
  count = local.s6_1 ? 1 : 0
  name  = "${var.name_prefix}-ssm-6-1-attacker"
  tags  = { Scenario = "6.1-SSM-SendCommand" }
}

resource "aws_iam_user_policy" "attacker_6_1" {
  count = local.s6_1 ? 1 : 0
  name  = "ssm-send-command"
  user  = aws_iam_user.attacker_6_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "ssm:SendCommand"
      Resource = "*"
    }]
  })
}

###############################################################################
# 6.2 — StartSession
###############################################################################
resource "aws_iam_user" "attacker_6_2" {
  count = local.s6_2 ? 1 : 0
  name  = "${var.name_prefix}-ssm-6-2-attacker"
  tags  = { Scenario = "6.2-SSM-StartSession" }
}

resource "aws_iam_user_policy" "attacker_6_2" {
  count = local.s6_2 ? 1 : 0
  name  = "ssm-start-session"
  user  = aws_iam_user.attacker_6_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "ssm:StartSession"
      Resource = "*"
    }]
  })
}
