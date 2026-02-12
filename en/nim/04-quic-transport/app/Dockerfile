# Build stage
FROM nim-libp2p-base AS builder

WORKDIR /app

# Create nimble project file
RUN echo 'requires "libp2p >= 1.0.0"' > lesson.nimble

# Copy source code from the lesson path
COPY en/nim/04-quic-transport/app/main.nim .

# Compile with optimizations
RUN nim c -d:release --threads:on --opt:speed -o:lesson main.nim

# Runtime stage - same base for simplicity with Nim
FROM nim-libp2p-base

WORKDIR /app

# Copy the compiled binary
COPY --from=builder /app/lesson /app/lesson

# Run the lesson
CMD ["./lesson"]
