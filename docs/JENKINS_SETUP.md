## Jenkins + CI/CD Setup

Follow these steps to run the EquiHire pipeline on Jenkins (Docker-based setup assumed).

### 1. Start Jenkins in Docker

```bash
docker network create jenkins-net

docker run -d --name jenkins `
  -p 8080:8080 -p 50000:50000 `
  -v jenkins_home:/var/jenkins_home `
  -v /var/run/docker.sock:/var/run/docker.sock `
  -v "${PWD}:/workspace" `
  --network jenkins-net `
  jenkins/jenkins:lts-jdk17
```

*The Docker socket mount allows Jenkins to invoke `docker compose` on the host.*

### 2. First-Time Jenkins Setup

1. Browse to `http://localhost:8080/`.
2. Unlock Jenkins using `/var/jenkins_home/secrets/initialAdminPassword`.
3. Install “Suggested plugins”.
4. Create an admin user.
5. Install extra plugins: **Pipeline**, **Git**, **Docker**, **Docker Pipeline**.

### 3. Configure Tools Inside Jenkins

Inside Jenkins (Manage Jenkins → Tools):

| Tool              | Configuration                                           |
|-------------------|---------------------------------------------------------|
| Git               | Auto-install or point to system git                     |
| JDK               | Optional (pipeline uses system Python/Docker)           |
| Docker            | Point to `/usr/bin/docker` (inside container)           |
| Docker Compose    | Optional; pipeline shell commands call `docker compose` |

> Ensure the Jenkins container user belongs to the `docker` group (already true with the socket mount) so that `docker compose` commands succeed.

### 4. Create the Pipeline Job

1. **New Item → Pipeline** (name: `equihire-ci`).
2. Under **Pipeline** section choose:
   - *Definition*: “Pipeline script from SCM”.
   - *SCM*: Git.
   - *Repository URL*: your repo URL (HTTPS or SSH).
   - *Script Path*: `Jenkinsfile`.
3. Save the job.

### 5. Required Jenkins Node Capabilities

The Jenkins agent that runs the pipeline must have:

- Docker Engine + Docker Compose v2 (`docker compose` CLI).
- Python 3.11+ (for Selenium tests when run on the host).
- Chrome/Chromedriver or another browser driver if Selenium tests rely on a real browser (alternatively update tests to use a remote Selenium Grid).
- Curl (used in pipeline health checks).

### 6. Running the Pipeline

1. Trigger a build (`Build Now`).
2. Pipeline stages:
   - Checkout repo.
   - Build Docker images (`docker compose build`).
   - Run Django unit tests inside the `django_app` container.
   - Bring up the entire stack with `docker compose up -d`.
   - Wait for the API health endpoint to respond.
   - Create a local Python venv and execute Selenium tests against `http://localhost:8000`.
   - Tear down the stack (`docker compose down -v`).
3. Review console output for test results.

### 7. Optional Enhancements

- Use Jenkins credentials to pull from a private repo.
- Add Slack/email notifications in the Jenkinsfile `post` section.
- Publish JUnit or Allure reports (`pytest --junitxml=reports/selenium.xml`) and archive artifacts.
- Spin up a Selenium Grid in Docker and point tests to it.

### 8. Troubleshooting

- **`docker compose: command not found`** → install Docker CLI with Compose V2 in the Jenkins container or change commands to `docker-compose`.
- **Ports already in use** → ensure no other stack (local `docker compose up`) is running when Jenkins executes the pipeline.
- **Selenium failures due to missing browser** → install Chrome/Chromedriver inside Jenkins agent or switch to headless drivers (e.g., `webdriver_manager`).
- **Long-lived containers** → the pipeline always runs `docker compose down -v` in the `post` block to keep the workspace clean; if it fails, clean manually.

With the Jenkinsfile and these setup steps, the CI/CD pipeline becomes fully automated: every build spins up the EquiHire stack, runs unit + Selenium tests, and tears everything down. Trigger builds manually or hook Jenkins to your Git provider (webhooks/Poll SCM) for continuous integration.

