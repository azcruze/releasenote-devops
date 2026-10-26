# ReleaseNote — Project Evidence

**Course:** DevOps (24DC2006)  
**Assessment:** IA-3  
**Project:** Automated Software Release Management and Changelog Tracking

## 1. GitHub Repository

**Repository:** https://github.com/azcruze/releasenote-devops

Evidence to capture:
- Repository overview and project structure.
- Commit history showing project development.
- README with architecture, setup instructions, and implementation status.

## 2. GitHub Actions — Automated Testing

**Workflow:** ReleaseNote Python Tests  
**Workflow file:** `.github/workflows/python-tests.yml`

**Verified result:**
- Tests executed: 78
- Failures: 0
- Errors: 0
- Skipped: 0
- Status: Success

**Workflow run:** https://github.com/azcruze/releasenote-devops/actions/runs/40289024445

Evidence to capture:
- Successful workflow summary.
- Test execution step showing the results.
- `releasenote-test-report` artifact.
- JUnit XML report showing the test totals.

## 3. Jenkins — CI Pipeline and Packaging

**Job:** ReleaseNote-CI

**Verified stages:**
1. Checkout source code from GitHub.
2. Verify the command-line environment.
3. Validate required project files.
4. Create a compressed source archive.
5. Generate a SHA-256 checksum.
6. Archive the build artifacts.

**Verified artifacts:**
- `releasenote-source.tar.gz`
- `SHA256SUMS`

Evidence to capture:
- Successful Jenkins build status.
- Console Output showing completed stages.
- Build artifacts displayed on the Jenkins build page.

## 4. Application Testing

The GitHub Actions workflow successfully executed 78 automated tests with zero failures and zero errors.

Evidence to capture:
- The GitHub Actions test summary.
- The downloadable JUnit XML report.

## 5. Terraform and Azure Deployment

**Status: Not yet verified as completed.**

If Terraform validation, planning, Azure provisioning, or deployment is performed later, add genuine evidence here.

Evidence to capture only if the relevant steps are executed:
- Terraform validation and plan output.
- Azure resources created.
- Deployment logs.
- Running application in the browser.
- Successful `/health` response from the deployed application.

Do not represent planned or unexecuted deployment steps as completed.

## 6. Final Implementation Status

| Component | Status |
|---|---|
| GitHub source repository | Available |
| GitHub Actions automated tests | Successful — 78 tests |
| JUnit XML test report | Uploaded as workflow artifact |
| Jenkins source checkout and validation | Successful |
| Jenkins source archive and checksum | Generated |
| Jenkins execution of Python tests | Not verified |
| Terraform Azure provisioning | Not verified |
| Remote application deployment | Not verified |
| Live health verification | Not verified |

## 7. Evidence Integrity

All screenshots and outputs submitted for assessment must come from actual executions of the project. Do not fabricate screenshots, test results, cloud resources, or deployment status.

Update this document when additional stages have been executed and verified.
