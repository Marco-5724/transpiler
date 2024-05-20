#!/bin/dash

filename=file_demo00.txt

if test -e $filename; then
    echo "$filename exists"
else
    echo "$filename does not exist"
    touch $filename
fi

if test -s $filename; then
    echo "$filename is not empty"
else
    echo "$filename is empty"
fi


chmod u+x $filename

if test -x $filename; then
    echo "$filename is executable"
else
    echo "$filename is not executable"
fi

if test -L $filename; then
    echo "$filename is a symbolic link"
else
    echo "$filename is not a symbolic link"
fi