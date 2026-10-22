---
title: "ReleaseNote: Automated Software Release Management and Changelog Tracking Using Flask, SQLite, Jenkins, Terraform, and Microsoft Azure"
---

<!-- Convert to PDF: pandoc docs/REPORT.md -o ReleaseNote_Report.pdf --toc  (Mermaid diagrams: render to PNG with mermaid-cli or screenshot from GitHub and insert). Text in [square brackets] must be filled by you. -->

# Title Page

**ReleaseNote: Automated Software Release Management and Changelog Tracking Using Flask, SQLite, Jenkins, Terraform, and Microsoft Azure**
*Track every release. Automate every deployment.*

| | |
|---|---|
| Course | DevOps (24DC2006) |
| Class / Semester | B.Tech AIDS / CO, VII Semester |
| Evaluation | IA-3 (maximum 40 marks) |
| Course instructors | Mrs. J. Srija, Mrs. Esther Lipni, Mr. Rahul |
| Submitted by | [Name(s), roll number(s)] |
| Date | [Submission date] |
| Repository | [GitHub URL] |

# 1. Abstract
ReleaseNote is a Flask web application that keeps a structured, searchable history of software releases. Around it, the project implements an end-to-end DevOps workflow: a push to GitHub triggers a Jenkins pipeline that runs automated tests, packages the application, deploys it over SSH to an Azure Linux virtual machine provisioned by Terraform, restarts the Gunicorn service behind Nginx, and verifies the new build through a public health endpoint. The project demonstrates infrastructure as code, continuous integration, continuous deployment, rollback, and basic security practice on a small, reproducible scale.

# 2. Problem Statement
Teams often record releases in scattered documents, so it is hard to see what changed, when, and who shipped it. Manual deployment adds a second problem: copying files to servers by hand is slow, inconsistent and error-prone. A single tool that stores release notes, and a pipeline that removes manual steps from shipping that tool, address both.

# 3. Objectives
1. Build a working release-tracking web application with full create/read/update/delete.
2. Provision cloud infrastructure from code (Terraform on Azure).
3. Automate test and deployment with a Jenkins pipeline triggered by GitHub.
4. Ensure a failing test prevents deployment, and a failing deployment rolls back.
5. Verify every deployment against the live public endpoint.
6. Document, test and present the work reproducibly.

# 4. Scope
**In scope:** one Flask application, SQLite storage, a single Azure Linux VM, Nginx + Gunicorn + systemd, one Jenkins pipeline, local Terraform state, HTTP access.
**Out of scope:** multi-user accounts, high availability, TLS certificate automation, containerisation/Kubernetes, remote Terraform state (documented as optional), database migrations framework.

# 5. Tools and Technologies
| Area | Tool | Why chosen |
|---|---|---|
| Web framework | Flask 3.0.3 | Small, explicit, easy to explain and test |
| Database | SQLite (WAL) | No server to run; adequate for one VM and light load |
| App server / proxy | Gunicorn 22, Nginx | Standard production pairing; Gunicorn is not exposed publicly |
| Process manager | systemd | Survives SSH disconnect and reboot; auto-restart |
| Testing | Pytest 8.2.2 | Concise tests, fixtures, JUnit output for Jenkins |
| Source control | Git, GitHub | Industry standard; push events drive the pipeline |
| CI/CD | Jenkins declarative pipeline | Required by the course; pipeline-as-code in `Jenkinsfile` |
| IaC | Terraform + AzureRM ~> 4.0 | Declarative, repeatable, reviewable infrastructure |
| Cloud | Azure Linux VM (Ubuntu 22.04 LTS) | Required VM-based deployment |

# 6. System Requirements
**Developer machine:** Windows/Linux/macOS, Python 3.10+, Git, Azure CLI, Terraform >= 1.6. **Jenkins machine:** Linux, Java (per Jenkins docs), Python 3 + venv, Git, curl, OpenSSH client. **Azure:** subscription with permission to create resources; VM size such as Standard_B2s (2 vCPU, 4 GiB). **Browser:** any current browser; no internet needed for UI assets.

