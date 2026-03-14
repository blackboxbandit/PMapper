output "scenario_summary" {
  description = "Summary of deployed IAM scenarios"
  value = merge(
    local.s1_1 ? { "1.1" = {
      name     = "CreateAccessKey"
      attacker = aws_iam_user.attacker_1_1[0].arn
      target   = aws_iam_user.target_user[0].arn
      edge     = "can create access keys to authenticate as"
    }} : {},
    local.s1_2 ? { "1.2" = {
      name     = "UpdateLoginProfile"
      attacker = aws_iam_user.attacker_1_2[0].arn
      target   = aws_iam_user.target_user[0].arn
      edge     = "can set the password to authenticate as"
    }} : {},
    local.s1_3 ? { "1.3" = {
      name     = "PutUserPolicy"
      attacker = aws_iam_user.attacker_1_3[0].arn
      target   = aws_iam_user.target_user[0].arn
      edge     = "can add inline policies to"
    }} : {},
    local.s1_4 ? { "1.4" = {
      name     = "AttachUserPolicy"
      attacker = aws_iam_user.attacker_1_4[0].arn
      target   = aws_iam_user.target_user[0].arn
      edge     = "can attach managed policies to"
    }} : {},
    local.s1_5 ? { "1.5" = {
      name     = "PutGroupPolicy"
      attacker = aws_iam_user.attacker_1_5[0].arn
      target   = aws_iam_user.target_user[0].arn
      edge     = "can add inline policies to the group which contains"
    }} : {},
    local.s1_6 ? { "1.6" = {
      name     = "AttachGroupPolicy"
      attacker = aws_iam_user.attacker_1_6[0].arn
      target   = aws_iam_user.target_user[0].arn
      edge     = "can attach managed policies to the group which contains"
    }} : {},
    local.s1_7 ? { "1.7" = {
      name     = "UpdateAssumeRolePolicy"
      attacker = aws_iam_user.attacker_1_7[0].arn
      target   = aws_iam_role.target_role[0].arn
      edge     = "can update the trust document to access"
    }} : {},
    local.s1_8 ? { "1.8" = {
      name     = "PutRolePolicy"
      attacker = aws_iam_user.attacker_1_8[0].arn
      target   = aws_iam_role.target_role[0].arn
      edge     = "can add inline policies to"
    }} : {},
    local.s1_9 ? { "1.9" = {
      name     = "AttachRolePolicy"
      attacker = aws_iam_user.attacker_1_9[0].arn
      target   = aws_iam_role.target_role[0].arn
      edge     = "can attach managed policies to"
    }} : {},
  )
}
