#!/bin/bash
echo "Sending message:"
echo "$1"
echo ""
echo "$1" | /usr/local/bin/signal-cli send --message-from-stdin -g "MyGroupID"
