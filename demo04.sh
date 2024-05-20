#!/bin/dash

echo *

C_files=*.[ch]
echo $C_files

echo all of the single letter Python files are: ?.py

for n in one two three; do
    read line
    echo Line $n $line
    for k in four five six; do
        echo Line $n $k $line
        for j in seven eight nine; do
            echo Line $n $k $j $line
            echo Line $n $k $j $line
            echo Line $n $k $j $line
            for i in ten eleven twelve; do
                echo Line $n $k $j $i $line
            done
        done
    done
done
