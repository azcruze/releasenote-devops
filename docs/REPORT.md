# ReleaseNote: Automated Software Release Management and Changelog Tracking Using Flask, SQLite, Jenkins, Terraform, and Microsoft Azure

*Track every release. Automate every deployment.*

## Title Page

| Detail | Information |
|---|---|
| Course | DevOps (24DC2006) |
| Class / Semester | B.Tech AIDS / CO, VII Semester |
| Evaluation | IA-3 |
| Course Instructors | Mrs. J. Srija, Mrs. Esther Lipni, Mr. Rahul |
| Submitted By | [Enter student name and roll number] |
| Submission Date | [Enter submission date] |
| GitHub Repository | https://github.com/azcruze/releasenote-devops |

## 1. Abstract

ReleaseNote is a Flask-based web application designed to maintain a structured, searchable history of software releases. It supports release creation, viewing, editing, deletion, filtering, and status tracking. The application is supported by a DevOps workflow using GitHub, GitHub Actions, and Jenkins. GitHub Actions executes the automated Python test suite and uploads a JUnit XML report. Jenkins checks out the source code, validates required project files, packages the source, and generates a SHA-256 checksum.

The verified GitHub Actions run completed 78 tests with zero failures and zero errors. The Jenkins `ReleaseNote-CI` pipeline also completed successfully and produced source packaging artifacts. Terraform and Microsoft Azure are included in the project's intended infrastructure and deployment design. However, Azure provisioning, remote deployment, and live health verification have not yet been confirmed. The project therefore demonstrates an implemented application, automated testing, source packaging, and a documented path toward cloud deployment.

## 2. Problem Statement

Software teams need a reliable way to record release versions, changes, fixes, improvements, and deployment notes. When this information is maintained manually across separate documents, searching for a particular release and identifying its changes can become difficult.

Manual software delivery can also involve repetitive, error-prone steps. ReleaseNote addresses release-information management through a centralized web application and supports a more repeatable software delivery process through automated testing and source packaging.

## 3. Objectives

1. Develop a web application for maintaining software release records.
2. Implement create, read, update, and delete operations with input validation.
3. Store release information in a SQLite database.
4. Maintain source code and version history using Git and GitHub.
5. Execute automated tests using GitHub Actions.
6. Configure a Jenkins pipeline for source checkout, project validation, and packaging.
7. Generate a source archive and SHA-256 checksum as build artifacts.
8. Document the planned infrastructure provisioning and deployment process using Terraform and Microsoft Azure.
9. Maintain accurate execution evidence and identify work that remains incomplete.

## 4. Scope

**Implemented and verified scope**

- Flask-based release-tracking application.
- SQLite-based persistence.
- Release management and validation features.
- GitHub repository and version control.
- GitHub Actions automated test workflow.
- JUnit XML test report artifact.
- Jenkins source checkout, environment verification, project-file validation, and packaging.
- SHA-256 checksum generation for the source archive.

**Planned or not yet verified**

- Terraform-based Azure resource provisioning.
- Remote application deployment.
- Nginx and Gunicorn configuration on a deployed VM.
- Jenkins-driven remote deployment and rollback.
- Live public health verification after deployment.

## 5. Tools and Technologies

| Technology | Purpose |
|---|---|
| Python 3 | Application programming language |
| Flask 3.0.3 | Web application framework |
| SQLite | Relational database |
| Jinja2 | HTML template rendering |
| Gunicorn 22 | Planned production application server |
| Nginx | Planned web server and reverse proxy |
| systemd | Planned Linux service management |
| Pytest 8.2.2 | Automated testing |
| Git and GitHub | Source control and repository hosting |
| GitHub Actions | Automated test execution and report upload |
| Jenkins | Source validation and packaging pipeline |
| Terraform | Infrastructure as code for planned Azure provisioning |
| Microsoft Azure | Intended cloud hosting platform |

## 6. System Requirements

For local development, the project requires Python 3.10 or later, Git, and a modern web browser. The automated testing workflow uses a GitHub-hosted Ubuntu runner with Python 3.12.

Jenkins requires a working Jenkins environment and the command-line tools used by the pipeline, including Git, Bash, and tar.

The planned Azure deployment additionally requires an Azure subscription, Azure CLI, Terraform, SSH credentials, and appropriate permissions to create and manage cloud resources. Azure deployment should only be performed after reviewing the infrastructure configuration and expected costs.

## 7. Proposed Solution

The solution consists of a Flask application and supporting automation workflows.

