#!/bin/dash

string=BAR
echo FOO${string}BAZ


echo 'hello    world'

echo 'This is not a $variable'

echo 'This is not a glob *.sh'

echo "hello    world"

echo "This is sill a $variable"

echo "This is not a glob *.sh"

echo This program is: $0

file_name=$2
number_of_lines=$5

echo going to print the first $number_of_lines lines of $file_name