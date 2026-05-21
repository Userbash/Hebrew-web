#!/bin/bash

# --- Logging Utilities ---
log() {
  local level=$1
  shift
  local message="$@"
  echo "[$(date +"%Y-%m-%dT%H:%M:%SZ")] [$level] $message" | tee -a pipeline.log
}

run_command() {
  local cmd_desc=$1
  local cmd=$2
  log "INFO" "Running: $cmd_desc (Command: $cmd)"
  
  output=$(eval "$cmd" 2>&1)
  exit_code=$?
  
  if [ $exit_code -ne 0 ]; then
    log "ERROR" "Command failed: $cmd_desc. Exit code: $exit_code. Output:"
    echo "$output" | tee -a pipeline.log
    echo "result=failure" >> $GITHUB_OUTPUT
    echo "output<<EOF" >> $GITHUB_OUTPUT
    echo "$output" >> $GITHUB_OUTPUT
    echo "EOF" >> $GITHUB_OUTPUT
    return 1
  else
    log "INFO" "Command successful: $cmd_desc. Output:"
    echo "$output" | tee -a pipeline.log
    echo "result=success" >> $GITHUB_OUTPUT
    echo "output<<EOF" >> $GITHUB_OUTPUT
    echo "$output" >> $GITHUB_OUTPUT
    echo "EOF" >> $GITHUB_OUTPUT
    return 0
  fi
}

# --- Error Analysis Functions ---
parse_logs() {
  local log_content="$1"
  local error_log_file="$2"
  
  echo "$log_content" | while IFS= read -r line; do
    # Try to parse as JSON if it looks like JSON
    if echo "$line" | jq -e . > /dev/null 2>&1; then
      local timestamp=$(echo "$line" | jq -r ".timestamp // empty")
      local level=$(echo "$line" | jq -r ".level // empty")
      local message=$(echo "$line" | jq -r ".msg // empty")
      
      # Check for error levels (Pino levels 50 is error)
      if [[ "$level" = "50" || "$level" = "ERROR" ]]; then
        echo "{\"timestamp\": \"$timestamp\", \"level\": \"$level\", \"message\": \"$message\"}" >> "$error_log_file"
      fi
    else
      # Fallback for non-JSON lines, simplistic error detection
      if echo "$line" | grep -iqE "error|fail|failed|exception|denied|refused|timeout|fatal|critical"; then
        echo "{\"timestamp\": \"$(date +"%Y-%m-%dT%H:%M:%SZ")\", \"level\": \"ERROR_DETECTED\", \"message\": \"$line\"}" >> "$error_log_file"
      fi
    fi
  done
}

# --- Project-specific Utilities ---
install_npm_deps() {
  local path=$1
  run_command "Install npm dependencies in $path" "npm install --prefix $path"
}

run_npm_test() {
  local path=$1
  run_command "Run npm tests in $path" "npm test --prefix $path"
}

build_docker_image() {
  local tag=$1
  local path=$2
  run_command "Build Podman image $tag from $path" "podman build -t $tag $path"
}

