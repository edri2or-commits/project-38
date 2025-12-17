#!/bin/bash
# Project 38 V2 - VM Startup Script
# Installs Docker + Docker Compose on first boot
# Usage: Run as root during VM creation (--metadata-from-file startup-script=startup.sh)

set -euo pipefail

echo "🚀 Project 38 V2 - VM Startup"
echo "   Starting Docker installation..."

# Update package lists only (no full upgrade to avoid timeouts)
echo "📦 Updating package lists..."
apt-get update

# Install dependencies
echo "📦 Installing prerequisites..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
echo "🔑 Adding Docker GPG key..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo "📚 Configuring Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
echo "🐳 Installing Docker Engine..."
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable Docker service
echo "⚙️  Enabling Docker service..."
systemctl enable docker
systemctl start docker

# Add primary non-root user to docker group
# Find first user with UID >= 1000 (non-system user)
PRIMARY_USER=$(getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $1; exit}')

if [ -n "$PRIMARY_USER" ]; then
    echo "👤 Adding user '$PRIMARY_USER' to docker group..."
    usermod -aG docker "$PRIMARY_USER"
else
    echo "⚠️  Warning: No non-root user found (UID >= 1000)"
fi

# Create project directory
echo "📁 Creating project directory..."
mkdir -p /opt/project38

if [ -n "$PRIMARY_USER" ]; then
    chown "$PRIMARY_USER:$PRIMARY_USER" /opt/project38
else
    # Fallback: world-writable (not ideal, but functional)
    chmod 777 /opt/project38
fi

# Verify installation
echo "✅ Verifying installation..."
docker --version > /opt/project38/docker_version.txt
docker compose version > /opt/project38/compose_version.txt

# Write completion marker with metadata
cat > /opt/project38/startup_complete.txt <<EOF
Project 38 V2 - Startup Complete
Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Docker Version: $(docker --version)
Compose Version: $(docker compose version)
Primary User: ${PRIMARY_USER:-none}
EOF

echo ""
echo "✅ Startup script completed successfully"
echo "   Docker: $(docker --version | cut -d' ' -f3)"
echo "   Compose: $(docker compose version | cut -d' ' -f4)"
if [ -n "$PRIMARY_USER" ]; then
    echo "   User '$PRIMARY_USER' can use Docker without sudo"
fi
