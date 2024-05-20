#!/bin/dash

for f in *.txt; do
    mv -- "$f" "$f.csv"
done