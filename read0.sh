#!/bin/dash

for n in one two three
do
    read -r line
    echo Line $n "$line"
done