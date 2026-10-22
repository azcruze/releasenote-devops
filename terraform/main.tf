locals {
  prefix = "${var.project_name}-${var.environment}"

  tags = merge({
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    course      = "24DC2006-DevOps"
  }, var.extra_tags)
}

# ---------------------------------------------------------------- Resource group
resource "azurerm_resource_group" "rg" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.tags
}

# ---------------------------------------------------------------- Networking
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${local.prefix}"
  address_space       = var.vnet_address_space
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = local.tags
}

resource "azurerm_subnet" "app" {
  name                 = "snet-${local.prefix}-app"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_prefix]
}

# Only SSH (restricted), HTTP and optional HTTPS. Jenkins (8080) is deliberately NOT exposed.
resource "azurerm_network_security_group" "nsg" {
  name                = "nsg-${local.prefix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = local.tags

  security_rule {
    name                       = "allow-ssh-from-admin"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefixes    = var.ssh_allowed_cidrs
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-http"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }

  dynamic "security_rule" {
    for_each = var.enable_https ? [1] : []
    content {
      name                       = "allow-https"
      priority                   = 120
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "443"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    }
  }
}

resource "azurerm_subnet_network_security_group_association" "app" {
  subnet_id                 = azurerm_subnet.app.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

resource "azurerm_public_ip" "pip" {
  name                = "pip-${local.prefix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Static"
  sku                 = "Standard"
  domain_name_label   = var.dns_label
  tags                = local.tags
}

resource "azurerm_network_interface" "nic" {
  name                = "nic-${local.prefix}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = local.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.app.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip.id
  }
}

# ---------------------------------------------------------------- Virtual machine
resource "azurerm_linux_virtual_machine" "vm" {
  name                  = "vm-${local.prefix}"
  computer_name         = replace(local.prefix, "-", "")
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  size                  = var.vm_size
  admin_username        = var.admin_username
  network_interface_ids = [azurerm_network_interface.nic.id]

  # SSH keys only. Password logins are disabled.
  disable_password_authentication = true
  admin_ssh_key {
    username   = var.admin_username
    public_key = file(pathexpand(var.ssh_public_key_path))
  }

  os_disk {
    name                 = "osdisk-${local.prefix}"
    caching              = "ReadWrite"
    storage_account_type = var.os_disk_type
    disk_size_gb         = var.os_disk_size_gb
  }

  # Ubuntu Server 22.04 LTS (Gen2)
  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  # Installs OS packages only (nginx, python3-venv, ...). The application itself is
  # deployed by Jenkins, not by Terraform.
  custom_data = base64encode(file("${path.module}/cloud-init.yaml"))

  boot_diagnostics {} # managed storage account, no extra resource to maintain

  tags = local.tags

  lifecycle {
    # Editing cloud-init later must not force the VM to be destroyed and recreated.
    ignore_changes = [custom_data]
  }
}
