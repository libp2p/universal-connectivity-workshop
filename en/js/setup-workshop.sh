#!/bin/bash
# Universal Connectivity JS Workshop Setup Script
# Run this once before starting the lessons

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Setting up Universal Connectivity JS Workshop..."
echo " Workshop root: $WORKSHOP_ROOT"

# 1. Create Docker network
echo ""
echo " Creating Docker network..."
docker network create --subnet=172.16.16.0/24 --gateway=172.16.16.1 workshop-net 2>/dev/null || {
    if docker network inspect workshop-net >/dev/null 2>&1; then
        echo "✓ Network workshop-net already exists"
    else
        echo " Network creation failed (may already exist with different subnet)"
        echo "   Trying to remove and recreate..."
        docker network rm workshop-net 2>/dev/null || true
        sleep 2
        docker network create --subnet=172.16.16.0/24 --gateway=172.16.16.1 workshop-net || {
            echo "❌ Failed to create network. Please check for conflicting Docker networks."
            exit 1
        }
    fi
}
echo "✓ Docker network ready"

# 2. Build unified checker image
echo ""
echo "🔨 Building unified checker image..."
CHECKER_DIR="$WORKSHOP_ROOT/en/checker"
if [ -d "$CHECKER_DIR" ]; then
    cd "$CHECKER_DIR"
    docker build -t ghcr.io/libp2p/universal-connectivity-workshop/ucw-checker-en:latest . || {
        echo "❌ Failed to build checker image"
        exit 1
    }
    echo "✓ Checker image built"
else
    echo "⚠️  Checker directory not found at $CHECKER_DIR"
    echo "   You may need to pull from GHCR or build manually"
fi

# 3. Set up checker keys directory
echo ""
echo "🔑 Setting up checker keys..."
KEYS_DIR="$WORKSHOP_ROOT/en/checker/keys"
mkdir -p "$KEYS_DIR"

# Generate keys if they don't exist (or copy from Rust lessons if available)
if [ ! -f "$KEYS_DIR/checker.key" ]; then
    echo "   Generating checker.key (single-checker lessons)..."
    # Try to copy from Rust lessons first
    RUST_KEY="$WORKSHOP_ROOT/en/rs/02-tcp-transport/12D3KooWDj4uNjMpUtESkyJa2ZB6DtXg5PKC4pTUptJixE7zo9gB.key"
    if [ -f "$RUST_KEY" ]; then
        cp "$RUST_KEY" "$KEYS_DIR/checker.key"
        echo "   ✓ Copied from Rust lessons"
    else
        echo "   ⚠️  Key file not found. Please ensure checker.key exists at:"
        echo "      $KEYS_DIR/checker.key"
        echo "   Or set CHECKER_KEY_PATH to point to your key file"
    fi
fi

if [ ! -f "$KEYS_DIR/checker1.key" ] || [ ! -f "$KEYS_DIR/checker2.key" ]; then
    echo "   Setting up dual-checker keys (lesson 07)..."
    RUST_KEY1="$WORKSHOP_ROOT/en/rs/07-kademlia-checkpoint/12D3KooWDj4uNjMpUtESkyJa2ZB6DtXg5PKC4pTUptJixE7zo9gB.key"
    RUST_KEY2="$WORKSHOP_ROOT/en/rs/07-kademlia-checkpoint/12D3KooWFg4cGhT7UAHJ6D2CzNCkr7MX6eN9vjhK1xSXweHkvd1X.key"
    if [ -f "$RUST_KEY1" ] && [ -f "$RUST_KEY2" ]; then
        cp "$RUST_KEY1" "$KEYS_DIR/checker1.key"
        cp "$RUST_KEY2" "$KEYS_DIR/checker2.key"
        echo "   ✓ Copied from Rust lessons"
    else
        echo "   ⚠️  Key files not found. Please ensure checker1.key and checker2.key exist"
    fi
fi

echo "✓ Keys directory ready at: $KEYS_DIR"

# 4. Export environment variables
echo ""
echo "📝 Setting environment variables..."
export WORKSHOP_ROOT
export CHECKER_KEY_PATH="${CHECKER_KEY_PATH:-$KEYS_DIR/checker.key}"
export CHECKER1_KEY_PATH="${CHECKER1_KEY_PATH:-$KEYS_DIR/checker1.key}"
export CHECKER2_KEY_PATH="${CHECKER2_KEY_PATH:-$KEYS_DIR/checker2.key}"

echo "   WORKSHOP_ROOT=$WORKSHOP_ROOT"
echo "   CHECKER_KEY_PATH=$CHECKER_KEY_PATH"
echo "   CHECKER1_KEY_PATH=$CHECKER1_KEY_PATH"
echo "   CHECKER2_KEY_PATH=$CHECKER2_KEY_PATH"

# Create .env file for docker-compose
cat > "$SCRIPT_DIR/.env" <<EOF
WORKSHOP_ROOT=$WORKSHOP_ROOT
CHECKER_KEY_PATH=$CHECKER_KEY_PATH
CHECKER1_KEY_PATH=$CHECKER1_KEY_PATH
CHECKER2_KEY_PATH=$CHECKER2_KEY_PATH
EOF
echo "✓ Environment variables saved to $SCRIPT_DIR/.env"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Source this script or export the env vars:"
echo "     source setup-workshop.sh"
echo "  2. Navigate to a lesson directory:"
echo "     cd 01-identity-and-swarm"
echo "  3. Run the lesson:"
echo "     docker compose up -d --build"
echo "     python3 check.py"
echo "     docker compose down -v"
echo ""
echo "Or use the run-all-lessons.sh script to run all lessons sequentially"