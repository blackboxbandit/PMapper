###############################################################################
# Global Variables
###############################################################################

variable "aws_region" {
  description = "AWS region to deploy test resources"
  type        = string
  default     = "eu-west-2"
}

variable "name_prefix" {
  description = "Prefix for all resource names to avoid collisions"
  type        = string
  default     = "pmapper-test"
}

###############################################################################
# Per-Group Enable Flags
###############################################################################

variable "enable_iam" {
  description = "Enable Section 1: IAM scenarios"
  type        = bool
  default     = false
}

variable "enable_sts" {
  description = "Enable Section 2: STS scenarios"
  type        = bool
  default     = false
}

variable "enable_ec2" {
  description = "Enable Section 3: EC2 scenarios"
  type        = bool
  default     = false
}

variable "enable_lambda" {
  description = "Enable Section 4: Lambda scenarios"
  type        = bool
  default     = false
}

variable "enable_sagemaker" {
  description = "Enable Section 5: SageMaker scenarios"
  type        = bool
  default     = false
}

variable "enable_ssm" {
  description = "Enable Section 6: SSM scenarios"
  type        = bool
  default     = false
}

variable "enable_codebuild" {
  description = "Enable Section 7: CodeBuild scenarios"
  type        = bool
  default     = false
}

variable "enable_cloudformation" {
  description = "Enable Section 8: CloudFormation scenarios"
  type        = bool
  default     = false
}

variable "enable_autoscaling" {
  description = "Enable Section 9: AutoScaling scenarios"
  type        = bool
  default     = false
}

variable "enable_glue" {
  description = "Enable Section 10: Glue scenarios"
  type        = bool
  default     = false
}

###############################################################################
# Per-Group Scenario Lists
###############################################################################

variable "iam_scenarios" {
  description = "List of IAM scenario IDs to enable (e.g. [\"1.1\", \"1.2\"]). Empty = all."
  type        = list(string)
  default     = []
}

variable "sts_scenarios" {
  description = "List of STS scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "ec2_scenarios" {
  description = "List of EC2 scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "lambda_scenarios" {
  description = "List of Lambda scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "sagemaker_scenarios" {
  description = "List of SageMaker scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "ssm_scenarios" {
  description = "List of SSM scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "codebuild_scenarios" {
  description = "List of CodeBuild scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "cloudformation_scenarios" {
  description = "List of CloudFormation scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "autoscaling_scenarios" {
  description = "List of AutoScaling scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}

variable "glue_scenarios" {
  description = "List of Glue scenario IDs to enable. Empty = all."
  type        = list(string)
  default     = []
}
