output "scenario_summary" {
  value = merge(
    local.s4_1 ? { "4.1" = {
      name     = "Lambda-CreateFunction"
      attacker = aws_iam_user.attacker_4_1[0].arn
      target   = aws_iam_role.lambda_target_role[0].arn
      edge     = "can use Lambda to create a new function with arbitrary code, then pass and access"
    }} : {},
    local.s4_2 ? { "4.2" = {
      name     = "Lambda-UpdateFunctionCode"
      attacker = aws_iam_user.attacker_4_2[0].arn
      target   = aws_iam_role.lambda_target_role[0].arn
      edge     = "can use Lambda to edit an existing function to access"
    }} : {},
  )
}
