#! /usr/bin/env python3 -u

for c_file in ['*.c']:
    print(f"gcc -c {c_file}")



#! /usr/bin/env python3 -u
for n in ['one', 'two', 'three']:
    print(f"Line {n} {line}")
    for k in ['four', 'five', 'six']:
        print(f"Line {n} {k} {line}")
        for j in ['seven', 'eight', 'nine']:
            print(f"Line {n} {k} {j} {line}")
            print(f"Line {n} {k} {j} {line}")
            print(f"Line {n} {k} {j} {line}")
            for i in ['ten', 'eleven', 'twelve']:
                print(f"Line {n} {k} {j} {i} {line}")