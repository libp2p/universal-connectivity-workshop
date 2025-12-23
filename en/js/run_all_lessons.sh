#!/bin/bash
# Run all JS workshop lessons sequentially
# First run setup-workshop.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source environment if .env exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Ensure environment is set
export WORKSHOP_ROOT="${WORKSHOP_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
export PROJECT_ROOT="$WORKSHOP_ROOT"

export CHECKER_KEY_PATH="${CHECKER_KEY_PATH:-$WORKSHOP_ROOT/en/checker/keys/checker.key}"
export CHECKER1_KEY_PATH="${CHECKER1_KEY_PATH:-$WORKSHOP_ROOT/en/checker/keys/checker1.key}"
export CHECKER2_KEY_PATH="${CHECKER2_KEY_PATH:-$WORKSHOP_ROOT/en/checker/keys/checker2.key}"

echo "🎓 Running Universal Connectivity JS Workshop Lessons"
echo "📍 Workshop root: $WORKSHOP_ROOT"
echo ""

LESSONS=(
    "01-identity-and-swarm"
    "02-tcp-transport"
    "03-ping-protocol"
    "04-circuit-relay-v2"
    "05-identify-protocol"
    "06-gossipsub-module"
    "07-kademlia-checkpoint"
    "08-final-checkpoint"
)

