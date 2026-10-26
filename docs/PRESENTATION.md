# ReleaseNote — Presentation Script and Slide Content

**Course:** DevOps (24DC2006)  
**Assessment:** IA-3  
**Project:** ReleaseNote — Automated Software Release Management and Changelog Tracking  
**Technology stack:** Flask, SQLite, Git, GitHub Actions, Jenkins, Terraform, Microsoft Azure

**Duration:** 8–10 minutes

---

## Slide 1 — Title

### ReleaseNote: Track Every Release. Automate Every Build.

- ReleaseNote — Automated Software Release Management and Changelog Tracking
- DevOps (24DC2006), IA-3
- Student name, roll number and team details

**Visual:** Actual ReleaseNote dashboard screenshot.

**Speaking script:**

“Good morning, respected faculty members. Our project is ReleaseNote, a software release tracking application developed as part of our DevOps assessment. It provides a centralized way to record, organize and review software releases. Alongside the application, we implemented automated testing through GitHub Actions and a Jenkins pipeline for source validation and packaging. Our objective is to combine application development with practical DevOps automation.”

## Slide 2 — Problem Statement and Objectives

### The Problem

- Release information can become scattered across documents and messages.
- Manually maintaining release history makes tracking changes difficult.
- Repeated manual verification can lead to inconsistent software delivery.
- Teams need reliable testing and traceable build artifacts.

### Our Objectives

- Centralize software release information.
- Provide searchable release history and release management.
- Run automated tests whenever changes are pushed to GitHub.
- Use Jenkins to validate project files and create a source package with a checksum.

**Visual:** A simple comparison: manual release tracking versus centralized tracking and automated validation.

**Speaking script:**

“The problem we address is the difficulty of maintaining organized release information and verifying software changes consistently. ReleaseNote provides a centralized application for tracking releases. We then extend the project with automated tests and a Jenkins pipeline so that important checks and packaging steps can be repeated consistently.”

## Slide 3 — Application Features

### Main Features

- Dashboard showing release statistics and recent activity.
- Searchable, filterable and sortable release history.
- Pagination for navigating release records.
- Create, view, edit and delete release entries.
- Input validation and duplicate-version protection.
- Authentication and CSRF protection for management operations.
- `/health` endpoint for application health and database checks.

**Visual:** Use actual screenshots of the dashboard, release history and a release detail page.

**Speaking script:**

“The application is built using Flask, with SQLite used to store release records. The dashboard provides a quick overview, while the history page supports search and filtering. Users can manage release information, including version numbers, release status, features and fixes. We also implemented validation, duplicate-version protection and security controls for management operations.”

## Slide 4 — System Architecture

### Architecture

**Application path:**

User → Flask application → SQLite database

**Automated testing path:**

Developer → GitHub repository → GitHub Actions → Automated tests → JUnit test report

**Jenkins pipeline:**

GitHub repository → Jenkins checkout → Environment verification → Project file validation → Source archive and checksum

**Infrastructure direction:** Terraform and Microsoft Azure are part of the planned infrastructure and deployment scope; a completed Azure deployment has not yet been verified.

**Visual:** Create a three-part architecture diagram with separate application, GitHub Actions and Jenkins flows. Mark Azure provisioning and deployment as planned rather than completed.

**Speaking script:**

“Our project has three main parts. First, the Flask application manages release records in SQLite. Second, GitHub Actions automatically runs our Python test suite and uploads a test report. Third, Jenkins checks out the source code, verifies the available environment, validates required project files and packages the source code with a SHA-256 checksum. These workflows demonstrate application development and CI automation without claiming an unverified cloud deployment.”

## Slide 5 — GitHub Actions: Automated Testing

### Workflow

1. Check out the repository.
2. Set up Python 3.12.
3. Install development dependencies.
4. Run the Pytest test suite.
5. Generate a JUnit XML report.
6. Upload the report as a workflow artifact.

### Verified Result

- **78 tests passed**
- **0 failures**
- **0 errors**
- **0 skipped tests**

**Visual:** Screenshot of the successful GitHub Actions run and the uploaded `releasenote-test-report` artifact.

**Speaking script:**

“We configured GitHub Actions to run the automated Python tests on pushes to the main branch and pull requests targeting main. The workflow installs the dependencies, executes Pytest and generates a JUnit XML report. Our verified run completed 78 tests with zero failures, zero errors and zero skipped tests. The report is uploaded as an artifact so that the results can be reviewed later.”

## Slide 6 — Jenkins CI Pipeline

### Pipeline Stages

1. **Checkout:** Retrieve the source from the main branch.
2. **Verify Environment:** Check the available Git, Bash and tar tools.
3. **Validate Project Files:** Confirm the required application, test, deployment and dependency files exist.
4. **Package Source:** Generate a compressed source archive.
5. **Generate Checksum:** Create a SHA-256 checksum file.
6. **Archive Artifacts:** Save the package and checksum in Jenkins.

### Output Artifacts

- `releasenote-source.tar.gz`
- `SHA256SUMS`

**Visual:** Jenkins successful build page, stage view if available, and archived artifacts.

**Speaking script:**

“Our Jenkins pipeline uses a declarative Pipeline script. It checks out the main branch, verifies the available tools and checks that required project files are present. It then creates a compressed source archive and generates a SHA-256 checksum. Jenkins archives both outputs so they can be retrieved from the build. The current Jenkins environment does not have Python installed, so Python testing is performed by GitHub Actions rather than being claimed as a Jenkins test stage.”

## Slide 7 — Source Packaging and Artifact Integrity

### What the Pipeline Produces

