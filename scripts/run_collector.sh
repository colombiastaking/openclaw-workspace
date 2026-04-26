#!/bin/bash
cd /home/raspberry/.openclaw/workspace/network-explorer
node server/collector.js 2>&1 | grep -iE "titanstake|mk1r|mk2r|partners|m1r|stake24" | head -30