FROM golang:1.23-alpine AS builder

# Install git for go modules
RUN apk add --no-cache git

WORKDIR /app

# Copy source code
COPY . .

# Initialize go modules and download dependencies
RUN go mod tidy && go mod download

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Final stage
FROM alpine:latest

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy binary from builder
COPY --from=builder /app/main .

# Run the application
CMD ["./main"]
