# js-libp2p Universal Connectivity Workshop Setup

Welcome to the js-libp2p Universal Connectivity Workshop! This guide will help you set up your development environment.

## Prerequisites

Before starting, ensure you have the following tools installed:

- **Node.js**: Version 18 LTS or higher
- **npm**: Version 9 or higher
- **Docker & Docker Compose**: Required for running the connectivity checks
- **Git**: For version control

## Environment Setup

### Step 1: Verify Dependencies

Run the dependency checker to make sure your environment is ready:

```bash
cd en/js
python3 deps.py
```

You should see all green checkmarks (✓) for the required tools.

### Step 2: Configure Docker Network

The workshop requires a shared Docker network for nodes to communicate. Create it manually:

```bash
docker network create --subnet=172.16.16.0/24 --gateway=172.16.16.1 workshop-net
```

If the network already exists, you can proceed. If you suspect issues, remove it (`docker network rm workshop-net`) and recreate it.

### Step 3: Prepare the Checker Image

The workshop uses a unified checker image to validate your lessons. Pull the pre-built image:

```bash
docker pull ghcr.io/libp2p/universal-connectivity-workshop/ucw-checker-en:latest
```

## Workshop Structure

Each lesson directory (e.g., `en/js/01-identity-and-swarm`) contains:

- `app/`: Your application code (this is where you write code)
- `lesson.md`: Detailed instructions for the lesson
- `docker-compose.yaml`: Configuration to run your node and the checker
- `check.py`: Script to validate your solution

## Running Lessons

The lessons are designed to run in Docker containers. This ensures a consistent environment for network testing.

### Standard Workflow

To run a lesson (e.g., Lesson 1), follow these steps:

1. **Set Environment Variables**
   The Docker configuration needs to know where the project root is. Run this from the repository root:
   
   ```bash
   export PROJECT_ROOT=$(git rev-parse --show-toplevel)
   ```

2. **Navigate to the Lesson**
   
   ```bash
   export LESSON_PATH=en/js/01-identity-and-swarm
   cd $PROJECT_ROOT/$LESSON_PATH
   ```

3. **Start the Environment**
   First, create the log file to ensure Docker mounts it correctly, then start the container:
   
   ```bash
   touch stdout.log
   docker compose up -d --build
   ```

4. **Run the Checker**
   This verifies your solution matches the requirements:
   
   ```bash
   python3 check.py
   ```

5. **Cleanup**
   Stop the containers and remove volumes to prepare for the next run:
   
   ```bash
   docker compose down -v
   ```

### Local Development (IntelliSense)

While the code runs in Docker, you'll edit it locally. To get code completion and type hints in your editor:

```bash
cd app
npm install
```

This installs the dependencies locally so your IDE can understand the imports.

## Troubleshooting

**"Variable is not set" errors:**
If Docker complains about `PROJECT_ROOT` or `LESSON_PATH` not being set, ensure you ran the `export` commands in your current terminal session.

**"Is a directory" error for stdout.log:**
If you see an error saying `stdout.log` is a directory, it means Docker created a directory instead of a file.
Fix it by running:
```bash
rm -rf stdout.log
touch stdout.log
```
Then try `docker compose up` again.

**Network conflicts:**
If you see errors about IP addresses being in use:
```bash
docker network rm workshop-net
docker network create --subnet=172.16.16.0/24 --gateway=172.16.16.1 workshop-net
```
