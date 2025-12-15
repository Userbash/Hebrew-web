#!/bin/bash

# Script to determine OS, available package managers, and container tools

echo "==================================="
echo "  System and Environment Info      "
echo "===================================\n"

RECOMMENDATIONS_FILE="installation_recommendations.md"
CONTAINER_STATUS=""
DOCKER_INSTALLED="no"
DOCKER_COMPOSE_INSTALLED="no"
PODMAN_INSTALLED="no"
PODMAN_COMPOSE_INSTALLED="no"

# 1. Determine Operating System
echo "--- Operating System Information ---"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME="${NAME:-"N/A"}"
    OS_VERSION="${VERSION:-"N/A"}"
    OS_ID="${ID:-"N/A"}"
    OS_ID_LIKE="${ID_LIKE:-"N/A"}"
    OS_PRETTY_NAME="${PRETTY_NAME:-"N/A"}"

    echo "NAME: $OS_NAME"
    echo "VERSION: $OS_VERSION"
    echo "ID: $OS_ID"
    echo "ID_LIKE: $OS_ID_LIKE"
    echo "PRETTY_NAME: $OS_PRETTY_NAME"
else
    echo "Could not find /etc/os-release. OS information limited."
    OS_NAME="Unknown"
    OS_VERSION="Unknown"
    OS_ID="Unknown"
    OS_ID_LIKE="Unknown"
    OS_PRETTY_NAME="$(uname -a)"
fi
echo ""

# 2. Identify and Check Package Managers (existing logic)
echo "--- Package Manager Information ---"

declare -A pms=(
    ["apt"]="apt-get"
    ["yum"]="yum"
    ["dnf"]="dnf"
    ["zypper"]="zypper"
    ["pacman"]="pacman"
    ["apk"]="apk"
    ["brew"]="brew" # macOS
    ["choco"]="choco" # Windows (via Git Bash/WSL)
    ["snap"]="snap"
    ["flatpak"]="flatpak"
    ["npm"]="npm" # Node.js package manager
    ["pip"]="pip" # Python package manager
    ["go"]="go" # Go package manager
    ["cargo"]="cargo" # Rust package manager
)

FOUND_PMS=()
for pm_name in "${!pms[@]}"; do
    command_name="${pms[$pm_name]}"
    if command -v "$command_name" &> /dev/null; then
        version_output=""
        case "$pm_name" in
            "apt") version_output="$($command_name --version | head -n 1)" ;;
            "yum") version_output="$($command_name --version | head -n 1)" ;;
            "dnf") version_output="$($command_name --version | head -n 1)" ;;
            "zypper") version_output="$($command_name --version | head -n 1)" ;;
            "pacman") version_output="$($command_name --version | head -n 1)" ;;
            "apk") version_output="$($command_name --version | head -n 1)" ;;
            "brew") version_output="$($command_name --version | head -n 1)" ;;
            "choco") version_output="$($command_name --version | head -n 1)" ;;
            "snap") version_output="$($command_name version | grep "snap" | head -n 1)" ;;
            "flatpak") version_output="$($command_name --version | head -n 1)" ;;
            "npm") version_output="$($command_name --version | head -n 1)" ;;
            "pip") version_output="$($command_name --version | head -n 1)" ;;
            "go") version_output="$($command_name version | head -n 1)" ;;
            "cargo") version_output="$($command_name --version | head -n 1)" ;;
            *) version_output="$($command_name --version 2>&1 | head -n 1)" ;; # Default for others
        esac
        echo "✓ $pm_name ($command_name) installed. Version: $version_output"
        FOUND_PMS+=("$pm_name")
    else
        echo "✗ $pm_name ($command_name) not found."
    fi
done
echo ""

# 3. Determine Container Tool Status
echo "--- Containerization Tool Status ---"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_INSTALLED="yes"
    echo "✓ Docker daemon installed. Version: $(docker --version)"
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE_INSTALLED="yes"
        echo "✓ Docker Compose plugin installed. Version: $(docker compose version | head -n 1)"
    else
        echo "✗ Docker Compose plugin NOT found."
    fi
else
    echo "✗ Docker daemon NOT found."
fi

# Check Podman
if command -v podman &> /dev/null; then
    PODMAN_INSTALLED="yes"
    echo "✓ Podman installed. Version: $(podman --version)"
    if command -v podman-compose &> /dev/null; then
        PODMAN_COMPOSE_INSTALLED="yes"
        echo "✓ Podman-compose installed. Version: $(podman-compose --version | head -n 1)"
    else
        echo "✗ Podman-compose NOT found."
    fi
else
    echo "✗ Podman NOT found."
fi
echo ""

