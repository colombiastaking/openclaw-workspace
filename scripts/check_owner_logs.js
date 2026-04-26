#!/usr/bin/env node
const { execSync } = require('child_process');
const output = execSync('node server/collector.js 2>/dev/null', { cwd: '/home/raspberry/.openclaw/workspace/network-explorer', encoding: 'utf8' });
const lines = output.split('\n');
const interesting = lines.filter(l => 
    l.match(/\[owner\]|\[owner-skip|findObserver|Nodes multikey-assigned IP|Blue \(multikey\)|Red edges|synth|Observers processed/i)
);
for(const l of interesting) process.stdout.write(l + '\n');