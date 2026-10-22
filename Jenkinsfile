// ReleaseNote CI/CD pipeline (Declarative). Jenkins agent must be Linux (uses `sh`).
// Required Jenkins credentials (Manage Jenkins > Credentials):
//   releasenote-azure-ssh  : "SSH Username with private key"  (user = azureuser, key = private key)
//   releasenote-vm-host    : "Secret text"                    (the VM's public IP or DNS name)
// Triggers are configured on the Jenkins job (GitHub hook trigger OR Poll SCM) - see docs/JENKINS.md.
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '5'))
        skipDefaultCheckout(true)
    }

    environment {
        VENV = '.venv'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHORT = sh(script: 'git rev-parse --short=8 HEAD', returnStdout: true).trim()
                    currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.GIT_SHORT}"
                    echo "Commit under build: ${env.GIT_SHORT} on ${env.GIT_BRANCH}"
                }
                sh 'git log -1 --pretty=format:"%h %an: %s"'
            }
        }

        stage('Verify Environment') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
for tool in python3 git ssh scp curl tar; do
  command -v "$tool" >/dev/null || { echo "Missing required tool on Jenkins agent: $tool"; exit 1; }
done
python3 --version
python3 -m venv --help >/dev/null || { echo "Install python3-venv on the Jenkins agent"; exit 1; }
rm -rf "$VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --disable-pip-version-check --upgrade pip
"$VENV/bin/pip" install --quiet --disable-pip-version-check -r requirements-dev.txt
"$VENV/bin/pip" list --format=freeze | grep -Ei '^(flask|gunicorn|pytest)=='
'''
            }
        }

        stage('Automated Tests') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports
"$VENV/bin/python" -m pytest --junitxml=reports/junit.xml
'''
            }
            post {
                always { junit allowEmptyResults: false, testResults: 'reports/junit.xml' }
            }
        }

        stage('Validate Build') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
"$VENV/bin/python" -m compileall -q app config.py wsgi.py
for f in deploy/*.sh; do bash -n "$f"; done
tmp="$(mktemp -d)"
DATABASE_PATH="$tmp/check.db" APP_ENV=testing "$VENV/bin/python" -c "from wsgi import app; c = app.test_client(); r = c.get('/health'); assert r.status_code == 200, r.status_code; print('Application imports and /health responds:', r.get_json()['status'])"
rm -rf "$tmp"
'''
            }
        }

        stage('Package') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
rm -rf dist stage && mkdir -p dist stage
git archive --format=tar HEAD app config.py wsgi.py gunicorn.conf.py requirements.txt deploy | tar -x -C stage
printf 'commit=%s\nbuild_number=%s\nbuilt_at=%s\n' "$GIT_SHORT" "$BUILD_NUMBER" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > stage/BUILD_INFO
tar -czf "dist/releasenote-${BUILD_NUMBER}-${GIT_SHORT}.tar.gz" -C stage .
sha256sum dist/*.tar.gz | tee dist/SHA256SUMS
'''
            }
            post {
                success { archiveArtifacts artifacts: 'dist/*', fingerprint: true }
            }
        }

        stage('Deploy to Azure VM') {
            when { expression { env.GIT_BRANCH ==~ /(origin\/)?main/ } }
            steps {
                withCredentials([
                    sshUserPrivateKey(credentialsId: 'releasenote-azure-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
                    string(credentialsId: 'releasenote-vm-host', variable: 'VM_HOST')
                ]) {
                    // Single-quoted: Groovy never interpolates secrets; the shell reads them from the environment.
                    sh '''#!/usr/bin/env bash
set -euo pipefail
RELEASE_ID="${BUILD_NUMBER}-${GIT_SHORT}"
ARTIFACT="releasenote-${RELEASE_ID}.tar.gz"
SSH_OPTS=(-i "$SSH_KEY" -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=20
          -o ServerAliveInterval=15 -o StrictHostKeyChecking=accept-new
          -o UserKnownHostsFile="${JENKINS_HOME:-$HOME}/.releasenote_known_hosts")

echo "Uploading $ARTIFACT"
timeout 300 scp "${SSH_OPTS[@]}" "dist/$ARTIFACT" "$SSH_USER@$VM_HOST:/tmp/$ARTIFACT"

echo "Deploying release $RELEASE_ID"
timeout 900 ssh "${SSH_OPTS[@]}" "$SSH_USER@$VM_HOST" "bash -s -- '$ARTIFACT' '$RELEASE_ID'" <<'REMOTE'
set -euo pipefail
ARTIFACT="$1"; RELEASE_ID="$2"
STAGE="/tmp/releasenote-stage-$RELEASE_ID"
rm -rf "$STAGE"; mkdir -p "$STAGE"
tar -xzf "/tmp/$ARTIFACT" -C "$STAGE"
rm -f "/tmp/$ARTIFACT"
sudo bash "$STAGE/deploy/deploy.sh" "$STAGE" "$RELEASE_ID"
REMOTE
'''
                }
            }
        }

        stage('Verify Deployment') {
            when { expression { env.GIT_BRANCH ==~ /(origin\/)?main/ } }
            steps {
                withCredentials([string(credentialsId: 'releasenote-vm-host', variable: 'VM_HOST')]) {
                    sh '''#!/usr/bin/env bash
set -euo pipefail
# Check the PUBLIC endpoint through Nginx, and confirm it serves THIS commit.
for attempt in $(seq 1 20); do
  body="$(curl -fsS --max-time 10 "http://$VM_HOST/health" 2>/dev/null || true)"
  if echo "$body" | grep -Eq '"status": ?"ok"' && echo "$body" | grep -Eq "\\"build\\": ?\\"$GIT_SHORT\\""; then
    echo "Public health check passed (attempt $attempt): $body"; exit 0
  fi
  echo "Attempt $attempt/20: not ready yet (${body:-no response})"; sleep 6
done
echo "Deployed application did not report status ok with build $GIT_SHORT" >&2
exit 1
'''
                }
            }
        }
    }

    post {
        success {
            echo "SUCCESS: build #${env.BUILD_NUMBER}, commit ${env.GIT_SHORT}. Tests passed; deployment verified."
        }
        failure {
            echo "FAILURE: build #${env.BUILD_NUMBER}, commit ${env.GIT_SHORT}. See the first failed stage. If a deployment failed, deploy.sh restored the previous release automatically."
        }
        always {
            sh 'rm -rf stage "$VENV" || true'
            echo "Result: ${currentBuild.currentResult}. Test report: ${env.BUILD_URL}testReport/"
        }
    }
}
