output "scenario_summary" {
  value = merge(
    local.s7_1 ? { "7.1" = {
      name     = "CodeBuild-CreateProject"
      attacker = aws_iam_user.attacker_7_1[0].arn
      target   = aws_iam_role.codebuild_target_role[0].arn
      edge     = "can create a project in CodeBuild to access"
    }} : {},
    local.s7_2 ? { "7.2" = {
      name     = "CodeBuild-UpdateProject"
      attacker = aws_iam_user.attacker_7_2[0].arn
      target   = aws_iam_role.codebuild_target_role[0].arn
      edge     = "can update a project in CodeBuild to access"
    }} : {},
  )
}
