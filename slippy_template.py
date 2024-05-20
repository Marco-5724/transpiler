#! /usr/bin/python3

import sys
import glob
import re

outputs = []


class Output:
    def __init__(self, out, comment="", imports=None):
        self.imports = imports
        self.out = out
        self.comment = comment


class Line:
    def __init__(self, line):
        line = line.rstrip('\n')
        self.line = ''
        self.comment = ''

        if line.startswith('#!'):
            self.line = line
        else:
            index = line.find('#')
            if index >= 0:
                self.line = line[: index]
                self.comment = line[index:]
            else:
                self.line = line


class Command:
    match_pattern = ""

    def __init__(self, lines):
        self.lines = lines

    def run(self):
        # 判断是否有内容
        while self.lines:
            # 检查每一行
            for k, v in sorted(globals().items()):
                if self.lines and re.search(r'\w+Command', k):
                    instance = globals()[k](self.lines)
                    if instance.match_pattern and re.search(instance.match_pattern, self.lines[0].line):
                        print(k, self.lines[0].line)
                        instance.analyse()

    def analyse(self):
        print('Command analyse')
        pass


class BlankCommand(Command):
    # 全是空格的情况下
    match_pattern = '^\s*$'

    def analyse(self):
        file_line = self.lines.pop(0)
        outputs.append(Output(file_line.comment))


class CdCommand(Command):
    match_pattern = r'(\s*)cd (.*)'

    def analyse(self):
        # 判断是否有内容
        m = re.search(CdCommand.match_pattern, self.lines[0].line)
        if m:
            file_line = self.lines.pop(0)
            out = f"{m.group(1)}os.chdir('{m.group(2).strip()}'"
            outputs.append(Output(out, file_line.comment, 'import os'))


if __name__ == '__main__':
    content = '''#!/bin/dash

if test -r /dev/null
then
    echo a
fi

if test -r nonexistantfile
then
    echo b
fi

    '''
    # with open(sys.argv[1]) as file:
    inputs = [Line(line) for line in content.split('\n')]
    command = Command(inputs)
    command.run()

    print(outputs.pop(0).out)

    imports = []
    for output in outputs:
        if output.imports and output.imports not in imports:
            imports.append(output.imports)
    if imports:
        print()
        # 排序输出
        for item in imports:
            print(item)
    for output in outputs:
        print(output.out, output.comment)
