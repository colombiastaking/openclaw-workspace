#!/usr/bin/env node
const { execSync } = require('child_process');
const output = require('child_process').execSync('node server/collector.js 2>/dev/null', { cwd: '/home/raspberry/.openclaw/workspace/network-explorer', encoding: 'utf8' });
const lines = output.split('\n');
for (const l of lines) {
    if (l.match(/STEP|identity.*multikey|owner.*multikey|observerIPs|Nodes multikey/i)) process.stdout.write(l + '\n');
}
