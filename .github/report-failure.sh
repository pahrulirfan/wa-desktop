#!/usr/bin/env bash
# Turn the tail of each log in $RUNNER_TEMP/logs into an error annotation, so the reason for a
# failure is visible on the run summary page without opening (or downloading) the full log.
shopt -s nullglob
for log in "$RUNNER_TEMP"/logs/*.log; do
    body="$(tail -c 3000 "$log" | tr -d '\r' | sed 's/%/%25/g' | awk 'BEGIN{ORS="%0A"} {print}')"
    echo "::error title=$(basename "$log")::${body}"
done
