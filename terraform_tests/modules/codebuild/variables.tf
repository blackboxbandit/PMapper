variable "name_prefix" {
  type = string
}

variable "account_id" {
  type = string
}

variable "scenarios" {
  type    = list(string)
  default = []
}