The application stores release records in SQLite and provides a browser-based interface for release management. Source code is maintained in GitHub. GitHub Actions runs the Python tests when changes are pushed to the `main` branch or when a pull request targets `main`. It also supports manual workflow execution and uploads a JUnit XML test report.

A separate Jenkins pipeline checks out the repository, verifies the execution environment, checks required project files, and creates a compressed source archive with a SHA-256 checksum.

Terraform configuration is included for the intended Azure infrastructure. Remote deployment and health verification remain future execution steps until supported by actual evidence.

## 8. System Architecture

The implemented workflow consists of the following paths:

**Automated testing**

Developer → GitHub → GitHub Actions → Python dependencies → Pytest → JUnit XML report artifact.

**Source packaging**

GitHub repository → Jenkins → Environment verification → Project-file validation → Source archive → SHA-256 checksum → Jenkins artifacts.

**Planned cloud deployment**

Terraform → Azure virtual machine → Nginx → Gunicorn → Flask application → SQLite database.

The testing and packaging paths are separate workflows. The successful Jenkins packaging build does not establish that Jenkins executed the Python tests or deployed the application.

## 9. Application Module Descriptions

| Module | Responsibility |
|---|---|
| `app/__init__.py` | Application factory, startup initialization, error handling, and security headers |
| `app/routes.py` | Dashboard, release history, CRUD routes, About page, health endpoint, and authentication routes |
| `app/models.py` | Database operations, release queries, filtering, sorting, pagination, and statistics |
| `app/validation.py` | Input normalization, version validation, field validation, and duplicate-version checks |
| `app/db.py` | Database connections, schema initialization, seeding, and reset operations |
| `app/auth.py` | Authentication, CSRF handling, redirect validation, and login throttling |
| `app/cli.py` | Flask command-line operations for database management and password hashing |
| `app/buildinfo.py` | Build identifier handling |
| Templates and static assets | HTML templates, styling, and browser-side enhancements |

## 10. Database Design

ReleaseNote uses SQLite to store release information.

The `releases` table contains fields for the release identifier, version, title, description, release date, status, category, features, bug fixes, improvements, deployment notes, author, and creation and update timestamps.

The version field is unique to prevent duplicate release versions. The application validates input before saving records and uses parameterized SQL for database operations.

A fresh database is designed to receive 25 demonstration releases spanning versions v1.6.0 through v2.5.0. The seeding process is intended to be repeatable and preserve existing release records.

## 11. GitHub Actions Implementation

The workflow is stored at:

`.github/workflows/python-tests.yml`

It is configured to run on pushes to `main`, pull requests targeting `main`, and manual execution.

The workflow performs the following steps:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Installs development dependencies from `requirements-dev.txt`.
4. Runs the Pytest suite.
5. Produces a JUnit XML report.
6. Uploads the report as a workflow artifact.

### Verified Test Results

| Metric | Verified result |
|---|---:|
| Tests executed | 78 |
| Failures | 0 |
| Errors | 0 |
| Skipped | 0 |
| Workflow outcome | Success |

The report is uploaded as the `releasenote-test-report` artifact, with a configured retention period of 14 days.

**Workflow run:** https://github.com/azcruze/releasenote-devops/actions/runs/40289024445

These results refer to the verified workflow run and should not be treated as a guarantee that every future code revision will pass.

## 12. Jenkins Pipeline Implementation

The Jenkins job is named `ReleaseNote-CI`.

The verified pipeline uses a declarative Jenkinsfile and performs the following stages:

1. **Checkout:** Retrieves the source code from the GitHub `main` branch.
2. **Verify Environment:** Checks the availability and versions of Git, Bash, and tar.
3. **Validate Project Files:** Verifies that required files and directories exist.
4. **Package Source:** Creates a compressed source archive from the checked-out commit.
5. **Generate Checksum:** Calculates the SHA-256 checksum of the archive.
6. **Archive Artifacts:** Saves the generated files as Jenkins build artifacts.

The successful build produced:

- `releasenote-source.tar.gz`
- `SHA256SUMS`

The archive contains a source snapshot, while the checksum provides a means of checking the archive's integrity.

**Important implementation boundary:** The verified Jenkins pipeline performs source validation and packaging. It does not currently establish that the 78 Python tests were run within Jenkins, that a deployment was executed, or that a remote health endpoint was verified.

## 13. Terraform and Azure Infrastructure Design

The repository contains Terraform configuration intended to provision a Linux virtual machine and associated Azure networking resources.

