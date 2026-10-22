variable "subscription_id" {
  description = "Azure subscription ID. Leave null to use the ARM_SUBSCRIPTION_ID environment variable."
  type        = string
  default     = null
}

variable "location" {
  description = "Azure region. Pick one where your subscription may create the chosen VM size."
  type        = string
  default     = "centralindia"
}

variable "project_name" {
  description = "Short lowercase name used as a prefix for every resource."
  type        = string
  default     = "releasenote"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project_name))
    error_message = "project_name must be 3-21 characters: lowercase letters, digits and hyphens, starting with a letter."
  }
}

variable "environment" {
  description = "Environment label (dev, test, prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test or prod."
  }
}

variable "vm_size" {
  description = "VM size. Check availability: az vm list-skus --location <region> --size Standard_B --output table"
  type        = string
  default     = "Standard_B2s"
}

variable "admin_username" {
  description = "Linux administrator account created on the VM."
  type        = string
  default     = "azureuser"

  validation {
    condition     = !contains(["root", "admin", "administrator"], lower(var.admin_username))
    error_message = "Choose an administrator name other than root/admin/administrator."
  }
}

variable "ssh_public_key_path" {
  description = "Path to the SSH PUBLIC key (.pub). The private key never enters Terraform."
  type        = string
  default     = "~/.ssh/releasenote_azure.pub"

  validation {
    condition     = fileexists(pathexpand(var.ssh_public_key_path))
    error_message = "SSH public key file not found. Generate one with ssh-keygen (see README)."
  }
}

variable "ssh_allowed_cidrs" {
  description = "CIDR ranges allowed to reach SSH (port 22): your IP and the Jenkins server's public IP, e.g. [\"203.0.113.10/32\"]."
  type        = list(string)

  validation {
    condition     = length(var.ssh_allowed_cidrs) > 0 && alltrue([for c in var.ssh_allowed_cidrs : can(cidrnetmask(c))])
    error_message = "Provide at least one valid IPv4 CIDR, e.g. 203.0.113.10/32."
  }

  validation {
    condition     = !contains(var.ssh_allowed_cidrs, "0.0.0.0/0")
    error_message = "SSH must not be open to the whole internet (0.0.0.0/0). Restrict it to specific addresses."
  }
}

variable "enable_https" {
  description = "Open port 443. Enable ONLY after TLS is actually configured on the VM."
  type        = bool
  default     = false
}

variable "vnet_address_space" {
  description = "Virtual network address space."
  type        = list(string)
  default     = ["10.20.0.0/16"]
}

variable "subnet_prefix" {
  description = "Subnet address prefix (must sit inside vnet_address_space)."
  type        = string
  default     = "10.20.1.0/24"
}

variable "os_disk_size_gb" {
  description = "OS disk size in GB."
  type        = number
  default     = 30
}

variable "os_disk_type" {
  description = "OS disk storage type."
  type        = string
  default     = "StandardSSD_LRS"
}

variable "dns_label" {
  description = "Optional unique DNS label giving the VM a name like <label>.<region>.cloudapp.azure.com."
  type        = string
  default     = null
}

variable "extra_tags" {
  description = "Additional tags merged into the standard tag set."
  type        = map(string)
  default     = {}
}
