# Presentation outline (10 slides, about 8 to 10 minutes)

Design tip: white background, navy text, indigo accent (matches the app). Use real screenshots only.

## 1. ReleaseNote: Track every release. Automate every deployment.
- DevOps (24DC2006), IA-3; team names and roll numbers
- Flask + SQLite + Jenkins + Terraform + Azure
- **Visual:** dashboard screenshot (Figure 1)
- **Script:** "ReleaseNote records software releases, and the same project shows how a Git push can become a tested, verified deployment on Azure with no manual steps."

## 2. Problem and objectives
- Release history scattered; manual deployments inconsistent
- Goal: one release tracker + automated delivery pipeline
- Tests gate deployment; health check proves it worked
- **Visual:** simple before/after graphic (manual copy vs pipeline)
- **Script:** "Manual shipping is slow and error-prone. We wanted every change to follow the same tested path."

## 3. Application features
- Dashboard, searchable history, create/edit/delete, details
- Validation, duplicate-version protection, CSRF, sign-in
- `/health` endpoint with DB check
- **Visual:** history page with filters (Figure 3) + detail page (Figure 4)
- **Script:** "Users record version, status, features, fixes and deployment notes. Search and filters make history easy to navigate."

## 4. System architecture
- Developer > GitHub > Jenkins > Azure VM
- On VM: Nginx > Gunicorn > Flask > SQLite
- Terraform provisions, Jenkins deploys: two separate paths
- **Visual:** Mermaid architecture diagram
- **Script:** "Terraform builds the infrastructure once. Jenkins handles every code change. Users only ever talk to Nginx."

## 5. Terraform infrastructure
- Resource group, VNet, subnet, NSG, public IP, NIC, Ubuntu VM
- SSH key only; SSH limited to named IPs; only 22/80 open
- init > validate > plan > apply > destroy
- **Visual:** plan and apply screenshots (Figures 6, 7) + Azure portal (Figure 8)
- **Script:** "Everything is code: reviewable, repeatable and removable with one destroy command."

## 6. Jenkins CI/CD workflow
- Checkout > environment > tests > validate > package > deploy > verify
- Trigger: webhook or Poll SCM [say which you used]
- Credentials stored in Jenkins, not in the repo
- **Visual:** Jenkins stage view (Figure 9) + pipeline diagram
- **Script:** "A failed test stops the run before packaging or deployment. Only green builds ship."

## 7. Azure deployment
- `deploy.sh`: release folder, venv, schema, systemd, Nginx, restart
- Data and secrets live outside releases; backup before every deploy
- Automatic rollback if `/health` fails
- **Visual:** deploy console (Figure 11) + public app (Figure 12)
- **Script:** "Each release is a numbered folder. We switch a symlink, restart, and check health. If it fails we switch back."

## 8. Testing and verification
- 71 pytest tests: seeding, CRUD, validation, search, security
- Isolated temp database; JUnit report in Jenkins
- Live proof: `/health` build equals the commit Jenkins built
- **Visual:** test report (Figure 10), health JSON (Figure 13), failed-test run (Figure 15)
- **Script:** "We demonstrate both outcomes: a passing commit deploys, a failing commit does not."

## 9. Results, limitations, lessons
- [Your measured results: push-to-live time, build duration]
- Limits: HTTP only, SQLite on one VM, no schema migrations
- Lessons: [your own, e.g. NSG/IP restrictions, idempotent scripts]
- **Visual:** Figure 14 (commit to automatic deployment)
- **Script:** "It works end to end for a single VM. We know exactly where it would need hardening for production."

## 10. Conclusion and future work
- Delivered IaC + CI/CD + verified deployment
- Next: HTTPS, managed DB, migrations, blue/green
- Q&A
- **Visual:** architecture diagram, small
- **Script:** "Track every release, automate every deployment: that is demonstrated here, and these are the next steps."
