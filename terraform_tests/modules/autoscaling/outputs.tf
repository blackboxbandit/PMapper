output "scenario_summary" {
  value = merge(
    local.s9_1 ? { "9.1" = {
      name     = "AutoScaling-ExistingLC"
      attacker = aws_iam_user.attacker_9_1[0].arn
      target   = aws_iam_role.as_target_role[0].arn
      edge     = "can use the EC2 Auto Scaling service role and an existing Launch Configuration to access"
    }} : {},
    local.s9_2 ? { "9.2" = {
      name     = "AutoScaling-NewLC"
      attacker = aws_iam_user.attacker_9_2[0].arn
      target   = aws_iam_role.as_target_role[0].arn
      edge     = "can use the EC2 Auto Scaling service role and create a launch configuration to access"
    }} : {},
  )
}
