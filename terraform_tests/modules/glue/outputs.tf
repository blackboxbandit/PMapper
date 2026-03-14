output "scenario_summary" {
  value = merge(
    local.s10_1 ? { "10.1" = {
      name     = "Glue-CreateDevEndpoint"
      attacker = aws_iam_user.attacker_10_1[0].arn
      target   = aws_iam_role.glue_target_role[0].arn
      edge     = "can execute glue:CreateDevEndpoint and pass the role to glue.amazonaws.com"
    }} : {},
    local.s10_2 ? { "10.2" = {
      name     = "Glue-UpdateDevEndpoint"
      attacker = aws_iam_user.attacker_10_2[0].arn
      target   = aws_iam_role.glue_target_role[0].arn
      edge     = "can execute glue:UpdateDevEndpoint and pass the role to glue.amazonaws.com"
    }} : {},
  )
}
