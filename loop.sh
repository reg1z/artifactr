#!/bin/bash
while :; do
    sleep 5;
    cat prompt.md | claude --print --verbose --dangerously-skip-permissions --output-format=stream-json
    
    # Optional: check for completion
    if [ -f "DONE.txt" ]; then
        break
    fi
done
