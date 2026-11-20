variable "name" { type = string }
variable "vpc_cidr" { type = string }
variable "availability_zones" { type = number }
variable "api_allowed_cidrs" { type = list(string) }