- A compressed snapshot of the Git source.
- A SHA-256 checksum for the generated archive.
- Build artifacts associated with the Jenkins run.
- A repeatable process for preparing source files.

### Why This Matters

- Archives make source distribution easier.
- Checksums help detect accidental changes to a downloaded archive.
- Build artifacts provide traceability for the pipeline output.

**Visual:** Jenkins artifact list showing both files.

**Speaking script:**

“After validation, Jenkins packages the source code into a compressed archive. It calculates the SHA-256 checksum and stores the result alongside the archive. A checksum can help verify that the archive has not changed after it was generated. This provides a useful foundation for artifact management. However, generating a checksum alone does not establish who produced the artifact or guarantee that the source is secure.”

## Slide 8 — Testing, Verification and Evidence

### Verification Summary

| Component | Verified outcome |
|---|---|
| Flask application | Project source and application structure available |
| GitHub Actions | 78 tests passed in the verified run |
| JUnit report | Generated and uploaded as an artifact |
| Jenkins checkout | Successful build |
| File validation | Required project files verified |
| Source packaging | Archive created successfully |
| SHA-256 checksum | Checksum file generated |
| Azure deployment | Not yet verified |

**Visual:** Use actual screenshots from GitHub Actions and Jenkins. Do not use fabricated screenshots or sample output presented as live evidence.

**Speaking script:**

“We verified the project using the actual outputs from the automation workflows. GitHub Actions provides the test results and JUnit report. Jenkins provides evidence of checkout, environment verification, project file validation and source packaging. We distinguish completed checks from future deployment work so that our results are reproducible and accurately reported.”

## Slide 9 — Limitations and Lessons Learned

### Current Limitations

- GitHub Actions and Jenkins are separate workflows.
- Jenkins currently validates and packages source code but does not run the Python tests in its current environment.
- Automatic deployment to an Azure virtual machine has not been verified.
- HTTPS, production infrastructure hardening and cloud health verification remain future work.

### Key Lessons

- Automated testing provides repeatable evidence of application correctness.
- CI pipelines should validate inputs before producing artifacts.
- Checksums support artifact-integrity verification.
- Documentation must distinguish implemented features from planned features.

**Speaking script:**

“One important lesson was that a pipeline should be described according to what it actually executes. Our GitHub Actions workflow provides automated Python testing, while Jenkins handles source validation and packaging in its current environment. We have not demonstrated a complete push-to-Azure deployment, so we identify that as future work rather than presenting it as a completed result.”

## Slide 10 — Conclusion and Future Enhancements

### Conclusion

- Developed a release tracking application using Flask and SQLite.
- Implemented automated testing with GitHub Actions.
- Verified 78 passing automated tests.
- Implemented Jenkins source validation, packaging and checksum generation.
- Documented the architecture, results and limitations.

### Future Enhancements

- Integrate automated tests into Jenkins by providing a suitable Python environment.
- Connect the CI pipeline to a controlled deployment workflow.
- Provision Azure infrastructure through Terraform.
- Add HTTPS, stronger production security and deployment health checks.
- Implement automated rollback and more comprehensive deployment verification.

**Speaking script:**

“To conclude, ReleaseNote combines a practical release tracking application with automated testing and source packaging. We demonstrated 78 passing tests in GitHub Actions and a successful Jenkins pipeline that generates source artifacts and a checksum. The next stage is to integrate these workflows and implement a verified cloud deployment. Thank you.”

---

# Live Demonstration Plan

Keep the demonstration to approximately two minutes.

1. Open the ReleaseNote application and show the dashboard.
2. Open the release history and demonstrate search or filtering.
3. Open the GitHub Actions page and show the successful run with 78 passing tests.
4. Show the uploaded JUnit report artifact.
5. Open the Jenkins `ReleaseNote-CI` job and show the successful build.
6. Show `releasenote-source.tar.gz` and `SHA256SUMS` in the archived artifacts.

**Important:** Demonstrate only features that open and work in the actual environment. Do not claim that an Azure VM, live cloud application, automatic rollback or end-to-end deployment is working unless you have verified it.

# Likely Viva Questions

**1. What is DevOps?**

DevOps combines development and operations practices to improve collaboration, automation, testing and software delivery.

**2. Why did you use Flask?**

Flask is a lightweight Python web framework suitable for building the application's routes, validation and web interface.

**3. Why SQLite?**

SQLite provides a simple relational database that stores release records without requiring a separate database server.

**4. What is CI?**

Continuous Integration automatically checks changes as developers integrate them into a shared repository. In our project, GitHub Actions runs the automated tests.

**5. What is the purpose of Jenkins?**

Jenkins automates the checkout, environment verification, project file validation and source packaging stages in our current pipeline.

**6. What is Terraform?**

Terraform is an infrastructure-as-code tool used to define and manage infrastructure through configuration files. A completed Azure provisioning run is not part of our verified results yet.

**7. What is a JUnit report?**

It is an XML-formatted test report containing test results, including counts of tests, failures and errors. Our GitHub Actions workflow generates and uploads one.

**8. Why generate a SHA-256 checksum?**

It allows a recipient to calculate the checksum of an archive and compare it with the recorded value to detect changes to the file.

**9. Does your project automatically deploy to Azure?**

Not in the currently verified implementation. GitHub Actions performs automated testing, and Jenkins validates and packages the source. Azure deployment remains a future enhancement.

**10. What is the main achievement of the project?**

The project demonstrates a release tracking application supported by automated Python testing and a Jenkins source-packaging pipeline, with verifiable reports and artifacts.

