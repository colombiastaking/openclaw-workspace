#!/bin/bash
# deploy-website.sh - Deploy Colombia Staking websites via FTP
# Uses colombia6 account which has access to all site subdirectories
# Usage: ./deploy-website.sh [en|es|fr|all]

ROOT_HOST="colombia-staking.com"
ROOT_USER="colombia6"

# Load FTP password from environment or ~/.openclaw/.env
if [ -z "$FTP_PASS" ]; then
  if [ -f "$HOME/.openclaw/.env" ]; then
    FTP_PASS=$(grep "^FTP_PASS=" "$HOME/.openclaw/.env" | cut -d'=' -f2- | tr -d '"')
  fi
fi

if [ -z "$FTP_PASS" ]; then
  echo "❌ FTP_PASS not set and not found in ~/.openclaw/.env"
  exit 1
fi

SITE_DIR="$HOME/.openclaw/workspace/Website"

# Map: site key -> FTP path (from colombia6 root)
declare -A SITE_PATHS=(
  ["en"]="/colombia-staking.com"
  ["es"]="/esp.colombia-staking.com"
  ["fr"]="/fr.colombia-staking.com"
)

# Local source dirs
declare -A LOCAL_DIRS=(
  ["en"]="$SITE_DIR/eng"
  ["es"]="$SITE_DIR/esp"
  ["fr"]="$SITE_DIR/fr"
)

# Upload function with delete-first for cached files
ftp_upload() {
  local local_file="$1"
  local remote_dir="$2"
  local filename=$(basename "$local_file")
  local max_retries=3
  local retry=0

  while [ $retry -lt $max_retries ]; do
    # Delete existing file first (helps LiteSpeed refresh)
    curl -s -k --ftp-ssl \
      -u "$ROOT_USER:$FTP_PASS" \
      -Q "DELE $remote_dir/$filename" \
      "ftp://$ROOT_HOST/" > /dev/null 2>&1

    # Upload new file
    result=$(curl -s -k --ftp-ssl \
      -u "$ROOT_USER:$FTP_PASS" \
      -T "$local_file" \
      "ftp://$ROOT_HOST$remote_dir/$filename" \
      --connect-timeout 20 -m 60 2>&1)
    ret=$?

    if [ $ret -eq 0 ]; then
      return 0
    elif [ $ret -eq 9 ] || [ $ret -eq 28 ]; then
      # Exit 9 = FTP connection reset, Exit 28 = timeout - retry
      retry=$((retry + 1))
      echo "  Retry $retry/$max_retries for $filename..."
      sleep 2
    else
      echo "  Error uploading $filename: $result"
      return $ret
    fi
  done

  echo "  Failed after $max_retries attempts: $filename"
  return 1
}

# Upload function
upload_site() {
  local local_path="$1"
  local remote_dir="$2"
  local site_name="$3"

  echo "=== Deploying $site_name ==="

  # Upload HTML files
  for file in "$local_path"/*.html; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")
    echo "  Uploading $filename..."
    ftp_upload "$file" "$remote_dir"
    sleep 1
  done

  # Upload js/ directory
  if [ -d "$local_path/js" ]; then
    echo "  Uploading js/..."
    for file in "$local_path/js"/*.js; do
      [ -f "$file" ] || continue
      ftp_upload "$file" "$remote_dir/js"
      sleep 1
    done
  fi

  # Upload css/ directory
  if [ -d "$local_path/css" ]; then
    echo "  Uploading css/..."
    for file in "$local_path/css"/*.css; do
      [ -f "$file" ] || continue
      ftp_upload "$file" "$remote_dir/css"
      sleep 1
    done
  fi

  echo "=== $site_name deployed ==="
}

# Main
case "$1" in
  en)    upload_site "${LOCAL_DIRS[en]}" "${SITE_PATHS[en]}" "English site" ;;
  es)    upload_site "${LOCAL_DIRS[es]}" "${SITE_PATHS[es]}" "Spanish site" ;;
  fr)    upload_site "${LOCAL_DIRS[fr]}" "${SITE_PATHS[fr]}" "French site" ;;
  all)
    upload_site "${LOCAL_DIRS[en]}" "${SITE_PATHS[en]}" "English site"
    upload_site "${LOCAL_DIRS[es]}" "${SITE_PATHS[es]}" "Spanish site"
    upload_site "${LOCAL_DIRS[fr]}" "${SITE_PATHS[fr]}" "French site"
    ;;
  *)  echo "Usage: $0 [en|es|fr|all]"
      echo "  en  - Colombia-staking.com"
      echo "  es  - esp.colombia-staking.com"
      echo "  fr  - fr.colombia-staking.com"
      echo "  all - All three sites"
      exit 1 ;;
esac

echo ""
echo "=== Deployment complete ==="
echo "IMPORTANT: If LiteSpeed cache is enabled, changes may not appear immediately."
echo "To purge cache: Log into cPanel → LiteSpeed Cache → Purge All"
echo "Or wait for TTL expiration (~hours to ~1 day)"
echo ""
echo "To deploy DApp: Use the cpanel-update skill instead"
