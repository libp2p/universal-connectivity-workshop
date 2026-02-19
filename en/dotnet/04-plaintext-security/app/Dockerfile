# Multi-stage build for .NET 8
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /app

# Copy project file and restore dependencies
COPY en/dotnet/04-plaintext-security/app/*.csproj ./
RUN dotnet restore

# Copy source code and build
COPY en/dotnet/04-plaintext-security/app/ ./
RUN dotnet publish -c Release -o out

# Runtime stage
FROM mcr.microsoft.com/dotnet/runtime:9.0
WORKDIR /app

# Copy built application
COPY --from=build /app/out .

# Environment variables
ARG TIMEOUT_DURATION
ENV TIMEOUT_DURATION=${TIMEOUT_DURATION:-20s}
ARG REMOTE_PEERS
ENV REMOTE_PEERS=${REMOTE_PEERS:-}

# Run with timeout and redirect output
CMD ["/bin/sh", "-c", "timeout ${TIMEOUT_DURATION} dotnet App.dll > /app/stdout.log 2>&1 || true"]
