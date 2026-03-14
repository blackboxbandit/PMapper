###############################################################################
# Section 5: SageMaker — PassRole to SageMaker Privilege Escalation
###############################################################################
#
# 5.1  CreateNotebookInstance + PassRole
# 5.2  CreateTrainingJob + PassRole
# 5.3  CreateProcessingJob + PassRole
###############################################################################

locals {
  all_scenarios = ["5.1", "5.2", "5.3"]
  enabled       = length(var.scenarios) == 0 ? local.all_scenarios : var.scenarios

  s5_1 = contains(local.enabled, "5.1")
  s5_2 = contains(local.enabled, "5.2")
  s5_3 = contains(local.enabled, "5.3")
}

# ─── Target role trusting SageMaker ────────────────────────────────────────
resource "aws_iam_role" "sagemaker_target_role" {
  count = anytrue([local.s5_1, local.s5_2, local.s5_3]) ? 1 : 0
  name  = "${var.name_prefix}-sagemaker-target-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sagemaker.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Scenario = "5.x-SageMaker-target" }
}

resource "aws_iam_role_policy" "sagemaker_target_elevated" {
  count = anytrue([local.s5_1, local.s5_2, local.s5_3]) ? 1 : 0
  name  = "elevated-permissions"
  role  = aws_iam_role.sagemaker_target_role[0].name

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
# 5.1 — CreateNotebookInstance + PassRole
###############################################################################
resource "aws_iam_user" "attacker_5_1" {
  count = local.s5_1 ? 1 : 0
  name  = "${var.name_prefix}-sm-5-1-attacker"
  tags  = { Scenario = "5.1-SageMaker-Notebook" }
}

resource "aws_iam_user_policy" "attacker_5_1" {
  count = local.s5_1 ? 1 : 0
  name  = "sagemaker-notebook-passrole"
  user  = aws_iam_user.attacker_5_1[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sagemaker:CreateNotebookInstance", "sagemaker:CreatePresignedNotebookInstanceUrl"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.sagemaker_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "sagemaker.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 5.2 — CreateTrainingJob + PassRole
###############################################################################
resource "aws_iam_user" "attacker_5_2" {
  count = local.s5_2 ? 1 : 0
  name  = "${var.name_prefix}-sm-5-2-attacker"
  tags  = { Scenario = "5.2-SageMaker-TrainingJob" }
}

resource "aws_iam_user_policy" "attacker_5_2" {
  count = local.s5_2 ? 1 : 0
  name  = "sagemaker-training-passrole"
  user  = aws_iam_user.attacker_5_2[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sagemaker:CreateTrainingJob"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.sagemaker_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "sagemaker.amazonaws.com" }
        }
      }
    ]
  })
}

###############################################################################
# 5.3 — CreateProcessingJob + PassRole
###############################################################################
resource "aws_iam_user" "attacker_5_3" {
  count = local.s5_3 ? 1 : 0
  name  = "${var.name_prefix}-sm-5-3-attacker"
  tags  = { Scenario = "5.3-SageMaker-ProcessingJob" }
}

resource "aws_iam_user_policy" "attacker_5_3" {
  count = local.s5_3 ? 1 : 0
  name  = "sagemaker-processing-passrole"
  user  = aws_iam_user.attacker_5_3[0].name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sagemaker:CreateProcessingJob"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = aws_iam_role.sagemaker_target_role[0].arn
        Condition = {
          StringEquals = { "iam:PassedToService" = "sagemaker.amazonaws.com" }
        }
      }
    ]
  })
}
