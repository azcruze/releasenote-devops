# Authentication: run `az login` first (Terraform uses the Azure CLI session).
# AzureRM 4.x needs the subscription ID. Supply it with the ARM_SUBSCRIPTION_ID
# environment variable (preferred) or the subscription_id variable. Never hardcode it in Git.
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
