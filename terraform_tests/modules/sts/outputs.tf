output "scenario_summary" {
  value = merge(
    local.s2_1 ? { "2.1" = {
      name     = "AssumeRole-IdentityPolicy"
      attacker = aws_iam_user.attacker_2_1[0].arn
      target   = aws_iam_role.target_role_2_1[0].arn
      edge     = "can access via sts:AssumeRole"
    }} : {},
    local.s2_2 ? { "2.2" = {
      name     = "AssumeRole-NodeMatch"
      attacker = aws_iam_user.attacker_2_2[0].arn
      target   = aws_iam_role.target_role_2_2[0].arn
      edge     = "can access via sts:AssumeRole"
    }} : {},
  )
}
