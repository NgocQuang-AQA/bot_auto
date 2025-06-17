# Quick Docker Start Guide

## 🚀 Fast Setup (Windows)

### Step 1: Ensure Docker is Running
- Start Docker Desktop
- Verify: Open PowerShell and run `docker --version`

### Step 2: Configure Environment
```cmd
copy .env.example .env
# Edit .env file with your Slack credentials
```

### Step 3: Build & Run (Choose One Method)

#### Method A: Using PowerShell Script (Recommended)
```powershell
# Build the image
.\build-docker.ps1

# Run the container
docker run -d -p 5000:5000 --env-file .env --name bot-slack-container bot-slack:latest
```

#### Method B: Using Batch Script
```cmd
# Build the image
.\build-docker.bat

# Run the container
docker run -d -p 5000:5000 --env-file .env --name bot-slack-container bot-slack:latest
```

#### Method C: Using Makefile
```cmd
# Build and run
make docker-build
make docker-run

# Or for development
make docker-build-dev
make docker-run-dev
```

#### Method D: Using Docker Compose (Production)
```cmd
docker-compose -f deployment\docker-compose.yml up -d
```

### Step 4: Verify
- Check container: `docker ps`
- Test health: `curl http://localhost:5000/health`
- View logs: `docker logs bot-slack-container`

## 🛠️ Quick Commands

```cmd
# Stop container
docker stop bot-slack-container

# View logs
docker logs -f bot-slack-container

# Access container shell
docker exec -it bot-slack-container bash

# Remove container
docker rm -f bot-slack-container

# List images
docker images bot-slack
```

## 🔧 Troubleshooting

**Docker not found?**
- Install Docker Desktop from docker.com
- Restart your terminal after installation

**Port 5000 busy?**
```cmd
docker run -d -p 5001:5000 --env-file .env --name bot-slack-container bot-slack:latest
```

**Build fails?**
- Check if you're in the project root directory
- Ensure `requirements.txt` and `deployment/Dockerfile` exist
- Try: `.\build-docker.ps1 -NoBuildCache`

**Container exits immediately?**
```cmd
docker logs bot-slack-container
# Check the error messages
```

## 📚 More Details

For comprehensive documentation, see:
- `DOCKER-GUIDE.md` - Complete Docker guide
- `docs/CI-CD-README.md` - CI/CD setup
- `Makefile` - All available commands

---

**Need help?** Check the logs first: `docker logs bot-slack-container`