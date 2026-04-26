#!/usr/bin/env node
const { execSync } = require('child_process');
const output = require('child_process').execSync('node server/collector.js 2>/dev/null', { cwd: '/home/raspberry/.openclaw/workspace/network-explorer', encoding: 'utf8' });
const lines = output.split('\n');
for (const l of lines) {
    if (l.match(/findObserver|STEP|mk1r|mk2r|titanstake|mk1|mk2|m1r/i)) process.stdout.write(l + '\n');
}
