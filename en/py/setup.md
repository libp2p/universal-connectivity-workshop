# py-libp2p Universal Connectivity Workshop Setup

Welcome to the py-libp2p Universal Connectivity Workshop! This guide will help you set up your development environment.

## Prerequisites

- Python 3.8 or higher
- Basic knowledge of Python async/await
- Familiarity with networking concepts (optional but helpful)
- Text editor or IDE of your choice

## Environment Setup

### Step 1: Create a Workshop Directory

Create a new directory for your workshop projects:

```bash
mkdir py-libp2p-workshop
cd py-libp2p-workshop
```

### Step 2: Set Up Python Virtual Environment (Recommended)

Create and activate a virtual environment to keep your workshop dependencies isolated:

```bash
# Create virtual environment
python -m venv workshop-env

# Activate it (Linux/Mac)
source workshop-env/bin/activate

# Activate it (Windows)
workshop-env\Scripts\activate
```

### Step 3: Install Core Dependencies

Install the required Python packages:

```bash
pip install trio aiohttp multiaddr protobuf cryptography pytest
```

### Step 4: Install py-libp2p

**Note**: py-libp2p is currently experimental. For this workshop, we'll use a simplified implementation that demonstrates core concepts.

### Step 5: Verify Your Setup

Run the dependency checker:

```bash
python deps.py
```

You should see all green checkmarks (✓) for required dependencies.

## Workshop Structure

Each lesson in this workshop follows this structure:

```
01-identity-and-host/
├── app/                    # Your application code goes here
│   ├── main.py            # Main application file
│   └── Dockerfile         # For containerized testing
├── lesson.md              # Lesson instructions and explanations
├── lesson.yaml            # Lesson metadata
├── check.py               # Automated checker for your solution
├── docker-compose.yaml    # Docker configuration
└── stdout.log             # Output log (created when you run your code)
```

## Getting Help

During the workshop:

1. **Read the lesson.md file carefully** - it contains detailed instructions and explanations
2. **Use the hint blocks** - they provide additional context for tricky parts
3. **Check your solution** - run `python check.py` to validate your implementation
4. **Ask for help** - don't hesitate to ask the instructor or fellow participants

## Workshop Objectives

By the end of this workshop, you will:

- Understand peer-to-peer networking fundamentals
- Know how to create libp2p nodes with cryptographic identities
- Implement transport layers and connection management
- Build custom protocols for peer communication
- Create a distributed chat application
- Connect to the Universal Connectivity network

## Next Steps

Once your environment is set up:

1. Navigate to the first lesson: `01-identity-and-host/`
2. Read the `lesson.md` file
3. Start coding in the `app/` directory
4. Test your solution with `python check.py`

Let's begin building the future of peer-to-peer applications! 🚀

## Troubleshooting

### Common Issues

**Python version too old:**
```bash
python --version  # Should be 3.8+
```
If you have multiple Python versions, try `python3` instead of `python`.

**Virtual environment issues:**
```bash
# Deactivate current environment
deactivate

# Remove and recreate
rm -rf workshop-env
python -m venv workshop-env
source workshop-env/bin/activate  # Linux/Mac
```

**Package installation failures:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Then install packages
pip install asyncio aiohttp multiaddr protobuf cryptography
```

**Import errors during lessons:**
Make sure your virtual environment is activated and all packages are installed in the correct environment.

Need more help? Ask your instructor! 👨‍🏫