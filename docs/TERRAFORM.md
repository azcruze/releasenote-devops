# Terraform guide

Terraform here creates **infrastructure only**. Files are in `terraform/`.

| File | Purpose |
|---|---|
| `versions.tf` | Terraform >= 1.6, AzureRM provider `~> 4.0` |
| `providers.tf` | Provider block (uses Azure CLI login; subscription from `ARM_SUBSCRIPTION_ID`) |
| `variables.tf` | Inputs with validation (SSH CIDRs must not be `0.0.0.0/0`; key file must exist) |
| `main.tf` | Resource group, VNet, subnet, NSG + rules, public IP, NIC, Ubuntu 22.04 VM |
| `cloud-init.yaml` | First boot: installs nginx, python3-venv, pip, curl, sqlite3 |
| `outputs.tf` | Public IP, URLs, SSH command |
| `terraform.tfvars.example` | Copy to `terraform.tfvars` (git-ignored) |

> The Terraform CLI was **not** available where this project was generated, so `fmt/validate/plan` have not been run by the author of these files. Run them yourself (below); if `validate` reports an error, fix it before `plan` and tell me the message.

## Authentication and permissions

Terraform calls Azure Resource Manager as **you**, through the Azure CLI session; no client secret is stored anywhere.

**Windows (PowerShell)**
```powershell
az login
az account list --output table
az account set --subscription "<subscription name or id>"
$env:ARM_SUBSCRIPTION_ID = (az account show --query id -o tsv)
```
**Linux/macOS**
```bash
az login
az account set --subscription "<subscription name or id>"
export ARM_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
```
Your account needs **Contributor** (or Owner) on the subscription or on a resource group you pre-create. Student subscriptions may restrict regions and VM sizes; if `apply` says a size is unavailable, run
`az vm list-skus --location centralindia --size Standard_B --output table` and set `vm_size`/`location`.

## SSH key (one time)

**Windows (PowerShell)** `ssh-keygen -t ed25519 -f $HOME\.ssh\releasenote_azure -C "releasenote"`
**Linux** `ssh-keygen -t ed25519 -f ~/.ssh/releasenote_azure -C "releasenote"`

Terraform reads only `releasenote_azure.pub`. The private key goes into Jenkins Credentials (see `JENKINS.md`) and nowhere else. Use a **dedicated** key for this project.

## Workflow (all from the `terraform/` directory)

```bash
terraform init                 # downloads the AzureRM provider, creates .terraform/ and .terraform.lock.hcl
terraform fmt -check -recursive   # style check (run `terraform fmt` to fix)
terraform validate             # offline syntax and reference check -> "Success! The configuration is valid."
terraform plan -out tfplan     # shows exactly what will be created; creates nothing
terraform apply tfplan         # PAID RESOURCES START HERE - review the plan first
terraform output               # public IP, URLs, ssh command
```
Commit `.terraform.lock.hcl` (pins provider hashes). Never commit `.terraform/`, `tfplan`, `*.tfstate` or `terraform.tfvars`.

Inspect what exists: `terraform state list`, `terraform show`, `az resource list --resource-group rg-releasenote-dev --output table`, or the Azure Portal.

## Avoiding duplicates and cost

* Re-running `apply` is safe: Terraform compares state with the plan and creates only what is missing. Duplicates appear only if you **lose the state file** or change `project_name`/`environment` (which changes every resource name). Keep `terraform.tfstate` backed up outside Git.
* A running B2s VM, its disk and the Standard static IP are billed **while they exist**, even when idle. Deallocating (`az vm deallocate`) stops VM compute charges but not the disk and IP.
* When finished, and after capturing screenshots: `terraform destroy` (type `yes`). Confirm with `az group exists --name rg-releasenote-dev` -> `false`.

## Terraform state

State is **local** (`terraform.tfstate`). It maps your code to real Azure objects and can contain sensitive attributes, so it must be protected and never committed. Losing it means Terraform no longer knows what it created.

### Optional: Azure Storage remote backend
Prerequisites: a storage account and blob container created *outside* this configuration (chicken-and-egg), and your account holding **Storage Blob Data Contributor** on it.
```bash
az group create -n rg-tfstate -l centralindia
az storage account create -n <globally-unique-name> -g rg-tfstate -l centralindia --sku Standard_LRS --allow-blob-public-access false
az storage container create --account-name <globally-unique-name> -n tfstate --auth-mode login
```
Add to `versions.tf`:
```hcl
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "<globally-unique-name>"
    container_name       = "tfstate"
    key                  = "releasenote.tfstate"
    use_azuread_auth     = true
  }
```
Then `terraform init -migrate-state`. The primary workflow does not require this.
