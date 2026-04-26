#!/usr/bin/env node
const { execSync } = require('child_process');
const output = require('child_process').execSync('node server/collector.js', { cwd: '/home/raspberry/.openclaw/workspace/network-explorer', encoding: 'utf8' });
const lines = output.split('\n');
for (const l of lines) {
    if (l.match(/titanstake|mk1r|mk2r|partners|m1r|stake24/i)) process.stdout.write(l + '\n');
}
