###############################################################################
# Section 9: AutoScaling — PassRole to EC2 Auto Scaling Privilege Escalation
###############################################################################
#
# 9.1  CreateAutoScalingGroup with existing LaunchConfig + ServiceLinkedRole
# 9.2  CreateLaunchConfiguration + CreateAutoScalingGroup + PassRole
###############################################################################

locals {
  all_scenarios = ["9.1", "9.2"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s9_1 = contains(local.enabled, "9.1")
  s9_2 = contains(local.enabled, "9.2")
}

# ─── Target role trusting EC2 with instance profile ────────────────────────
resource "aws_iam_role" "as_target_role" {
  count = anytrue([local.s9_1, local.s9_2]) ? 1 : 0
  name  = "${var.name_prefix}-as-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "9.x-AutoScaling-target" }
}

resource "aws_iam_role_policy" "as_target_elevated" {
  count = anytrue([local.s9_1, local.s9_2]) ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.as_target_role[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "iam:List*"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_instance_profile" "as_target" {
  count = anytrue([local.s9_1, local.s9_2]) ? 1 : 0
  name  = "${var.name_prefix}-as-target-ip"
  role  = aws_iam_role.as_target_role[0].name
}

###############################################################################
# 9.1 — CreateAutoScalingGroup + existing LaunchConfig + ServiceLinkedRole
###############################################################################
resource "aws_iam_user" "attacker_9_1" {
  count = local.s9_1 ? 1 : 0
  name  = "${var.name_prefix}-as-9-1-attacker"
  tags  = { Scenario = "9.1-AutoScaling-ExistingLC" }
}

resource "aws_iam_user_policy" "attacker_9_1" {
  count = local.s9_1 ? 1 : 0
  name  = "autoscaling-create-asg-slr"
  user  = aws_iam_user.attacker_9_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "autoscaling:CreateAutoScalingGroup"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:CreateServiceLinkedRole"
        Resource = "*"
        Condition = {
          StringEquals = { "iam:AWSServiceName" = "autoscaling.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 9.2 — CreateLaunchConfiguration + CreateAutoScalingGroup + PassRole
###############################################################################
resource "aws_iam_user" "attacker_9_2" {
  count = local.s9_2 ? 1 : 0
  name  = "${var.name_prefix}-as-9-2-attacker"
  tags  = { Scenario = "9.2-AutoScaling-NewLC" }
}

resource "aws_iam_user_policy" "attacker_9_2" {
  count = local.s9_2 ? 1 : 0
  name  = "autoscaling-create-lc-asg-passrole"
  user  = aws_iam_user.attacker_9_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:CreateLaunchConfiguration",
          "autoscaling:CreateAutoScalingGroup"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.as_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "ec2.amazonaws.com" }
        }
      },
      {
        Effect   = "Allow"
        Action   = "iam:CreateServiceLinkedRole"
        Resource = "*"
        Condition = {
          StringEquals = { "iam:AWSServiceName" = "autoscaling.amazonaws.com" }
        }
      }
    ]
  })
}
