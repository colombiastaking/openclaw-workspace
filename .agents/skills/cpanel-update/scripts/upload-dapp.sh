#!/bin/bash
# Upload Colombia Staking DApp via FTP using curl
# Automatically protects mvx-api.php from being overwritten
# Uses credentials from ~/.openclaw/secrets/.ftp_credentials
#
# IMPORTANT: Uses curl instead of lftp because lftp has SSL timeout issues
# with this server. curl --ftp-ssl works properly.
#
# CRITICAL: LiteSpeed aggressively caches HTML responses for ALL file types.
# After upload, we DELETE then RE-UPLOAD each file to force cache clear.

set -e

source ~/.openclaw/secrets/.ftp_credentials

DAPP_DIR="$HOME/.openclaw/workspace/DAPP-V3/dist"
REMOTE_DIR="/home/colombia6/staking.colombia-staking.com"
PROTECTED_FILE="mvx-api.php"

echo "=== Uploading Colombia Staking DApp via FTP ==="
echo "Server: $HOST"
echo "Remote: $REMOTE_DIR"
echo ""
echo "⚠️  NOTE: Delete + Re-upload pattern used to clear LiteSpeed cache"
echo ""

# Check if DApp build exists
if [ ! -d "$DAPP_DIR" ]; then
    echo "ERROR: DApp build not found at $DAPP_DIR"
    echo "Please run: cd ~/.openclaw/workspace/DAPP-V3 && npm run build"
    exit 1
fi

# Function to delete and re-upload a file via curl
# This clears LiteSpeed cache which caches HTML for ALL file types
delete_and_upload() {
    local local_file="$1"
    local remote_path="$2"
    local filename=$(basename "$local_file")
    
    # Skip protected file
    if [ "$filename" = "$PROTECTED_FILE" ]; then
        echo "  ⏭️  Skipping (protected): $filename"
        return 0
    fi
    
    echo "  🔄 $filename"
    
    # Step 1: Delete the remote file (forces LiteSpeed to clear cache)
    curl -s -k --ftp-ssl -Q "DELE $remote_path" -u "$USER:$PASS" "ftp://$HOST$remote_path" 2>/dev/null || true
    
    # Small delay to ensure delete completes
    sleep 1
    
    # Step 2: Re-upload the file
    curl -s -k --ftp-ssl -T "$local_file" -u "$USER:$PASS" "ftp://$HOST$remote_path"
}

# Function to upload directory recursively
upload_directory() {
    local local_dir="$1"
    local remote_base="$2"
    
    # Create remote directory first
    curl -s -k --ftp-ssl -u "$USER:$PASS" -Q "MKD $remote_base" "ftp://$HOST/" 2>/dev/null || true
    
    # Find and upload all files
    find "$local_dir" -type f | sort | while read -r file; do
        # Get relative path
        relative_path="${file#$local_dir/}"
        remote_path="$remote_base/$relative_path"
        remote_dir=$(dirname "$remote_path")
        
        # Create remote subdirectory if needed
        curl -s -k --ftp-ssl -u "$USER:$PASS" -Q "MKD $remote_dir" "ftp://$HOST/" 2>/dev/null || true
        
        # Delete and re-upload (clears LiteSpeed cache)
        delete_and_upload "$file" "$remote_path"
    done
}

echo "Uploading DApp build (delete + re-upload to clear LiteSpeed cache)..."
echo ""

# Upload main dist directory
upload_directory "$DAPP_DIR" "$REMOTE_DIR"

# Upload root index.html if exists
if [ -f "$HOME/.openclaw/workspace/DAPP-V3/index.html" ]; then
    delete_and_upload "$HOME/.openclaw/workspace/DAPP-V3/index.html" "$REMOTE_DIR/index.html"
fi

# Upload root assets directory if exists in DAPP-V3 (not in dist)
if [ -d "$HOME/.openclaw/workspace/DAPP-V3/public" ]; then
    upload_directory "$HOME/.openclaw/workspace/DAPP-V3/public" "$REMOTE_DIR/public"
fi

echo ""
echo "=== DApp upload complete! ==="
echo "⚠️  Note: $PROTECTED_FILE was NOT overwritten (protected file)"
echo ""
echo "Test at: https://staking.colombia-staking.com"
