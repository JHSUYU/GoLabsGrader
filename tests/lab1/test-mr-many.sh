#!/usr/bin/env bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 numTrials"
    exit 1
fi

trap 'kill -INT -$pid; exit 1' INT

# Note: because the socketID is based on the current userID,
# ./test-mr.sh cannot be run in parallel
runs=$1
test_script=$2
chmod +x "$test_script"

for i in $(seq 1 $runs); do
    timeout -k 2s 100s ./"$test_script" &
    pid=$!
    if ! wait $pid; then
        echo '***' FAILED TESTS IN TRIAL $i
        exit 1
    fi
done
echo '***' PASSED ALL $i TESTING TRIALS
