
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(
            numToKeepStr: '20',
            artifactNumToKeepStr: '5'
        ))
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
                    env.GIT_SHORT = sh(
                        script: 'git rev-parse --short=8 HEAD',
                        returnStdout: true
                    ).trim()

                    currentBuild.displayName =
                        "#${env.BUILD_NUMBER} ${env.GIT_SHORT}"

                    echo "Building commit ${env.GIT_SHORT}"
                }

                sh 'git log -1 --pretty=format:"%h %an: %s"'
            }
        }

        stage('Verify Environment') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail

echo "Checking required tools..."

for tool in python3 git tar; do
    command -v "$tool" >/dev/null || {
        echo "Missing required tool: $tool"
        exit 1
    }
done

python3 --version
git --version
tar --version | head -n 1

python3 -m venv --help >/dev/null || {
    echo "Python virtual environment support is missing."
    exit 1
}

echo "Creating Python virtual environment..."

python3 -m venv "$VENV"

"$VENV/bin/python" -m pip install \
    --disable-pip-version-check \
    --upgrade pip

echo "Installing project dependencies..."

"$VENV/bin/python" -m pip install \
    --disable-pip-version-check \
    -r requirements-dev.txt

echo "Dependency installation completed."
'''
            }
        }

        stage('Automated Tests') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports

"$VENV/bin/python" -m pytest -v \
    --junitxml=reports/junit.xml
'''
            }

            post {
                always {
                    junit(
                        allowEmptyResults: true,
                        testResults: 'reports/junit.xml'
                    )
                }
            }
        }

        stage('Validate Build') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail

echo "Checking Python syntax..."

"$VENV/bin/python" -m compileall -q \
    app config.py wsgi.py

echo "Checking deployment shell scripts..."

for f in deploy/*.sh; do
    if [ -f "$f" ]; then
        bash -n "$f"
    fi
done

echo "Checking application health endpoint..."

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

DATABASE_PATH="$tmp/check.db" \
APP_ENV=testing \
"$VENV/bin/python" -c "
from wsgi import app
client = app.test_client()
response = client.get('/health')
assert response.status_code == 200, response.status_code
print('Health endpoint:', response.status_code)
print(response.get_json())
"
'''
            }
        }

        stage('Package') {
            steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail

rm -rf dist stage
mkdir -p dist stage

git archive --format=tar HEAD \
    app config.py wsgi.py gunicorn.conf.py \
    requirements.txt deploy |
    tar -x -C stage

printf 'commit=%s\\nbuild_number=%s\\nbuilt_at=%s\\n' \
    "$GIT_SHORT" \
    "$BUILD_NUMBER" \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    > stage/BUILD_INFO

ARTIFACT="releasenote-${BUILD_NUMBER}-${GIT_SHORT}.tar.gz"

tar -czf "dist/$ARTIFACT" -C stage .

sha256sum dist/*.tar.gz | tee dist/SHA256SUMS

echo "Package created: $ARTIFACT"
'''
            }

            post {
                success {
                    archiveArtifacts(
                        artifacts: 'dist/*',
                        fingerprint: true
                    )
                }
            }
        }
    }

    post {
        success {
            echo "CI SUCCESS: Build #${env.BUILD_NUMBER}, commit ${env.GIT_SHORT}. Tests, validation and packaging completed."
        }

        failure {
            echo "CI FAILURE: Build #${env.BUILD_NUMBER}. Check the first failed stage in Console Output."
        }

        always {
            sh 'rm -rf stage "$VENV" || true'
            echo "Final build result: ${currentBuild.currentResult}"
        }
    }
}
