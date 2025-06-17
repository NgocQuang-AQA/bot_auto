# Docker Guide for Bot Slack Project

This guide will help you dockerize and run the Bot Slack project using Docker.

## Prerequisites

1. **Docker Desktop**: Make sure Docker Desktop is installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Verify installation: `docker --version`

2. **Environment Configuration**: Copy and configure your environment file
   ```bash
   cp .env.example .env
   # Edit .env with your Slack credentials and configuration
   ```

## Quick Start

### Option 1: Using Batch Script (Windows)

```cmd
# Build the Docker image
.\build-docker.bat

# Run the container
docker run -d -p 5000:5000 --env-file .env --name bot-slack-container bot-slack:latest
```

### Option 2: Using PowerShell Script (Recommended)

```powershell
# Basic build
.\build-docker.ps1

# Build with custom tag
.\build-docker.ps1 -Tag "v1.0.0"

# Build for development with no cache
.\build-docker.ps1 -Tag "dev" -Environment "development" -NoBuildCache

# Verbose build output
.\build-docker.ps1 -Verbose
```

### Option 3: Using Docker Compose (Recommended for Production)

```bash
# Production deployment
docker-compose -f deployment/docker-compose.yml up -d

# Development with override
docker-compose -f deployment/docker-compose.yml -f deployment/docker-compose.override.yml up -d

# View logs
docker-compose -f deployment/docker-compose.yml logs -f

# Stop services
docker-compose -f deployment/docker-compose.yml down
```

## Manual Docker Commands

### Building the Image

```bash
# Basic build
docker build -t bot-slack:latest -f deployment/Dockerfile .

# Build with build arguments
docker build -t bot-slack:v1.0.0 \
  --build-arg ENVIRONMENT=production \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VERSION=v1.0.0 \
  -f deployment/Dockerfile .

# Build without cache
docker build --no-cache -t bot-slack:latest -f deployment/Dockerfile .
```

### Running the Container

```bash
# Basic run
docker run -d -p 5000:5000 --name bot-slack-container bot-slack:latest

# Run with environment file
docker run -d -p 5000:5000 --env-file .env --name bot-slack-container bot-slack:latest

# Run with custom environment variables
docker run -d -p 5000:5000 \
  -e SLACK_BOT_TOKEN=your_token \
  -e SLACK_APP_TOKEN=your_app_token \
  -e FLASK_ENV=production \
  --name bot-slack-container \
  bot-slack:latest

# Run with volume for persistent data
docker run -d -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --name bot-slack-container \
  bot-slack:latest
```

### Container Management

```bash
# View running containers
docker ps

# View all containers
docker ps -a

# View container logs
docker logs bot-slack-container

# Follow logs in real-time
docker logs -f bot-slack-container

# Execute commands in running container
docker exec -it bot-slack-container bash

# Stop container
docker stop bot-slack-container

# Start stopped container
docker start bot-slack-container

# Remove container
docker rm bot-slack-container

# Remove container forcefully
docker rm -f bot-slack-container
```

### Image Management

```bash
# List images
docker images

# List bot-slack images only
docker images bot-slack

# Remove image
docker rmi bot-slack:latest

# Remove all unused images
docker image prune

# Remove all unused images (including tagged)
docker image prune -a
```

## Environment Configuration

### Required Environment Variables

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# Flask Configuration
FLASK_ENV=production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# Application Configuration
APP_MODE=prod
LOG_LEVEL=INFO
```

### Development vs Production

**Development:**
```bash
# Use override file for development
docker-compose -f deployment/docker-compose.yml -f deployment/docker-compose.override.yml up -d
```

**Production:**
```bash
# Use production configuration
docker-compose -f deployment/docker-compose.yml up -d
```

## Health Checks

### Container Health

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' bot-slack-container

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' bot-slack-container
```

### Application Health

```bash
# Test health endpoint
curl http://localhost:5000/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

## Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   # Start Docker Desktop or Docker service
   # Windows: Start Docker Desktop application
   # Linux: sudo systemctl start docker
   ```

2. **Port already in use**
   ```bash
   # Find process using port 5000
   netstat -ano | findstr :5000
   
   # Use different port
   docker run -d -p 5001:5000 --env-file .env --name bot-slack-container bot-slack:latest
   ```

3. **Build fails due to missing files**
   ```bash
   # Make sure you're in the project root directory
   # Check if required files exist
   ls -la requirements.txt deployment/Dockerfile
   ```

4. **Container exits immediately**
   ```bash
   # Check container logs
   docker logs bot-slack-container
   
   # Run container interactively for debugging
   docker run -it --env-file .env bot-slack:latest bash
   ```

5. **Permission issues**
   ```bash
   # On Linux/Mac, fix file permissions
   chmod +x build-docker.ps1
   
   # Or run with explicit permissions
   bash build-docker.sh
   ```

### Debug Mode

```bash
# Run container in debug mode
docker run -it --env-file .env \
  -e FLASK_DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  -p 5000:5000 \
  -p 5678:5678 \
  bot-slack:latest
```

### Logs and Monitoring

```bash
# View application logs
docker logs -f bot-slack-container

# View logs with timestamps
docker logs -t bot-slack-container

# View last 100 lines
docker logs --tail 100 bot-slack-container

# Export logs to file
docker logs bot-slack-container > bot-slack.log 2>&1
```

## Performance Optimization

### Resource Limits

```bash
# Run with resource limits
docker run -d -p 5000:5000 \
  --memory=512m \
  --cpus=1.0 \
  --env-file .env \
  --name bot-slack-container \
  bot-slack:latest
```

### Multi-stage Build (Advanced)

The Dockerfile already uses optimization techniques:
- Multi-layer caching
- Non-root user
- Minimal base image
- Health checks

## Security Best Practices

1. **Use non-root user** (already implemented)
2. **Limit container capabilities**
   ```bash
   docker run -d --cap-drop=ALL --cap-add=NET_BIND_SERVICE -p 5000:5000 bot-slack:latest
   ```

3. **Use secrets for sensitive data**
   ```bash
   # Use Docker secrets instead of environment variables for production
   docker secret create slack_bot_token slack_bot_token.txt
   ```

4. **Regular security scans**
   ```bash
   # Scan image for vulnerabilities
   docker scan bot-slack:latest
   ```

## CI/CD Integration

The project includes GitLab CI/CD configuration:
- Automated builds
- Security scanning
- Multi-environment deployment
- Rollback capabilities

See `docs/CI-CD-README.md` for detailed CI/CD setup instructions.

## Support

If you encounter issues:
1. Check the logs: `docker logs bot-slack-container`
2. Verify environment configuration
3. Ensure Docker Desktop is running
4. Check port availability
5. Review the troubleshooting section above

For development, use the override configuration to enable hot reloading and debugging features.