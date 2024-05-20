#!/bin/dash

a=`printf hi`
echo $a

x='###'
while test $x != '########'
do
    y='#'
    while test $y != $x
    do
        echo $y
        y="${y}#"
    done
    x="${x}#"
done

row=1
while test $row != 11111111111
do
    echo $row
    row=1$row
done
