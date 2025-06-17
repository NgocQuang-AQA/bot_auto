# CI/CD Pipeline Documentation

This document provides comprehensive information about the GitLab CI/CD pipeline setup for the Bot Slack Service.

## 📋 Table of Contents

- [Overview](#overview)
- [Pipeline Stages](#pipeline-stages)
- [Environment Setup](#environment-setup)
- [GitLab Variables](#gitlab-variables)
- [Docker Configuration](#docker-configuration)
- [Deployment Process](#deployment-process)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Best Practices](#best-practices)

## 🔍 Overview

The CI/CD pipeline automates the build, test, security scan, and deployment processes for the Bot Slack Service. It supports multiple environments (development, staging, production) and includes comprehensive testing and security checks.

### Pipeline Features

- ✅ **Automated Building**: Docker image creation and Python compilation
- ✅ **Comprehensive Testing**: Unit tests, integration tests, and code quality checks
- ✅ **Security Scanning**: Dependency vulnerability checks and code security analysis
- ✅ **Multi-Environment Deployment**: Support for staging and production environments
- ✅ **Rollback Capability**: Quick rollback to previous versions
- ✅ **Health Monitoring**: Automated health checks and status monitoring
- ✅ **Notifications**: Slack notifications for pipeline status

## 🚀 Pipeline Stages

### 1. Build Stage

#### `build:docker`
- Builds Docker images using the Dockerfile
- Pushes images to GitLab Container Registry
- Tags images with commit SHA and `latest`
- Runs on: `main`, `develop`, `merge_requests`

#### `build:python`
- Compiles Python files to check for syntax errors
- Installs dependencies and validates requirements
- Creates build artifacts
- Runs on: `main`, `develop`, `merge_requests`

### 2. Test Stage

#### `test:unit`
- Runs unit tests using pytest
- Generates code coverage reports
- Creates coverage artifacts and reports
- Coverage threshold: Configurable via pipeline

#### `test:integration`
- Starts Docker container with the built image
- Performs integration tests against running service
- Tests health endpoints and API functionality

#### `test:lint`
- Code quality checks using flake8, black, and isort
- Ensures code follows Python standards
- Allows failure (won't block pipeline)

### 3. Security Stage

#### `security:dependency-scan`
- Scans dependencies for known vulnerabilities using Safety
- Performs static code analysis using Bandit
- Generates security reports

#### `security:docker-scan`
- Scans Docker images for vulnerabilities
- Can be extended with tools like Trivy or Clair

### 4. Deploy Stage

#### `deploy:staging`
- Deploys to staging environment
- Manual trigger required
- Runs on `develop` branch

#### `deploy:production`
- Deploys to production environment
- Manual trigger required
- Runs on `main` branch only

#### `deploy:rollback`
- Rolls back to previous version
- Manual trigger
- Available for production environment

### 5. Cleanup Stage

#### `cleanup:docker`
- Removes unused Docker images and containers
- Frees up storage space
- Manual trigger

## ⚙️ Environment Setup

### Prerequisites

1. **GitLab Runner**: Configured with Docker executor
2. **Docker Registry**: GitLab Container Registry enabled
3. **Target Servers**: Configured with Docker and Docker Compose
4. **SSH Access**: Key-based authentication to deployment servers

### GitLab Runner Configuration

```toml
[[runners]]
  name = "docker-runner"
  url = "https://gitlab.com/"
  token = "your-runner-token"
  executor = "docker"
  [runners.docker]
    image = "docker:20.10.16"
    privileged = true
    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
```

## 🔐 GitLab Variables

Configure the following variables in GitLab Project Settings > CI/CD > Variables:

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|----------|
| `SSH_PRIVATE_KEY` | File | SSH private key for deployment | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `DEPLOY_HOST` | Variable | Target deployment server | `your-server.com` |
| `DEPLOY_USER` | Variable | SSH user for deployment | `deploy` |
| `DEPLOY_PATH` | Variable | Application path on server | `/opt/bot-slack` |

### Optional Variables

| Variable | Type | Description | Default |
|----------|------|-------------|----------|
| `SLACK_WEBHOOK_URL` | Variable | Slack webhook for notifications | - |
| `CI_REGISTRY_IMAGE` | Variable | Docker registry image path | Auto-generated |
| `DOCKER_TLS_CERTDIR` | Variable | Docker TLS certificate directory | `/certs` |

### Environment-Specific Variables

Create environment-specific variables for staging and production:

```bash
# Staging
STAGING_DEPLOY_HOST=staging.your-server.com
STAGING_DEPLOY_PATH=/opt/bot-slack-staging

# Production
PRODUCTION_DEPLOY_HOST=your-server.com
PRODUCTION_DEPLOY_PATH=/opt/bot-slack
```

## 🐳 Docker Configuration

### Registry Setup

The pipeline uses GitLab Container Registry. Ensure it's enabled:

1. Go to Project Settings > General > Visibility
2. Enable "Container Registry"
3. Configure registry cleanup policies if needed

### Image Tagging Strategy

- `latest`: Latest stable version (from main branch)
- `staging`: Staging version (from develop branch)
- `{commit-sha}`: Specific commit version
- `dev`: Development version (local builds)

### Docker Compose Environments

#### Production (`docker-compose.yml`)
```yaml
services:
  bot-slack:
    image: ${CI_REGISTRY_IMAGE}/bot-slack:${IMAGE_TAG:-latest}
    # ... other configuration
```

#### Development (`docker-compose.override.yml`)
```yaml
services:
  bot-slack:
    build:
      context: ..
      dockerfile: deployment/Dockerfile
    # ... development-specific configuration
```

## 🚀 Deployment Process

### Automatic Deployment

1. **Code Push**: Push code to `develop` or `main` branch
2. **Pipeline Trigger**: GitLab automatically starts the pipeline
3. **Build & Test**: All stages run automatically
4. **Manual Deploy**: Click "Deploy" button for staging/production

### Manual Deployment

Using the deployment script:

```bash
# Deploy to staging
./deployment/deploy.sh staging deploy

# Deploy to production
./deployment/deploy.sh production deploy

# Check status
./deployment/deploy.sh production status

# View logs
./deployment/deploy.sh production logs

# Rollback
./deployment/deploy.sh production rollback
```

### Deployment Checklist

- [ ] Environment variables configured
- [ ] SSH keys added to GitLab
- [ ] Target server accessible
- [ ] Docker and Docker Compose installed on target
- [ ] `.env` file created on target server
- [ ] Firewall rules configured
- [ ] Health check endpoint accessible

## 📊 Monitoring & Troubleshooting

### Pipeline Monitoring

1. **GitLab Pipeline View**: Monitor pipeline progress
2. **Job Logs**: Check individual job outputs
3. **Artifacts**: Download test reports and coverage
4. **Environments**: Track deployment status

### Health Checks

The pipeline includes automated health checks:

```bash
# Manual health check
curl -f http://your-server.com/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Common Issues

#### Build Failures

```bash
# Check Docker daemon
docker info

# Check disk space
df -h

# Clean up Docker
docker system prune -f
```

#### Deployment Failures

```bash
# Check SSH connectivity
ssh deploy@your-server.com

# Check Docker Compose
docker-compose ps
docker-compose logs

# Check service status
systemctl status docker
```

#### Test Failures

```bash
# Run tests locally
python -m pytest test_api.py -v

# Check test coverage
python -m pytest --cov=app --cov-report=html

# Lint code
flake8 app/ services/ utils/
black --check app/ services/ utils/
```

### Debugging Pipeline

1. **Enable Debug Mode**: Add `CI_DEBUG_TRACE: "true"` to variables
2. **Check Runner Logs**: View GitLab Runner logs
3. **Test Locally**: Use `gitlab-runner exec docker job-name`
4. **Validate YAML**: Use GitLab CI Lint tool

## 🎯 Best Practices

### Security

- ✅ Use protected variables for sensitive data
- ✅ Rotate SSH keys regularly
- ✅ Enable branch protection rules
- ✅ Use least privilege principle for deployment users
- ✅ Scan dependencies regularly

### Performance

- ✅ Use Docker layer caching
- ✅ Optimize Docker images (multi-stage builds)
- ✅ Cache dependencies between pipeline runs
- ✅ Run tests in parallel when possible
- ✅ Use appropriate runner resources

### Reliability

- ✅ Implement proper health checks
- ✅ Use blue-green or rolling deployments
- ✅ Maintain rollback capability
- ✅ Monitor application metrics
- ✅ Set up alerting for failures

### Code Quality

- ✅ Maintain high test coverage (>80%)
- ✅ Use code quality gates
- ✅ Implement pre-commit hooks
- ✅ Follow semantic versioning
- ✅ Write meaningful commit messages

## 📚 Additional Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [Slack API Documentation](https://api.slack.com/)

## 🆘 Support

For issues with the CI/CD pipeline:

1. Check this documentation
2. Review GitLab pipeline logs
3. Contact the DevOps team
4. Create an issue in the project repository

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: DevOps Team