# 7. Proposed Solution
Application code lives in GitHub. Terraform builds the network and VM once. Jenkins builds, tests and ships each commit; `deploy.sh` on the VM installs it as an immutable numbered release directory, switches a symlink, restarts the service, and rolls back automatically if `/health` fails. Persistent data and secrets live outside the release directories so deployments cannot overwrite them.

# 8. System Architecture
See `docs/ARCHITECTURE.md`. Summary: Developer -> GitHub -> Jenkins -> (pytest -> package -> SSH) -> Azure VM [Nginx -> Gunicorn -> Flask -> SQLite]; Terraform independently provisions Azure.

# 9. Architecture Diagrams
[Insert rendered Figure A (system architecture) and Figure B (CI/CD pipeline) from `docs/ARCHITECTURE.md`.]

# 10. Application Module Descriptions
| Module | Responsibility |
|---|---|
| `app/__init__.py` | Application factory, error pages, security headers, start-up initialisation |
| `app/routes.py` | Dashboard, history, CRUD, About, `/health`, login/logout |
| `app/models.py` | Parameterised SQL: list/search/filter/sort/paginate, CRUD, statistics, neighbours |
| `app/validation.py` | Version (semantic) and field validation, normalisation, duplicate check |
| `app/db.py` | Connections, schema, idempotent demo seeding, reset |
| `app/auth.py` | Management modes, sign-in, CSRF, redirect safety, login throttle |
| `app/cli.py` | `init-db`, `seed-demo`, `reset-demo`, `backup-db`, `hash-password` |
| `app/buildinfo.py` | Commit/build identifier from `BUILD_INFO` or Git |
| `templates/`, `static/` | Jinja pages and a CSS design system with variables; minimal progressive-enhancement JS |

# 11. Database Design
Single table `releases`.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| version | TEXT NOT NULL **UNIQUE** | semantic version without "v"; prevents duplicates even under races |
| title | TEXT NOT NULL | 3-120 chars |
| description | TEXT NOT NULL | 10-1000 chars; added to existing databases with a non-destructive migration |
| release_date | TEXT NOT NULL | ISO date |
| status | TEXT NOT NULL | Draft, Scheduled, Released, Rolled Back, Deprecated |
| category | TEXT NOT NULL | Major, Minor, Patch, Hotfix, Security |
| features / bug_fixes / improvements | TEXT | one item per line |
| deployment_notes | TEXT | |
| author | TEXT NOT NULL | |
| created_at / updated_at | TEXT NOT NULL | UTC |

Indexes on `(release_date DESC, id DESC)` and `status`. WAL journal mode permits two Gunicorn workers.

Fresh databases are populated with 25 releases from v1.6.0 through v2.5.0. Startup seeding uses `INSERT OR IGNORE`: existing versions and user-created records are preserved, and subsequent starts do not create duplicates.

# 12. Terraform Implementation
Files `versions.tf`, `providers.tf`, `variables.tf`, `main.tf`, `outputs.tf`, `cloud-init.yaml`, `terraform.tfvars.example`. Variables cover region, names, VM size, admin user, key path, SSH CIDRs, networking, disk, HTTPS toggle, tags; validations reject `0.0.0.0/0` for SSH and missing key files. Resources carry tags; dependencies are expressed through resource references. Procedure, authentication and state handling are in `docs/TERRAFORM.md`.

# 13. Azure Infrastructure Configuration
Resource group `rg-releasenote-dev`; VNet `10.20.0.0/16`; subnet `10.20.1.0/24`; NSG allowing 22 (only from listed CIDRs), 80 (Internet), 443 only if enabled; Standard static public IP; NIC; Ubuntu Server 22.04 LTS Gen2 VM with SSH-key-only login. Jenkins (8080) is not exposed. [Record the actual region, VM size and IP you used.]

# 14. Jenkins Pipeline Design
Declarative pipeline: Checkout; Verify Environment; Automated Tests (JUnit published); Validate Build; Package (archived, checksummed); Deploy to Azure VM (SSH key and host from Jenkins Credentials, single-quoted shell to avoid secret interpolation, `timeout`, `BatchMode`); Verify Deployment (public `/health`, must show `status: ok` and the commit just built); `post` reporting. Options: timestamps, 30-minute timeout, no concurrent builds, log rotation.