run_lesson() {
    local lesson=$1
    local lesson_dir="$SCRIPT_DIR/$lesson"

    if [ ! -d "$lesson_dir" ]; then
        echo "❌ Lesson directory not found: $lesson_dir"
        return 1
    fi

    # Ensure CHECKER_KEY_PATH is absolute before cd (preserve from top-level)
    local saved_checker_key_path="$CHECKER_KEY_PATH"
    local saved_checker1_key_path="$CHECKER1_KEY_PATH"
    local saved_checker2_key_path="$CHECKER2_KEY_PATH"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📚 Lesson: $lesson"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cd "$lesson_dir"

    # Restore and ensure absolute paths after cd (always use WORKSHOP_ROOT)
    export CHECKER_KEY_PATH="$WORKSHOP_ROOT/en/checker/keys/checker.key"
    export CHECKER1_KEY_PATH="$WORKSHOP_ROOT/en/checker/keys/checker1.key"
    export CHECKER2_KEY_PATH="$WORKSHOP_ROOT/en/checker/keys/checker2.key"

    # Clean up any previous runs
    docker compose down -v 2>/dev/null || true
    
    # Ensure these are files, not directories
    touch stdout.log checker.log

    # Pre-create lesson-specific log files
    if [ "$lesson" = "04-circuit-relay-v2" ]; then
        touch relay.log listener.log dialer.log
    fi

    if [ "$lesson" = "05-identify-protocol" ]; then
        touch node1.log node2.log node1-address.txt
    fi

    if [ "$lesson" = "07-kademlia-checkpoint" ]; then
        touch checker2.log
    fi

    # Lesson 08 checker.log is already created above, but ensure it's a file
    if [ "$lesson" = "08-final-checkpoint" ]; then
        # Ensure checker.log exists as a file (remove if it's a directory)
        [ -d checker.log ] && rm -rf checker.log
        touch checker.log
        # Ensure it has write permissions
        chmod 666 checker.log 2>/dev/null || true
    fi

    # Set lesson-specific environment
    export LESSON_PATH="en/js/$lesson"

    # Ensure CHECKER_KEY_PATH is set correctly (use absolute path from WORKSHOP_ROOT)
    if [ -z "$CHECKER_KEY_PATH" ] || [ ! -f "$CHECKER_KEY_PATH" ]; then
        export CHECKER_KEY_PATH="$WORKSHOP_ROOT/en/checker/keys/checker.key"
    fi

    # Validate key file exists for lessons that use checkers
    if [ "$lesson" = "02-tcp-transport" ] || [ "$lesson" = "03-ping-protocol" ] || [ "$lesson" = "06-gossipsub-module" ] || [ "$lesson" = "08-final-checkpoint" ]; then
        if [ ! -f "$CHECKER_KEY_PATH" ]; then
            echo "❌ Checker key file not found: $CHECKER_KEY_PATH"
            echo "   Please run setup-workshop.sh first or set CHECKER_KEY_PATH"
            return 1
        fi
    fi

    # Build and start
    echo "🔨 Building and starting containers..."
    docker compose up -d --build || {
        echo "❌ Failed to start lesson $lesson"
        return 1
    }

    # Wait for containers to be ready
    echo "⏳ Waiting for containers to be ready..."
    sleep 3

    # Run check script
    echo "✔️  Running checks..."
    if [ "$lesson" = "05-identify-protocol" ]; then
        # Special handling for lesson 05 - wait longer for both nodes to complete identify exchange
        echo "⏳ Waiting for identify protocol exchange to complete..."
        sleep 15

        # Ensure log files exist (prevent directory mount issues)
        touch node1.log node2.log

        # Wait a bit more to ensure all nodes have written their logs
        sleep 3

        # Special handling for lesson 05
        python3 check.py || {
            echo "❌ Checks failed for lesson $lesson"
            echo "📋 Checking logs..."
            echo "--- Node1 log ---"
            tail -30 node1.log || echo "node1.log empty or missing"
            echo "--- Node2 log ---"
            tail -30 node2.log || echo "node2.log empty or missing"
            docker compose logs
            docker compose down -v
            return 1
        }
    elif [ "$lesson" = "04-circuit-relay-v2" ]; then
        # Special handling for lesson 04 - wait longer for all nodes to complete
        echo "⏳ Waiting for circuit relay nodes to complete..."
        sleep 10

        # Ensure log files exist (prevent directory mount issues)
        touch relay.log listener.log dialer.log

        # Wait a bit more to ensure all nodes have written their logs
        sleep 3

        # Special handling for lesson 04
        python3 check.py \
            --relay-log relay.log \
            --listener-log listener.log \
            --dialer-log dialer.log || {
            echo "❌ Checks failed for lesson $lesson"
            echo "📋 Checking logs..."
            echo "--- Relay log ---"
            tail -20 relay.log || echo "relay.log empty or missing"
            echo "--- Listener log ---"
            tail -20 listener.log || echo "listener.log empty or missing"
            echo "--- Dialer log ---"
            tail -20 dialer.log || echo "dialer.log empty or missing"
            docker compose down -v
            return 1
        }
    elif [ "$lesson" = "06-gossipsub-module" ]; then
        # Special handling for lesson 06 - wait longer for multi-node GossipSub demonstration to complete
        # The demo takes ~15 seconds: mesh formation (3s) + message exchange (4s) + validation wait (5s) + overhead (3s)
        echo "⏳ Waiting for GossipSub multi-node demonstration to complete..."
        sleep 18

        # Ensure log file exists and is readable (prevent directory mount issues)
        touch stdout.log

        # Sync filesystem to ensure log is flushed to disk
        sync

        # Wait a bit more to ensure all logs are fully written
        sleep 2

        # Verify log file has content before checking
        if [ ! -s stdout.log ]; then
            echo "⚠️  Warning: stdout.log is empty, waiting a bit more..."
            sleep 5
        fi

        # Special handling for lesson 06
        python3 check.py || {
            echo "❌ Checks failed for lesson $lesson"
            echo "📋 Checking logs..."
            echo "--- stdout.log (last 50 lines) ---"
            tail -50 stdout.log || echo "stdout.log empty or missing"
            echo "--- stdout.log size ---"
            ls -lh stdout.log || echo "stdout.log not found"
            docker compose logs --tail=50 lesson
            docker compose down -v
            return 1
        }
    elif [ "$lesson" = "07-kademlia-checkpoint" ]; then
        # Special handling for lesson 07 - wait longer for multi-node Kademlia DHT demonstration to complete
        # The demo takes ~25 seconds: network formation (3s) + DHT population (3s) + peer routing (1s) + 
        # content announce/search (7s) + value storage/retrieve (5s) + validation wait (5s) + overhead (1s)
        echo "⏳ Waiting for Kademlia DHT multi-node demonstration to complete..."
        sleep 25

        # Ensure log file exists and is readable (prevent directory mount issues)
        touch stdout.log

        # Sync filesystem to ensure log is flushed to disk
        sync

        # Wait a bit more to ensure all logs are fully written
        sleep 3

        # Verify log file has content before checking
        if [ ! -s stdout.log ]; then
            echo "⚠️  Warning: stdout.log is empty, waiting a bit more..."
            sleep 5
        fi

        # Special handling for lesson 07
        python3 check.py || {
            echo "❌ Checks failed for lesson $lesson"
            echo "📋 Checking logs..."
            echo "--- stdout.log (last 60 lines) ---"
            tail -60 stdout.log || echo "stdout.log empty or missing"
            echo "--- stdout.log size ---"
            ls -lh stdout.log || echo "stdout.log not found"
            echo "--- checker.log ---"
            tail -20 checker.log || echo "checker.log empty or missing"
            echo "--- checker2.log ---"
            tail -20 checker2.log || echo "checker2.log empty or missing"
            docker compose logs --tail=60 lesson
            docker compose down -v
            return 1
        }
    elif [ "$lesson" = "08-final-checkpoint" ]; then
        # Special handling for lesson 08 - wait longer for final checkpoint to complete
        # The demo needs time for: connection (2s) + identify (2s) + gossipsub mesh formation (5s) + 
        # message exchange (2s) + validation (5s) + overhead (3s)
        echo "⏳ Waiting for Final Checkpoint demonstration to complete..."
        sleep 20

        # Ensure log files exist and are readable (prevent directory mount issues)
        touch stdout.log
        rm -f checker.log

        # Capture checker logs from Docker container (not via volume mount)
        echo "📋 Capturing checker logs..."
        docker compose logs checker > checker.log 2>&1 || true

        # Sync filesystem to ensure logs are flushed to disk
        sync

        # Wait a bit more to ensure all logs are fully written
        sleep 3

        # Verify log files have content before checking
        if [ ! -s stdout.log ]; then
            echo "⚠️  Warning: stdout.log is empty, waiting a bit more..."
            sleep 5
        fi

        if [ ! -s checker.log ]; then
            echo "⚠️  Warning: checker.log is empty, capturing again..."
            sleep 3
            docker compose logs checker > checker.log 2>&1 || true
        fi

        # Special handling for lesson 08
        python3 check.py || {
            echo "❌ Checks failed for lesson $lesson"
            echo "📋 Checking logs..."
            echo "--- stdout.log (last 60 lines) ---"
            tail -60 stdout.log || echo "stdout.log empty or missing"
            echo "--- checker.log (last 30 lines) ---"
            tail -30 checker.log || echo "checker.log empty or missing"
            echo "--- stdout.log size ---"
            ls -lh stdout.log || echo "stdout.log not found"
            echo "--- checker.log size ---"
            ls -lh checker.log || echo "checker.log not found"
            docker compose logs --tail=60 lesson
            docker compose logs --tail=30 checker
            docker compose down -v
            return 1
        }
    else
        python3 check.py || {
            echo "❌ Checks failed for lesson $lesson"
            docker compose logs
            docker compose down -v
            return 1
        }
    fi

    # Clean up
    echo "🧹 Cleaning up..."
    docker compose down -v

    echo "✅ Lesson $lesson completed successfully!"
}

# Run all lessons
for lesson in "${LESSONS[@]}"; do
    if ! run_lesson "$lesson"; then
        echo ""
        echo "❌ Failed at lesson: $lesson"
        echo "   Please check the output above and fix any issues"
        exit 1
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All lessons completed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"