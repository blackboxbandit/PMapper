###############################################################################
# Root Module — wires each scenario group via conditional modules
###############################################################################

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

# ─── Section 1: IAM ─────────────────────────────────────────────────────────
module "iam" {
  source = "./modules/iam"
  count  = var.enable_iam ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.iam_scenarios
}

# ─── Section 2: STS ─────────────────────────────────────────────────────────
module "sts" {
  source = "./modules/sts"
  count  = var.enable_sts ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.sts_scenarios
}

# ─── Section 3: EC2 ─────────────────────────────────────────────────────────
module "ec2" {
  source = "./modules/ec2"
  count  = var.enable_ec2 ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.ec2_scenarios
}

# ─── Section 4: Lambda ──────────────────────────────────────────────────────
module "lambda" {
  source = "./modules/lambda"
  count  = var.enable_lambda ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.lambda_scenarios
}

# ─── Section 5: SageMaker ───────────────────────────────────────────────────
module "sagemaker" {
  source = "./modules/sagemaker"
  count  = var.enable_sagemaker ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.sagemaker_scenarios
}

# ─── Section 6: SSM ─────────────────────────────────────────────────────────
module "ssm" {
  source = "./modules/ssm"
  count  = var.enable_ssm ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.ssm_scenarios
}

# ─── Section 7: CodeBuild ───────────────────────────────────────────────────
module "codebuild" {
  source = "./modules/codebuild"
  count  = var.enable_codebuild ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.codebuild_scenarios
}

# ─── Section 8: CloudFormation ──────────────────────────────────────────────
module "cloudformation" {
  source = "./modules/cloudformation"
  count  = var.enable_cloudformation ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.cloudformation_scenarios
}

# ─── Section 9: AutoScaling ─────────────────────────────────────────────────
module "autoscaling" {
  source = "./modules/autoscaling"
  count  = var.enable_autoscaling ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.autoscaling_scenarios
}

# ─── Section 10: Glue ───────────────────────────────────────────────────────
module "glue" {
  source = "./modules/glue"
  count  = var.enable_glue ? 1 : 0

  name_prefix = var.name_prefix
  account_id  = local.account_id
  scenarios   = var.glue_scenarios
}
