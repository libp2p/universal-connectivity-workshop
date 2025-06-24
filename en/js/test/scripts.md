Here are **automated/scripted testing instructions and scripts** for both Lesson 1 and Lesson 2. These scripts will ensure your lessons are robustly validated in a CI pipeline or locally, just like in the Rust workshop.

---

## **Automated Testing Script (Bash)**

This script will:
- Build and run the lesson using Docker Compose.
- Capture the output.
- Pipe the output to `check.py`.
- Print the result (✅ or ❌) and exit with the correct status.

### **test_lesson.sh**
```bash
#!/bin/bash
# Usage: ./test_lesson.sh <lesson_dir>
set -e

LESSON_DIR="$1"
if [ -z "$LESSON_DIR" ]; then
  echo "Usage: $0 <lesson_dir>"
  exit 1
fi

cd "$LESSON_DIR"

echo "Building Docker image for $LESSON_DIR..."
docker-compose build --quiet

echo "Running Docker Compose for $LESSON_DIR..."
# Run the container, capture output, and clean up after
docker-compose up --abort-on-container-exit | tee output.log

echo "Validating output with check.py..."
python3 check.py < output.log

RESULT=$?
if [ $RESULT -eq 0 ]; then
  echo "✅ Lesson test passed!"
else
  echo "❌ Lesson test failed!"
fi

# Clean up
docker-compose down -v

exit $RESULT
```

---

## **How to Use**

1. **Save the script above as `test_lesson.sh` in your workspace root.**
2. **Make it executable:**
   ```sh
   chmod +x test_lesson.sh
   ```
3. **Run for Lesson 1:**
   ```sh
   ./test_lesson.sh universal-connectivity-workshop/en/js/01-identity-and-swarm
   ```
4. **Run for Lesson 2:**
   ```sh
   ./test_lesson.sh universal-connectivity-workshop/en/js/02-tcp-transport
   ```

---

## **What This Does**

- Builds the Docker image for the lesson.
- Runs the app, capturing all output.
- Pipes the output to `check.py` for validation.
- Prints a checkmark (✅) for success or a cross (❌) for failure.
- Cleans up Docker containers and volumes after the test.

---