output "scenario_summary" {
  value = merge(
    local.s5_1 ? { "5.1" = {
      name     = "SageMaker-Notebook"
      attacker = aws_iam_user.attacker_5_1[0].arn
      target   = aws_iam_role.sagemaker_target_role[0].arn
      edge     = "can use SageMaker to launch a notebook and access"
    }} : {},
    local.s5_2 ? { "5.2" = {
      name     = "SageMaker-TrainingJob"
      attacker = aws_iam_user.attacker_5_2[0].arn
      target   = aws_iam_role.sagemaker_target_role[0].arn
      edge     = "can use SageMaker to create a training job and access"
    }} : {},
    local.s5_3 ? { "5.3" = {
      name     = "SageMaker-ProcessingJob"
      attacker = aws_iam_user.attacker_5_3[0].arn
      target   = aws_iam_role.sagemaker_target_role[0].arn
      edge     = "can use SageMaker to create a processing job and access"
    }} : {},
  )
}
