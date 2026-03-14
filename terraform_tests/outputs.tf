###############################################################################
# Aggregated Outputs
###############################################################################

output "iam_scenarios" {
  description = "IAM scenario outputs"
  value       = var.enable_iam ? module.iam[0].scenario_summary : {}
}

output "sts_scenarios" {
  description = "STS scenario outputs"
  value       = var.enable_sts ? module.sts[0].scenario_summary : {}
}

output "ec2_scenarios" {
  description = "EC2 scenario outputs"
  value       = var.enable_ec2 ? module.ec2[0].scenario_summary : {}
}

output "lambda_scenarios" {
  description = "Lambda scenario outputs"
  value       = var.enable_lambda ? module.lambda[0].scenario_summary : {}
}

output "sagemaker_scenarios" {
  description = "SageMaker scenario outputs"
  value       = var.enable_sagemaker ? module.sagemaker[0].scenario_summary : {}
}

output "ssm_scenarios" {
  description = "SSM scenario outputs"
  value       = var.enable_ssm ? module.ssm[0].scenario_summary : {}
}

output "codebuild_scenarios" {
  description = "CodeBuild scenario outputs"
  value       = var.enable_codebuild ? module.codebuild[0].scenario_summary : {}
}

output "cloudformation_scenarios" {
  description = "CloudFormation scenario outputs"
  value       = var.enable_cloudformation ? module.cloudformation[0].scenario_summary : {}
}

output "autoscaling_scenarios" {
  description = "AutoScaling scenario outputs"
  value       = var.enable_autoscaling ? module.autoscaling[0].scenario_summary : {}
}

output "glue_scenarios" {
  description = "Glue scenario outputs"
  value       = var.enable_glue ? module.glue[0].scenario_summary : {}
}
