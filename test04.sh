#!/bin/dash

if [ -f "file.txt" ]; then
  echo "File exists"
else
  echo "File does not exist"
  touch file.txt
fi

echo "This is a file" > file.txt