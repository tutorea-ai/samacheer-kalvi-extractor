#!/bin/bash
# Delete files older than 24 hours from temp directory

TEMP_DIR="storage/temp"
HOURS=24

echo "🧹 Starting temp file cleanup..."
echo "Directory: $TEMP_DIR"
echo "Retention: $HOURS hours"

# Find and delete files older than HOURS
find "$TEMP_DIR" -type f -mtime +1 -delete

echo "✅ Cleanup complete!"