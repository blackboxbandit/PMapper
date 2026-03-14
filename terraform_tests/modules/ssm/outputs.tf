output "scenario_summary" {
  value = merge(
    local.s6_1 ? { "6.1" = {
      name     = "SSM-SendCommand"
      attacker = aws_iam_user.attacker_6_1[0].arn
      target   = aws_iam_role.ssm_target_role[0].arn
      edge     = "can call ssm:SendCommand to access an EC2 instance with access to"
    }} : {},
    local.s6_2 ? { "6.2" = {
      name     = "SSM-StartSession"
      attacker = aws_iam_user.attacker_6_2[0].arn
      target   = aws_iam_role.ssm_target_role[0].arn
      edge     = "can call ssm:StartSession to access an EC2 instance with access to"
    }} : {},
  )
}
