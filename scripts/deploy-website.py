#!/usr/bin/env python3
"""
deploy-website.py - Deploy Colombia Staking websites via FTP (TLS)
Replaces deploy-website.sh with Python ftplib.FTP_TLS for reliable TLS connections.

Usage:
    python3 deploy-website.py [en|es|fr|dapp|all]
    python3 deploy-website.py en es fr      # specific sites
    python3 deploy-website.py all           # all 3 websites
    python3 deploy-website.py dapp         # DApp only
"""

import ftplib
import os
import socket
import sys
from pathlib import Path

# FTP credentials
HOST = "colombia-staking.com"
USER = "colombia6"
PASS = "sMGi6hW3vikr"

# Site configs: (local_path, remote_path)
SITES = {
    "en": ("/home/raspberry/.openclaw/workspace/colombia-staking/Website/eng", "/public_html"),
    "es": ("/home/raspberry/.openclaw/workspace/colombia-staking/Website/esp", "/esp.colombia-staking.com"),
    "fr": ("/home/raspberry/.openclaw/workspace/colombia-staking/Website/fr", "/fr.colombia-staking.com"),
    "dapp": ("/home/raspberry/.openclaw/workspace/colombia-staking/DAPP-V3/build", "/staking.colombia-staking.com"),
}


def ftp_connect(timeout=30):
    """Connect via FTP/TLS"""
    socket.setdefaulttimeout(timeout)
    ftp = ftplib.FTP_TLS(HOST)
    ftp.login(USER, PASS)
    ftp.prot_p()  # Enable TLS data connection
    print(f"✅ Connected to {HOST}")
    return ftp


def upload_file(ftp, local_path, remote_dir, filename):
    """Upload single file - skip if server has identical size"""
    local_file = os.path.join(local_path, filename)
    local_size = os.path.getsize(local_file)
    
    # Skip if server file is same size (avoid re-upload)
    try:
        server_size = ftp.size(filename)
        if server_size == local_size:
            return False  # Identical, skip
    except:
        pass  # File doesn't exist or can't check size
    
    # Upload without DELE
    with open(local_file, 'rb') as f:
        ftp.storbinary(f"STOR {filename}", f)
    
    return True


def upload_directory(ftp, local_path, remote_dir, extensions=None):
    """
    Upload all files in a directory (optionally filtered by extension).
    Handles nested directories recursively.
    """
    uploaded = 0
    errors = 0
    
    for root, dirs, files in os.walk(local_path):
        # Handle subdirectories
        rel_dir = os.path.relpath(root, local_path)
        if rel_dir != '.':
            remote_subdir = f"{remote_dir}/{rel_dir}".replace('\\', '/')
            try:
                ftp.cwd(remote_subdir)
            except ftplib.all_errors:
                try:
                    ftp.mkd(remote_subdir)
                    print(f"  📁 Created: {rel_dir}")
                except ftplib.all_errors:
                    pass
                ftp.cwd(remote_subdir)
        
        for filename in sorted(files):
            if extensions and not any(filename.endswith(ext) for ext in extensions):
                continue
            
            local_file = os.path.join(root, filename)
            try:
                with open(local_file, 'rb') as f:
                    ftp.storbinary(f"STOR {filename}", f)
                uploaded += 1
                
            except ftplib.all_errors as e:
                print(f"  ❌ Error: {filename} → {e}")
                errors += 1
    
    return uploaded, errors


def deploy_site(ftp, site_key, local_path, remote_dir):
    """Deploy a single site"""
    print(f"\n{'='*50}")
    print(f"  Deploying {site_key.upper()} → {remote_dir}")
    print(f"{'='*50}")
    
    ftp.cwd("/")
    try:
        ftp.cwd(remote_dir)
    except ftplib.all_errors:
        try:
            ftp.mkd(remote_dir)
            print(f"  📁 Created remote dir: {remote_dir}")
            ftp.cwd(remote_dir)
        except ftplib.all_errors as e:
            print(f"  ❌ Can't access {remote_dir}: {e}")
            return 0, 0
    
    if site_key == "dapp":
        # DApp: upload all files (HTML, JS, assets)
        uploaded, errors = upload_directory(ftp, local_path, remote_dir)
    else:
        # Websites: upload HTML, css/, js/ only
        uploaded, errors = 0, 0
        
        # Reset to remote_dir for each subdir
        for subdir in ['', 'css', 'js']:
            local_subdir = os.path.join(local_path, subdir) if subdir else local_path
            remote_subdir = remote_dir if subdir == '' else f"{remote_dir}/{subdir}"
            
            if not os.path.isdir(local_subdir):
                continue
            
            # Create remote subdir
            try:
                ftp.cwd(remote_subdir)
            except ftplib.all_errors:
                try:
                    ftp.mkd(remote_subdir)
                except ftplib.all_errors:
                    pass
                try:
                    ftp.cwd(remote_subdir)
                except ftplib.all_errors:
                    print(f"  ⚠️ Can't create {remote_subdir}, skipping")
                    continue
            
            exts = None if subdir == '' else ['.css', '.js']
            u, e = upload_directory(ftp, local_subdir, remote_subdir, extensions=exts)
            uploaded += u
            errors += e
    
    print(f"  ✅ {uploaded} files uploaded, {errors} errors")
    return uploaded, errors


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ['all']
    
    # Resolve aliases
    sites_to_deploy = []
    for arg in args:
        if arg == 'all':
            sites_to_deploy = ["en", "es", "fr"]
        elif arg == 'dapp':
            sites_to_deploy = ["dapp"]
        elif arg in SITES:
            sites_to_deploy.append(arg)
        else:
            print(f"Unknown site: {arg}")
            print(f"Available: {' '.join(SITES.keys())}")
            sys.exit(1)
    
    if not sites_to_deploy:
        print("Usage: deploy-website.py [en|es|fr|dapp|all]")
        sys.exit(1)
    
    print(f"🚀 Deploying: {' '.join(sites_to_deploy)}")
    
    try:
        ftp = ftp_connect()
        total_uploaded = 0
        total_errors = 0
        
        for site_key in sites_to_deploy:
            local_path, remote_dir = SITES[site_key]
            if not os.path.exists(local_path):
                print(f"⚠️  Local path not found: {local_path}")
                continue
            u, e = deploy_site(ftp, site_key, local_path, remote_dir)
            total_uploaded += u
            total_errors += e
        
        ftp.quit()
        
        print(f"\n{'='*50}")
        print(f"  🎉 Done: {total_uploaded} files uploaded, {total_errors} errors")
        print(f"{'='*50}")
        
        if total_errors == 0:
            print("\n✅ All sites deployed successfully!")
            print("   LiteSpeed cache: changes should appear within minutes.")
            print("   (If not, purge via cPanel → LiteSpeed Cache → Purge All)")
        
    except ftplib.all_errors as e:
        print(f"\n❌ FTP Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
