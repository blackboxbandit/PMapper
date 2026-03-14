###############################################################################
# Section 3: EC2 — PassRole to EC2 Privilege Escalation
###############################################################################
#
# 3.1  RunInstances + PassRole (existing instance profile)
# 3.2  RunInstances + AssociateIamInstanceProfile + CreateInstanceProfile
###############################################################################

locals {
  all_scenarios = ["3.1", "3.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s3_1 = contains(local.enabled, "3.1")
  s3_2 = contains(local.enabled, "3.2")
}

# ─── Target role trusting EC2 ──────────────────────────────────────────────
resource "aws_iam_role" "ec2_target_role" {
  count = anytrue([local.s3_1, local.s3_2]) ? 1 : 0
  name  = "${var.name_prefix}-ec2-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "3.x-EC2-target" }
}

resource "aws_iam_role_policy" "ec2_target_elevated" {
  count = anytrue([local.s3_1, local.s3_2]) ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.ec2_target_role[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "iam:List*"]
      Resource = "*"
    }]
  })
}

# Instance profile for 3.1
resource "aws_iam_instance_profile" "ec2_target" {
  count = local.s3_1 ? 1 : 0
  name  = "${var.name_prefix}-ec2-target-ip"
  role  = aws_iam_role.ec2_target_role[0].name
}

###############################################################################
# 3.1 — RunInstances + PassRole with existing instance profile
###############################################################################
resource "aws_iam_user" "attacker_3_1" {
  count = local.s3_1 ? 1 : 0
  name  = "${var.name_prefix}-ec2-3-1-attacker"
  tags  = { Scenario = "3.1-EC2-RunInstances-ExistingIP" }
}

resource "aws_iam_user_policy" "attacker_3_1" {
  count = local.s3_1 ? 1 : 0
  name  = "ec2-run-instances-passrole"
  user  = aws_iam_user.attacker_3_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ec2:RunInstances"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.ec2_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "ec2.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 3.2 — RunInstances + AssociateIamInstanceProfile (no existing IP)
###############################################################################
resource "aws_iam_user" "attacker_3_2" {
  count = local.s3_2 ? 1 : 0
  name  = "${var.name_prefix}-ec2-3-2-attacker"
  tags  = { Scenario = "3.2-EC2-RunInstances-NewIP" }
}

resource "aws_iam_user_policy" "attacker_3_2" {
  count = local.s3_2 ? 1 : 0
  name  = "ec2-run-associate-passrole"
  user  = aws_iam_user.attacker_3_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ec2:RunInstances", "ec2:AssociateIamInstanceProfile"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole", "iam:CreateInstanceProfile", "iam:AddRoleToInstanceProfile"]
        Resource = aws_iam_role.ec2_target_role[0].arn
      }
    ]
  })
}
