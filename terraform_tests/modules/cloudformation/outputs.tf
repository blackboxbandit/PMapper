output "scenario_summary" {
  value = merge(
    local.s8_1 ? { "8.1" = {
      name     = "CloudFormation-CreateStack"
      attacker = aws_iam_user.attacker_8_1[0].arn
      target   = aws_iam_role.cf_target_role[0].arn
      edge     = "can create a stack in CloudFormation to access"
    }} : {},
    local.s8_2 ? { "8.2" = {
      name     = "CloudFormation-UpdateStack"
      attacker = aws_iam_user.attacker_8_2[0].arn
      target   = aws_iam_role.cf_target_role[0].arn
      edge     = "can update the CloudFormation stack to access"
    }} : {},
  )
}
