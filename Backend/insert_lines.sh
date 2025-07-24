#!/bin/bash

# Check if the right number of arguments are provided
if [ $# -lt 3 ]; then
  echo "Usage: $0 <filename> <keyword> <new-line> [<new-line> ...]"
  exit 1
fi

# Arguments
filename=$1
keyword=$2
shift 2  # Remove the first two arguments from the list
new_lines="$@"

# Create a temp file to store the result
temp_file=$(mktemp)

# Loop through the file and insert new lines after the keyword
while IFS= read -r line; do
  echo "$line" >> "$temp_file"
  if [[ "$line" =~ $keyword ]]; then
    for new_line in "$@"; do
      echo "$new_line" >> "$temp_file"
    done
  fi
done < "$filename"

# Replace the original file with the modified temp file
mv "$temp_file" "$filename"