# 4. Generate Installation Recommendations
generate_recommendations() {
    echo "Generating installation recommendations to $RECOMMENDATIONS_FILE..."
    {
        echo "# Containerization Tool Installation Recommendations"
        echo ""
        echo "This document provides recommendations for installing containerization tools based on your system's current configuration."
        echo ""
        echo "## System Information"
        echo "  * **OS Name:** \`$OS_NAME\`"
        echo "  * **OS Version:** \`$OS_VERSION\`"
        echo "  * **OS ID:** \`$OS_ID\`"
        echo "  * **Pretty Name:** \`$OS_PRETTY_NAME\`"
        echo "  * **Detected Package Managers:** \`${FOUND_PMS[*]:-"None found"}\`"
        echo ""
        echo "---"
        echo ""
        echo "## Current Container Tool Status"
        echo ""
        echo "### Docker Status"
        if [ "$DOCKER_INSTALLED" == "yes" ]; then
            echo "*   Docker daemon: **Installed** (Version: \`$(docker --version)\`)"
        else
            echo "*   Docker daemon: **NOT Installed**"
        fi
        if [ "$DOCKER_COMPOSE_INSTALLED" == "yes" ]; then
            echo "*   Docker Compose plugin: **Installed** (Version: \`$(docker compose version | head -n 1)\`)"
        else
            echo "*   Docker Compose plugin: **NOT Installed**"
        fi
        echo ""
        echo "### Podman Status"
        if [ "$PODMAN_INSTALLED" == "yes" ]; then
            echo "*   Podman: **Installed** (Version: \`$(podman --version)\`)"
        else
            echo "*   Podman: **NOT Installed**"
        fi
        if [ "$PODMAN_COMPOSE_INSTALLED" == "yes" ]; then
            echo "*   Podman-compose: **Installed** (Version: \`$(podman-compose --version | head -n 1)\`)"
        else
            echo "*   Podman-compose: **NOT Installed**"
        fi
        echo ""
        echo "---"
        echo ""
        echo "## Recommendations"
        echo ""

        if [ "$DOCKER_INSTALLED" == "yes" ] && [ "$DOCKER_COMPOSE_INSTALLED" == "yes" ]; then
            echo "### Your system is ready for Docker-based deployments!"
            echo "You have Docker and Docker Compose plugin fully installed."
            echo "You can now run \`bash deploy.sh\`."
            echo ""
        elif [ "$PODMAN_INSTALLED" == "yes" ] && [ "$PODMAN_COMPOSE_INSTALLED" == "yes" ]; then
            echo "### Your system is ready for Podman-based deployments!"
            echo "You have Podman and Podman-compose fully installed."
            echo "You can now run \`bash deploy.sh\`."
            echo ""
        else
            echo "### To enable container-based deployments, please install either Docker or Podman."
            echo ""
            echo "#### Option 1: Install Docker Desktop (Recommended for ease of use)"
            echo "Docker Desktop provides a complete Docker environment, including the Docker daemon and Docker Compose plugin."
            echo "Follow the official installation guide for your operating system:"
            echo "-   **Docker Desktop for Linux:** [https://docs.docker.com/desktop/install/linux-install/](https://docs.docker.com/desktop/install/linux-install/)"
            echo "-   **Docker Desktop for Mac:** [https://docs.docker.com/desktop/install/mac-install/](https://docs.docker.com/desktop/install/mac-install/)"
            echo "-   **Docker Desktop for Windows:** [https://docs.docker.com/desktop/install/windows-install/](https://docs.docker.com/desktop/install/windows-install/)"
            echo ""
            echo "#### Option 2: Install Podman and Podman-Compose"
            echo "If you prefer a daemonless container engine, Podman is an excellent choice. You will also need Podman-compose to manage multi-container applications with Docker Compose files."
            echo ""
            echo "1.  **Install Podman:**"
            echo "    Follow the official Podman installation guide for your operating system:"
            echo "    [https://podman.io/docs/installation](https://podman.io/docs/installation)"
            echo ""
            echo "2.  **Install Podman-Compose:**"
            echo "    Podman-compose is typically installed via `pip` (Python package manager)."
            echo "    If `pip` is not installed, you may need to install Python and pip first."
            echo "    You can often install it with:"
            echo "    \`\`\`bash"
            echo "    pip install podman-compose"
            echo "    \`\`\`"
            echo "    Alternatively, follow the Podman-compose installation instructions:"
            echo "    [https://github.com/containers/podman-compose](https://github.com/containers/podman-compose)"
            echo ""
        fi
        echo "---"
        echo ""
        echo "After installing your preferred containerization tool, you can re-run this script (\`bash detect_system.sh\`) to verify the installation, or directly attempt to deploy your application using \`bash deploy.sh\`."
        echo ""
        echo "*Note: This environment (\`$OS_PRETTY_NAME\`) appears to be a Flatpak runtime, which might require specific considerations for system-level installations. Always refer to the official documentation for the most accurate and up-to-date installation instructions for your specific setup.*"

    } > "$RECOMMENDATIONS_FILE"
    echo "Recommendations saved to: $RECOMMENDATIONS_FILE"
}

# Call the function to generate recommendations
generate_recommendations

echo "\n===================================\n"
