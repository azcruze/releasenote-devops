output "resource_group_name" {
  description = "Resource group containing every provisioned resource."
  value       = azurerm_resource_group.rg.name
}

output "vm_name" {
  description = "Name of the Linux virtual machine."
  value       = azurerm_linux_virtual_machine.vm.name
}

output "public_ip_address" {
  description = "Public IP of the VM. Store this in the Jenkins credential 'releasenote-vm-host'."
  value       = azurerm_public_ip.pip.ip_address
}

output "deployment_url" {
  description = "Public URL of the application (after the first Jenkins deployment)."
  value       = "http://${azurerm_public_ip.pip.ip_address}"
}

output "health_url" {
  description = "Health endpoint used for post-deployment verification."
  value       = "http://${azurerm_public_ip.pip.ip_address}/health"
}

output "ssh_command" {
  description = "Command to connect (adjust the private-key path)."
  value       = "ssh -i ~/.ssh/releasenote_azure ${var.admin_username}@${azurerm_public_ip.pip.ip_address}"
}
