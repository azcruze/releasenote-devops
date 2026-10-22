# Screenshot and evidence checklist

Capture **genuine** screenshots yourself after running each step. Do not edit, mock or reuse another project's images. Include the browser address bar / terminal prompt and (where visible) date and your name in the shell prompt or Jenkins user.

| # | Evidence | Caption to use | Captured |
|---|---|---|---|
| 1 | Dashboard (local or Azure) | Figure 1: ReleaseNote dashboard showing totals, latest released version and recent activity | [ ] |
| 2 | Create release form, filled | Figure 2: Release creation form with validation hints | [ ] |
| 3 | Release history with search/filter applied | Figure 3: Searchable, filterable release history | [ ] |
| 4 | Release details page | Figure 4: Release details with features, fixes and improvements separated | [ ] |
| 5 | `terraform init` and `terraform validate` output | Figure 5: Terraform initialisation and successful validation | [ ] |
| 6 | `terraform plan` summary (`Plan: N to add`) | Figure 6: Terraform plan of Azure resources | [ ] |
| 7 | `terraform apply` complete + `terraform output` | Figure 7: Infrastructure provisioned | [ ] |
| 8 | Azure Portal resource group contents | Figure 8: Azure resources in rg-releasenote-dev | [ ] |
| 9 | Jenkins Stage View, all stages green | Figure 9: Jenkins pipeline stages | [ ] |
| 10 | Jenkins test report / console showing pytest result | Figure 10: Automated tests passing in Jenkins | [ ] |
| 11 | Console of Deploy + Verify stages | Figure 11: Successful deployment and health verification | [ ] |
| 12 | Application at `http://<public-ip>/` | Figure 12: Application on the Azure public IP | [ ] |
| 13 | `http://<public-ip>/health` JSON | Figure 13: Health endpoint response | [ ] |
| 14 | GitHub commit + Jenkins build "Started by GitHub push / SCM change" + updated `build` in `/health` | Figure 14: Automatic deployment after a commit | [ ] |
| 15 | (Recommended) Failed-test build with later stages skipped, `/health` build unchanged | Figure 15: Failed tests block deployment | [ ] |
| 16 | GitHub webhook "Recent Deliveries" 200 (only if you used the webhook) | Figure 16: Webhook delivery | [ ] |

Redact the subscription ID if shown. Do not show private keys or the admin password.
