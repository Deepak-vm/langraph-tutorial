#!/bin/bash
# Interactive Custom Date Git Commit Helper for this repository
#git dcomit

echo "========================================="
echo "       Git Dated Commit Helper          "
echo "========================================="

# Prompt for Date
read -p "Enter Commit Date (e.g. 27 MARCH 2026 or 2026-03-27) [Press Enter for Today]: " INPUT_DATE

if [ -z "$INPUT_DATE" ]; then
    COMMIT_DATE=$(date --iso-8601=seconds)
else
    # Prompt for Time
    read -p "Enter Commit Time (e.g. 12:00:00) [Default: 12:00:00]: " INPUT_TIME
    INPUT_TIME=${INPUT_TIME:-"12:00:00"}
    
    # Format date and time
    COMMIT_DATE=$(date -d "$INPUT_DATE $INPUT_TIME" --iso-8601=seconds 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "❌ Error: Invalid date/time format!"
        exit 1
    fi
fi

# Prompt for Commit Message
read -p "Enter Commit Message: " MSG

if [ -z "$MSG" ]; then
    echo "❌ Error: Commit message cannot be empty!"
    exit 1
fi

echo "-----------------------------------------"
echo "📅 Commit Date: $COMMIT_DATE"
echo "💬 Message:     $MSG"
echo "-----------------------------------------"

GIT_AUTHOR_DATE="$COMMIT_DATE" GIT_COMMITTER_DATE="$COMMIT_DATE" git commit -m "$MSG"
