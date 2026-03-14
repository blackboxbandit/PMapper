output "scenario_summary" {
  value = merge(
    local.s3_1 ? { "3.1" = {
      name     = "EC2-RunInstances-ExistingIP"
      attacker = aws_iam_user.attacker_3_1[0].arn
      target   = aws_iam_role.ec2_target_role[0].arn
      edge     = "can use EC2 to run an instance with an existing instance profile to access"
    }} : {},
    local.s3_2 ? { "3.2" = {
      name     = "EC2-RunInstances-NewIP"
      attacker = aws_iam_user.attacker_3_2[0].arn
      target   = aws_iam_role.ec2_target_role[0].arn
      edge     = "can use EC2 to run an instance with a newly created instance profile to access"
    }} : {},
  )
}
