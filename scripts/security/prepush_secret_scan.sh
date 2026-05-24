#!/usr/bin/env bash
set -euo pipefail

# Blocks push if likely secrets are found in files being pushed,
# except approved secret-bearing files (dotenv/infra secret templates).

if ! command -v git >/dev/null 2>&1; then
  echo "[secret-scan] git is required"
  exit 1
fi

NULL_SHA="0000000000000000000000000000000000000000"

# Paths where secret-like tokens are expected placeholders or local config.
is_allowed_secret_file() {
  local path="$1"
  case "$path" in
    .env|.env.*|*/.env|*/.env.*|*.pem|*.key|*.p12|*.jks)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# High-signal secret patterns.
SECRET_REGEX='(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|ghp_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{40,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----|(api[_-]?key|secret|token|password|passwd|authorization)[[:space:]]*[:=][[:space:]]*['"'"']?[A-Za-z0-9_\-\/+=]{10,})'

found=0

scan_range() {
  local range="$1"

  # Added/modified/renamed/copied files only.
  while IFS= read -r file; do
    [ -z "$file" ] && continue

    if is_allowed_secret_file "$file"; then
      continue
    fi

    # Scan added lines only to reduce noise.
    if git diff --unified=0 "$range" -- "$file" | sed -n 's/^+//p' | grep -E -n "$SECRET_REGEX" >/dev/null 2>&1; then
      echo "[secret-scan] Possible secret found in: $file"
      git diff --unified=0 "$range" -- "$file" | sed -n 's/^+//p' | grep -E -n "$SECRET_REGEX" | sed 's/^/  line /'
      found=1
    fi
  done < <(git diff --name-only --diff-filter=ACMR "$range")
}

# Read refs from pre-push stdin.
# shellcheck disable=SC2162
while read local_ref local_sha remote_ref remote_sha; do
  [ -z "${local_sha:-}" ] && continue

  if [ "$local_sha" = "$NULL_SHA" ]; then
    continue
  fi

  if [ "${remote_sha:-$NULL_SHA}" = "$NULL_SHA" ]; then
    range="$local_sha"
  else
    range="$remote_sha..$local_sha"
  fi

  scan_range "$range"
done

if [ "$found" -ne 0 ]; then
  cat <<'MSG'
[secret-scan] Push blocked.
Detected potential secrets in files outside protected dotenv/secret files.
Move sensitive values to .env / GitHub Secrets and rotate leaked credentials.
MSG
  exit 1
fi

exit 0
