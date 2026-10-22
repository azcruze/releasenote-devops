# Jenkins setup, triggers, rollback and failure demo

## 1. Where Jenkins runs
The `Jenkinsfile` uses `sh`, so the Jenkins **agent must be Linux** (Ubuntu VM, WSL2, or a Linux container). Jenkins is **not** installed on the Azure application VM and port 8080 is never opened there.

Install Jenkins by following the current official instructions (package keys change over time): <https://www.jenkins.io/doc/book/installing/linux/>. On the Jenkins machine also install the pipeline's tool needs:
```bash
sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip git curl openssh-client
```

## 2. Plugins (minimal set)
Pipeline (`workflow-aggregator`), Git, Credentials Binding, SSH Credentials, JUnit (bundled), Timestamper, and **GitHub** (only for the webhook trigger). Nothing else is required.

## 3. Credentials (Manage Jenkins > Credentials > Global)
| ID | Kind | Value |
|---|---|---|
| `releasenote-azure-ssh` | SSH Username with private key | username `azureuser`; paste the contents of the **private** key `releasenote_azure` |
| `releasenote-vm-host` | Secret text | the VM public IP from `terraform output public_ip_address` |

If the repository is private, add a GitHub personal access token (minimum scope: read access to this repo) as a *Username with password* credential and select it in the job's Git settings.

## 4. How Jenkins securely reaches the VM
* Outbound SSH from Jenkins to the VM's public IP, key-based, `BatchMode`, host key recorded on first connect in `$JENKINS_HOME/.releasenote_known_hosts` (trust-on-first-use; if you recreate the VM, delete that line).
* The Azure NSG allows port 22 **only** from `ssh_allowed_cidrs`. Put your own IP **and the public egress IP of the Jenkins machine** there (`curl ifconfig.me` run on the Jenkins machine), then `terraform apply` again. If Jenkins is on a home network with a changing IP, SSH will start failing when the IP changes; update the variable.
* The deploy user (`azureuser`) has passwordless `sudo` (Azure default). Accepting this is a deliberate simplification; a stricter design would use a dedicated deploy user limited to `deploy.sh`.

## 5. Create the job
New Item > **Pipeline** > Pipeline script from SCM > Git > repository URL > branch `*/main` > Script Path `Jenkinsfile`. Save, then press **Build Now** once to confirm the whole path works before configuring triggers.

## 6. Trigger option A - GitHub webhook
1. Job > Configure > Build Triggers > tick **GitHub hook trigger for GITScm polling**.
2. GitHub repo > Settings > Webhooks > Add webhook: Payload URL `https://<jenkins-public-url>/github-webhook/` (keep the trailing slash), content type `application/json`, event **Just the push event**.
3. GitHub must be able to reach Jenkins from the internet. A Jenkins on a laptop or campus network usually is **not** reachable; either expose it through a tunnel (ngrok, Cloudflare Tunnel) or use option B. Never expose Jenkins without authentication; prefer HTTPS.
4. Authentication: the `/github-webhook/` endpoint does not need a Jenkins login or crumb. If your GitHub plugin version supports a webhook shared secret (Manage Jenkins > System > GitHub), configure it and set the same secret in the GitHub webhook.
5. **Test:** the webhook's *Recent Deliveries* tab should show a `200`. Then push a trivial commit; a new build should start within seconds with the "Started by GitHub push" cause. Until you have seen this, do not describe the webhook as working.

## 7. Trigger option B - Poll SCM (simplest fallback)
Job > Configure > Build Triggers > **Poll SCM** > schedule `H/2 * * * *`. Jenkins checks GitHub every ~2 minutes and builds when there is a new commit. It needs only outbound access to GitHub.
**Test:** push a commit, wait up to 2 minutes, confirm a build starts ("Started by an SCM change").

## 8. Prove that failed tests block deployment
1. Note the current build ID: `curl http://<ip>/health` (field `build`).
2. On `main`, break one test (e.g. change an `assert` in `tests/test_app_basics.py` to `assert False`), commit, push.
3. Jenkins runs **Automated Tests**, the stage fails, and the later stages (`Validate Build`, `Package`, `Deploy`, `Verify`) show as skipped/not run. Capture the screenshot.
4. `curl http://<ip>/health` again: `build` is **unchanged**, so nothing was deployed.
5. Fix with `git revert <bad-commit>` and push; the next build passes and deploys.

## 9. Rollback strategy
* **Automatic:** `deploy.sh` keeps the previous release directory. If `/health` is not `ok` within ~40 s after the switch, it re-points `/opt/releasenote/current` to the previous release, restarts, and fails the pipeline.
* **Manual** (on the VM):
  ```bash
  sudo bash /opt/releasenote/current/deploy/rollback.sh --list
  sudo bash /opt/releasenote/current/deploy/rollback.sh            # previous release
  sudo bash /opt/releasenote/current/deploy/rollback.sh 12-ab12cd34  # specific release
  ```
  The last 5 releases are retained.
* **Limitation - data:** rollback restores *code only*. SQLite data is shared by every release. The app uses `CREATE TABLE IF NOT EXISTS` and has no migration framework, so a future release that changes the schema (new column, etc.) may not be compatible with older code. Keep schema changes backward compatible (add, never rename or drop) for one release. Before every deployment a consistent backup is written to `/var/backups/releasenote/` (last 10 kept). Restore:
  ```bash
  sudo systemctl stop releasenote
  sudo cp /var/backups/releasenote/releasenote-<id>.db /var/lib/releasenote/releasenote.db
  sudo chown releasenote:releasenote /var/lib/releasenote/releasenote.db
  sudo rm -f /var/lib/releasenote/releasenote.db-wal /var/lib/releasenote/releasenote.db-shm
  sudo systemctl start releasenote
  ```
  Backups live on the same VM disk; they do not protect against loss of the VM.

## 10. Troubleshooting
| Symptom | Likely cause / fix |
|---|---|
| `Permission denied (publickey)` | Wrong private key in credential, or key does not match the `.pub` Terraform installed |
| SSH hangs, then timeout | Jenkins egress IP not in `ssh_allowed_cidrs`; update and re-apply |
| `Host key verification failed` | VM was recreated with the same IP; remove the line from `$JENKINS_HOME/.releasenote_known_hosts` |
| Deploy fails at `apt-get` | cloud-init still running; wait a minute and rebuild |
| Verify stage times out but deploy passed | NSG port 80 closed, or Nginx not running: `sudo systemctl status nginx releasenote` on the VM |
| `GIT_BRANCH` is not `origin/main` | Job built a different branch; deploy stages are intentionally skipped |
| Writes return 403 | `ADMIN_PASSWORD_HASH` not set yet (read-only by design) |