# 15. GitHub Integration and Trigger Configuration
Two supported triggers: GitHub webhook to `/github-webhook/`, or Poll SCM every 2 minutes. Configuration and tests in `docs/JENKINS.md` sections 6-7. [State which one you actually configured and tested.]

# 16. Deployment Workflow
`deploy.sh` (9 steps): prerequisites; service user and directories; env file (created once); install release + per-release virtualenv; schema init as service user; database backup; systemd + Nginx config; atomic symlink switch + restart + health wait (rollback on failure); prune to last 5 releases. Persistent data in `/var/lib/releasenote`, secrets in `/etc/releasenote`.

# 17. Automated Testing Strategy
62 Pytest tests in five files with a fresh temporary database per test: start-up and schema, dashboard, health (including failure and secret-leak checks), seeding idempotency, full CRUD, 404s, validation (parameterised invalid inputs, duplicates), search/filter/sort/pagination, and security (CSRF, auth, throttle, open-redirect, XSS escaping, SQL-injection inertness, headers, request size, read-only production mode). The pipeline only reaches deployment if all pass. [Add coverage figures only if you measure them, e.g. `pip install pytest-cov` and `pytest --cov=app`.]

# 18. Security Considerations
Authentication for writes; read-only default in production; CSRF; parameterised SQL; auto-escaped templates; CSP and other headers; SSH-key-only VM, SSH restricted by CIDR; secrets only in Jenkins Credentials and a root-owned env file; service runs as an unprivileged account with a hardened systemd unit; Terraform state excluded from Git. Known gaps: HTTP not HTTPS, single shared password, per-worker in-memory throttle, trust-on-first-use SSH host key, admin account with passwordless sudo.

# 19. Execution and Verification Instructions
Follow `README.md` sections 1-6 in order. Verification checklist: tests pass locally; `terraform validate` succeeds; `terraform apply` completes; Jenkins build is green; `/health` returns ok with the expected commit; a new commit triggers a build and changes the `build` value; a deliberately failing test stops the pipeline.

# 20. Observations and Actual Results
*Fill from your own runs. Do not enter values you did not observe.*

| Item | Observed |
|---|---|
| Local test run | [paste your actual test output] |
| `terraform validate` | [paste result] |
| `terraform plan` summary | [Plan: N to add...] |
| Resources created in Azure | [list from portal] |
| Public IP / URL | [value] |
| First Jenkins build result and duration | [value] |
| Trigger used and time from push to build start | [value] |
| `/health` response after deployment | [paste] |
| Failed-test experiment outcome | [value] |
| Deployed commit vs `/health` build | [match? value] |

# 21. Limitations
Single VM and no high availability; SQLite is single-writer and tied to the VM disk (destroying the VM destroys data; backups are on the same disk); no migration tooling, so rollback does not revert schema; HTTP only; Jenkins must be able to reach the VM by SSH and, for webhooks, be reachable by GitHub; short-lived demo cost model.

# 22. Future Enhancements
TLS with Let's Encrypt and a DNS name; Azure Database or managed backups; Alembic-style migrations; role-based users; Markdown/RSS export of release notes; remote Terraform state in Azure Storage; blue/green deployment with a second VM; Jenkins agent in Azure; container image build.

# 23. Conclusion
The project delivers a complete, reproducible path from a Git commit to a verified Azure deployment, with tests as a gate, infrastructure defined as code, and rollback and health verification built in. [Add one or two sentences on what you learned from running it.]

# 24. References
1. Flask documentation - <https://flask.palletsprojects.com/>
2. Gunicorn documentation - <https://docs.gunicorn.org/>
3. Nginx documentation - <https://nginx.org/en/docs/>
4. pytest documentation - <https://docs.pytest.org/>
5. Terraform documentation - <https://developer.hashicorp.com/terraform/docs>
6. Terraform AzureRM provider - <https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs>
7. Jenkins documentation - <https://www.jenkins.io/doc/>
8. Azure Virtual Machines documentation - <https://learn.microsoft.com/azure/virtual-machines/>
9. Semantic Versioning 2.0.0 - <https://semver.org/>
10. SQLite Write-Ahead Logging - <https://www.sqlite.org/wal.html>

# Appendix A: Screenshots
See `docs/SCREENSHOTS.md`; insert Figures 1-16 here with captions. *Items missing at submission time must be captured, not substituted.*
