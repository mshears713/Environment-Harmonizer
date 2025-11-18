# Environment Harmonizer - Quick Start Guide

Get up and running with Environment Harmonizer in Docker on Windows, WSL, or Linux in just a few minutes!

## Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux/WSL)
  - Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - WSL: [Install Docker in WSL](https://docs.docker.com/desktop/windows/wsl/)
  - Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)
  - macOS: [Download Docker Desktop](https://docs.docker.com/desktop/mac/install/)

## Quick Start (Automated)

### Windows (PowerShell or CMD)

```cmd
# Clone the repository
git clone https://github.com/mshears713/Environment-Harmonizer.git
cd Environment-Harmonizer

# Run the quick start script
quickstart-windows.bat
```

### Linux / WSL / macOS

```bash
# Clone the repository
git clone https://github.com/mshears713/Environment-Harmonizer.git
cd Environment-Harmonizer

# Run the quick start script
./quickstart.sh
```

The script will:
1. Check if Docker is installed and running
2. Build the Docker image
3. Present you with options to scan your project

## Manual Quick Start

### 1. Build the Docker Image

```bash
# From the Environment-Harmonizer directory
docker build -t environment-harmonizer:latest .
```

Or using docker-compose:

```bash
docker-compose build
```

### 2. Run Environment Harmonizer

#### Scan Current Directory

**Windows (CMD):**
```cmd
docker run --rm -v "%cd%":/workspace environment-harmonizer:latest
```

**Windows (PowerShell):**
```powershell
docker run --rm -v "${PWD}:/workspace" environment-harmonizer:latest
```

**Linux / WSL / macOS:**
```bash
docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest
```

#### Scan a Specific Directory

**Windows:**
```cmd
docker run --rm -v "C:\path\to\project":/workspace environment-harmonizer:latest
```

**Linux / WSL / macOS:**
```bash
docker run --rm -v /path/to/project:/workspace environment-harmonizer:latest
```

## Common Usage Patterns

### Scan with Verbose Output

```bash
# Linux/WSL/macOS
docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest --verbose

# Windows (CMD)
docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --verbose
```

### Preview Fixes (Dry Run)

```bash
# Linux/WSL/macOS
docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest --fix --dry-run

# Windows (CMD)
docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --fix --dry-run
```

### Apply Fixes

```bash
# Linux/WSL/macOS
docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest --fix

# Windows (CMD)
docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --fix
```

### Generate JSON Report

```bash
# Linux/WSL/macOS
docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest --json --output report.json

# Windows (CMD)
docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --json --output report.json
```

## Using Docker Compose

Docker Compose simplifies the command syntax:

### Scan Current Directory

```bash
docker-compose run --rm harmonizer
```

### Scan with Custom Arguments

```bash
docker-compose run --rm harmonizer --verbose
docker-compose run --rm harmonizer --fix --dry-run
docker-compose run --rm harmonizer --json --output report.json
```

### Scan a Different Project

```bash
# Set the project path and run
PROJECT_PATH=/path/to/your/project docker-compose run --rm harmonizer-scan
```

## Creating a Shell Alias (Optional)

For easier usage, create a shell alias:

### Linux / WSL / macOS

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias harmonizer='docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest'
```

Then use it like:

```bash
harmonizer
harmonizer --verbose
harmonizer --fix --dry-run
```

### Windows (PowerShell)

Add to your PowerShell profile:

```powershell
function harmonizer { docker run --rm -v "${PWD}:/workspace" environment-harmonizer:latest $args }
```

Then use it like:

```powershell
harmonizer
harmonizer --verbose
harmonizer --fix --dry-run
```

## Interactive Shell

To get an interactive shell inside the container:

```bash
# Linux/WSL/macOS
docker run --rm -it -v "$(pwd)":/workspace --entrypoint /bin/bash environment-harmonizer:latest

# Windows (CMD)
docker run --rm -it -v "%cd%":/workspace --entrypoint /bin/bash environment-harmonizer:latest
```

From there, you can run:

```bash
harmonizer --help
harmonizer .
python -m harmonizer --verbose
```

## Troubleshooting

### Docker Not Running

**Error:** `Cannot connect to the Docker daemon`

**Solution:**
- Windows/Mac: Start Docker Desktop
- Linux/WSL: `sudo systemctl start docker`

### Permission Denied

**Error:** `Permission denied` when running on Linux/WSL

**Solution:**
- Add your user to the docker group: `sudo usermod -aG docker $USER`
- Log out and back in
- Or run with sudo: `sudo docker run ...`

### Volume Mount Issues on Windows

**Error:** Files not appearing in container

**Solution:**
- Ensure drive sharing is enabled in Docker Desktop settings
- Use absolute paths: `docker run --rm -v "C:\full\path":/workspace ...`
- Check Docker Desktop → Settings → Resources → File Sharing

### WSL Path Issues

**Error:** Cannot access Windows paths in WSL

**Solution:**
- Use WSL paths: `/mnt/c/Users/...` instead of `C:\Users\...`
- Or use `$(wslpath -a "C:\Users\...")` to convert paths

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Check out [examples](examples/) for sample projects
- Explore the CLI options with `--help`:
  ```bash
  docker run --rm environment-harmonizer:latest --help
  ```

## Advanced Usage

### Building for Different Platforms

```bash
# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t environment-harmonizer:latest .
```

### Pushing to a Registry

```bash
# Tag and push to Docker Hub
docker tag environment-harmonizer:latest username/environment-harmonizer:latest
docker push username/environment-harmonizer:latest
```

### Development Mode

Mount the source code for live development:

```bash
docker run --rm -it \
  -v "$(pwd)":/workspace \
  -v "$(pwd)/harmonizer":/usr/local/lib/python3.11/site-packages/harmonizer \
  environment-harmonizer:latest --verbose
```

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/mshears713/Environment-Harmonizer/issues
- Documentation: See README.md

---

**Happy Harmonizing!** 🎵
