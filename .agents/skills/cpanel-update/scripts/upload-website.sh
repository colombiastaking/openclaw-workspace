#!/bin/bash
# Upload Colombia Staking Website (all 3 languages) via FTP using curl
# Uses credentials from ~/.openclaw/secrets/.ftp_credentials
#
# IMPORTANT: Uses curl instead of lftp because lftp has SSL timeout issues
# with this server. curl --ftp-ssl works properly.

set -e

source ~/.openclaw/secrets/.ftp_credentials

WEBSITE_DIR="$HOME/.openclaw/workspace/Website"

echo "=== Uploading Colombia Staking Websites (EN/ES/FR) ==="
echo "Server: $HOST"
echo ""

# Function to upload a directory
upload_dir() {
    local local_dir="$1"
    local remote_dir="$2"
    local lang="$3"
    
    echo "[$lang] Uploading: $local_dir → $remote_dir"
    
    # Create remote directory
    curl -s -k --ftp-ssl -u "$USER:$PASS" -Q "MKD $remote_dir" "ftp://$HOST/" 2>/dev/null || true
    
    # Upload all files recursively
    find "$local_dir" -type f | while read -r file; do
        relative_path="${file#$local_dir/}"
        remote_path="$remote_dir/$relative_path"
        remote_subdir=$(dirname "$remote_path")
        
        # Create subdirectory if needed
        curl -s -k --ftp-ssl -u "$USER:$PASS" -Q "MKD $remote_subdir" "ftp://$HOST/" 2>/dev/null || true
        
        # Upload file
        filename=$(basename "$file")
        curl -s -k --ftp-ssl -u "$USER:$PASS" -T "$file" "ftp://$HOST$remote_path"
        echo "  📤 $filename"
    done
    
    echo "✓ $lang website uploaded"
}

# EN Website (public_html/eng)
upload_dir "$WEBSITE_DIR/eng" "/home/colombia6/public_html/eng" "🇬🇧 EN"

echo ""

# ES Website
upload_dir "$WEBSITE_DIR/esp" "/home/colombia6/esp.colombia-staking.com" "🇪🇸 ES"

echo ""

# FR Website
upload_dir "$WEBSITE_DIR/fr" "/home/colombia6/fr.colombia-staking.com" "🇫🇷 FR"

echo ""
echo "=== All websites uploaded successfully! ==="
echo ""
echo "Test at:"
echo "  EN: https://colombia-staking.com"
echo "  ES: https://esp.colombia-staking.com"
echo "  FR: https://fr.colombia-staking.com"
