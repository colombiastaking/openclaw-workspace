#!/bin/bash
# Generic FTP helper for cPanel operations using curl
# Uses credentials from ~/.openclaw/secrets/.ftp_credentials
#
# IMPORTANT: Uses curl instead of lftp because lftp has SSL timeout issues
# with this server. curl --ftp-ssl works properly.

source ~/.openclaw/secrets/.ftp_credentials

ACTION="${1:-test}"

case "$ACTION" in
    test)
        echo "=== FTP Connection Test (all 4 sites) ==="
        echo ""
        echo "DApp (staking.colombia-staking.com):"
        curl -s -k --ftp-ssl -u "$DAPP_USER:$DAPP_PASS" "ftp://$DAPP_HOST/" --list-only 2>&1 | head -3
        echo ""
        echo "EN (colombia-staking.com):"
        curl -s -k --ftp-ssl -u "$ENG_USER:$ENG_PASS" "ftp://$ENG_HOST/" --list-only 2>&1 | head -3
        echo ""
        echo "ES (esp.colombia-staking.com):"
        curl -s -k --ftp-ssl -u "$ESP_USER:$ESP_PASS" "ftp://$ESP_HOST/" --list-only 2>&1 | head -3
        echo ""
        echo "FR (fr.colombia-staking.com):"
        curl -s -k --ftp-ssl -u "$FR_USER:$FR_PASS" "ftp://$FR_HOST/" --list-only 2>&1 | head -3
        ;;
    list-dapp)
        echo "=== Listing DApp directory ==="
        curl -s -k --ftp-ssl -u "$DAPP_USER:$DAPP_PASS" "ftp://$DAPP_HOST/home/colombia6/staking.colombia-staking.com/" --list-only 2>&1
        ;;
    list-eng)
        echo "=== Listing EN website ==="
        curl -s -k --ftp-ssl -u "$ENG_USER:$ENG_PASS" "ftp://$ENG_HOST/home/colombia6/public_html/" --list-only 2>&1
        ;;
    list-esp)
        echo "=== Listing ES website ==="
        curl -s -k --ftp-ssl -u "$ESP_USER:$ESP_PASS" "ftp://$ESP_HOST/home/colombia6/esp.colombia-staking.com/" --list-only 2>&1
        ;;
    list-fr)
        echo "=== Listing FR website ==="
        curl -s -k --ftp-ssl -u "$FR_USER:$FR_PASS" "ftp://$FR_HOST/home/colombia6/fr.colombia-staking.com/" --list-only 2>&1
        ;;
    upload-dapp)
        local_file="$2"
        remote_file="$3"
        curl -s -k --ftp-ssl -u "$DAPP_USER:$DAPP_PASS" -T "$local_file" "ftp://$DAPP_HOST$remote_file" && echo "✓ Uploaded to DApp"
        ;;
    upload-eng)
        local_file="$2"
        remote_file="$3"
        curl -s -k --ftp-ssl -u "$ENG_USER:$ENG_PASS" -T "$local_file" "ftp://$ENG_HOST$remote_file" && echo "✓ Uploaded to EN"
        ;;
    upload-esp)
        local_file="$2"
        remote_file="$3"
        curl -s -k --ftp-ssl -u "$ESP_USER:$ESP_PASS" -T "$local_file" "ftp://$ESP_HOST$remote_file" && echo "✓ Uploaded to ES"
        ;;
    upload-fr)
        local_file="$2"
        remote_file="$3"
        curl -s -k --ftp-ssl -u "$FR_USER:$FR_PASS" -T "$local_file" "ftp://$FR_HOST$remote_file" && echo "✓ Uploaded to FR"
        ;;
    help|--help|-h)
        echo "FTP Helper for Colombia Staking cPanel"
        echo ""
        echo "Usage: $0 <action> [args]"
        echo ""
        echo "Actions:"
        echo "  test              - Test all 4 FTP connections"
        echo "  list-dapp         - List DApp files"
        echo "  list-eng          - List EN website files"
        echo "  list-esp          - List ES website files"
        echo "  list-fr           - List FR website files"
        echo "  upload-dapp <f> <r>  - Upload file to DApp"
        echo "  upload-eng <f> <r>   - Upload file to EN"
        echo "  upload-esp <f> <r>   - Upload file to ES"
        echo "  upload-fr <f> <r>    - Upload file to FR"
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Use: $0 help"
        ;;
esac