The planned configuration includes a resource group, virtual network, subnet, network security group, public IP address, network interface, and Ubuntu virtual machine.

The intended security design restricts SSH access to configured source IP ranges and avoids exposing the Jenkins port through the application's VM security rules.

Terraform validation, planning, and resource creation must be executed against an appropriately configured Azure subscription. The presence of Terraform configuration files alone does not prove that the infrastructure was created.

**Current status:** Azure resource provisioning has not been verified as completed.

## 14. Planned Deployment Design

The intended deployment uses Nginx as the web server, Gunicorn as the Flask application server, systemd for service management, and SQLite for data storage.

The planned deployment script is designed to install application releases, preserve persistent application data, restart the service, verify application health, and roll back if a deployment check fails.

These are design objectives. The remote deployment, automatic rollback, and live health-check behavior must be executed and observed before being reported as verified results.

## 15. Security Considerations

The project includes security-related application controls such as input validation, parameterized SQL, CSRF protection, template auto-escaping, authentication for management operations, and security headers.

Additional deployment considerations include:

- Keeping secrets and private keys out of the Git repository.
- Restricting SSH access to approved source IP addresses.
- Storing deployment credentials securely.
- Configuring an administrator password hash before enabling public management operations.
- Using HTTPS for production deployment.
- Protecting Terraform state and other files containing sensitive infrastructure information.

The intended deployment architecture has limitations, including single-server availability, a shared management password, and HTTP-only access unless TLS is configured. These limitations should be addressed before production use.

## 16. Execution and Verification

The following results have been verified:

1. The GitHub Actions workflow completed successfully.
2. The verified workflow run executed 78 tests with zero failures and zero errors.
3. The workflow uploaded a JUnit XML report artifact.
4. The Jenkins `ReleaseNote-CI` pipeline completed successfully.
5. Jenkins validated the required project files.
6. Jenkins generated the source archive and SHA-256 checksum.

The following activities remain unverified:

- Successful execution of the test suite inside Jenkins.
- Terraform validation and resource provisioning in Azure.
- Remote application deployment.
- Automatic rollback following a failed deployment.
- Live health endpoint verification.
- End-to-end deployment triggered by a GitHub change.

These activities should be updated in the report only after execution evidence is available.

## 17. Observations and Actual Results

| Item | Observed result |
|---|---|
| GitHub repository | Available |
| GitHub Actions workflow | Successful |
| Automated tests | 78 |
| Test failures | 0 |
| Test errors | 0 |
| JUnit XML artifact | Uploaded successfully |
| Jenkins pipeline | Successful |
| Required project-file validation | Passed |
| Source archive | Generated |
| SHA-256 checksum | Generated |
| Jenkins execution of Python tests | Not verified |
| Terraform Azure provisioning | Not verified |
| Remote deployment | Not verified |
| Live health verification | Not verified |

The verified results demonstrate automated test execution and source packaging. They do not demonstrate a completed cloud deployment.

## 18. Limitations

The project currently has the following limitations:

- The Azure deployment has not been verified.
- The GitHub Actions and Jenkins workflows are separate.
- The verified Jenkins pipeline does not execute the Python test suite.
- Remote deployment and health verification remain unconfirmed.
- The intended infrastructure uses a single VM rather than a highly available architecture.
- SQLite is appropriate for a small application but may not suit a high-concurrency production system.
- HTTPS and automated TLS certificate management require additional configuration.
- Deployment rollback and production recovery need practical verification.

## 19. Future Enhancements

Potential improvements include:

1. Integrating automated testing and deployment through a unified CI/CD pipeline.
2. Running Pytest inside Jenkins and publishing JUnit results there.
3. Connecting Jenkins to GitHub through a tested webhook or polling configuration.
4. Provisioning Azure infrastructure using Terraform.
5. Deploying the application to a real Azure VM.
6. Verifying live application health after deployment.
7. Testing rollback using a controlled deployment failure.
8. Configuring HTTPS and a domain name.
9. Adding automated backups and improved database recovery.
10. Introducing role-based access control and more advanced release reporting.

## 20. Conclusion

ReleaseNote combines a software release-tracking application with automated testing and source packaging workflows. The verified GitHub Actions run executed 78 automated tests with zero failures and zero errors, while Jenkins successfully validated the repository structure and generated a source archive with a SHA-256 checksum.

The project also documents an intended infrastructure-as-code and cloud deployment path using Terraform and Microsoft Azure. Completing and verifying the cloud deployment would be the next major milestone. Maintaining a clear distinction between implemented functionality,
