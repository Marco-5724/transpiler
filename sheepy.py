#! /usr/bin/env python3

import sys
import keyword
import re
import os


class LineParser:

    def __init__(self, line, import_manager=None):
        line = line.rstrip('\n')
        line = line.strip()

        self.line = ''
        self.comment = ''
        self.import_manager = import_manager
        self.glob_parts = []

        # to separate the line from the comment
        pattern = r'(\".*?\"|\'.*?\')|(\#.*)'
        matches = re.findall(pattern, line)

        comment = None
        for match in matches:
            if match[1]:  # the comment group in the regex
                comment = match[1]

        if comment is not None:
            comment_index = line.find(comment)
            self.line = line[: comment_index]
            self.comment = line[comment_index:]
        else:
            self.line = line

        self.translate()

    def has_glob(self):
        # check if the line has a globbing pattern
        if re.search(r'\*[^*]*|\[[^\]]*\]|\?.[^\?]*', self.line):
            if re.search(r'\'.*\'$', self.line) or re.search(r'".*"$', self.line):
                return False
            return True

    def handle_glob(self):
        if self.has_glob():
            self.import_manager.add_import('glob')
            translated_line = self.line

        glob_parts = []
        # find the globbing patterns in the line
        for match in re.finditer(r'\*[^*]*|\[[^\]]*\]|\?.[^\?]*', translated_line):
            glob_parts.append(match.group(0))
        self.glob_parts = glob_parts

    def translate(self):
        if self.line and self.line.strip():
            if self.has_glob():
                self.handle_glob()


class TestOperationTranslator():
    def __init__(self, condition):
        self.condition = condition

    def translate(self):
        # Split the condition into operands and operator
        # operands = self.condition.split()
        operands = re.findall(r'[^"\s]\S*|".+?"', self.condition)

        if len(operands) == 3:
            operand1, operator, operand2 = operands
        elif len(operands) == 2:
            operator, operand1 = operands
            operand2 = None
        else:
            return None

        # check if there are quotes around the first operand
        if operand1.startswith('"') and operand1.endswith('"'):
            operand1 = operand1[1:-1]

        if operand2:
            # check if there are quotes around the second operand
            if not re.search(r'^".*"$', operand2):
                if not re.search(r"^'.*'$", operand2):
                    if not operand2.startswith('$'):
                        operand2 = f'"{operand2}"'

        if not re.search(r'^".*"$', operand1):
            if not re.search(r"^'.*'$", operand1):
                if not operand1.startswith('$'):
                    operand1 = f"'{operand1}'"

        if operand1 and not operand2:
            if operand1.startswith('$'):
                operand1 = operand1.replace('$', '')
        # translate the operands to python format
        if operator == '-eq':
            operator = '=='
        elif operator == '-ne':
            operator = '!='
        elif operator == '-lt':
            operator = '<'
        elif operator == '-le':
            operator = '<='
        elif operator == '-gt':
            operator = '>'
        elif operator == '-ge':
            operator = '>='
        elif operator == '=':
            operator = '=='
        elif operator == '!=':
            operator = '!='
        elif operator == '-b':  # check if the file is a block special file
            return f"os.path.isblock({operand1})"
        elif operator == '-c':  # check if the file is a character special file
            return f"os.path.ischar({operand1})"
        elif operator == '-d':  # check if the file is a directory
            return f"os.path.isdir({operand1})"
        elif operator == '-e':  # check if the file exists
            return f"os.path.exists({operand1})"
        elif operator == '-f':  # check if the file is a regular file
            return f"os.path.isfile({operand1})"
        elif operator == '-g':  # check if the file is set-group-id
            return f"os.path.issetgid({operand1})"
        elif operator == '-h' or operator == '-L':  # check if the file is a symbolic link
            return f"os.path.islink({operand1})"
        elif operator == '-n':  # check if the length of the string is not zero
            return f'len({operand1}) != 0'
        elif operator == '-p':  # check if the file is a named pipe
            return f"os.path.isfifo({operand1})"
        elif operator == '-r':  # check if the file is readable
            return f"os.access({operand1}, os.R_OK)"
        elif operator == '-s':  # check if the file is not empty
            return f"os.path.getsize({operand1}) > 0"
        elif operator == '-u':  # check if the file is set-user-id
            return f"os.path.issetuid({operand1})"
        elif operator == '-w':  # check if the file is writable
            return f"os.access({operand1}, os.W_OK)"
        elif operator == '-x':  # check if the file is executable
            return f"os.access({operand1}, os.X_OK)"
        elif operator == '-z':  # check if the length of the string is zero
            return f'len({operand1}) == 0'

        return operand1, operator, operand2


class ShellTranslator:
    match_pattern = ''

    def __init__(self, lines, variable_manager=None, import_manager=None):
        self.shell_lines = lines
        self.import_manager = import_manager
        self.variable_manager = variable_manager
        self.has_backticks_variable = False

    # identify if the word is a keyword or builtin in python
    def is_keyword_or_builtin(self, word):
        return keyword.iskeyword(word) or word in dir(__builtins__)

    def get_first_line(self):
        return self.shell_lines[0].line.strip() if self.shell_lines else None

    def translate(self):
        translated_script = []
        for line in self.lines:
            # Create a translator for the line
            # Pass a reference to self to the translator, so it can access self.variables
            translator = self.create_translator_for_line(line, self)
            translated_line = translator.translate()
            if translated_line is not None:
                translated_script.append(translated_line)
        return '\n'.join(translated_script)

    def substitute_backticks(self, field):
        self.import_manager.add_import('subprocess')
        backtick_match = re.search(r'`(.*?)`', field)
        command = backtick_match.group(1).split()
        field = f'subprocess.run({command}, text=True, stdout=subprocess.PIPE).stdout'
        return field

    def substitute_variables(self, field):
        var_match = re.search(r'\$(\{?[a-zA-Z0-9_@]+\}?)', field)
        var_match_str = var_match.group(0)
        var_name = var_match.group(1)
        if var_name.startswith('{') and var_name.endswith('}'):
            var_name = var_name.strip('{}')
        if var_name in self.variable_manager.get_variables():
            # replace the variable with its value
            var_value = self.variable_manager.get_variables()[var_name]
            # if the value is a subprocess command, replace the variable with its value directly
            if var_value.startswith('subprocess.run'):
                self.has_backticks_variable = True
                if self.__class__ .__name__ == 'EchoTranslator':
                    field = field.replace(
                        '$' + var_name, f"' '.join({var_name}.strip().split())")
                else:
                    field = field.replace('$' + var_name, var_name)
            # check if the value contains a globbing pattern
            elif re.search(r'\*[^*]*|\[[^\]]*\]|\?.[^\?]*', var_value):
                if var_value.startswith('sys.argv'):
                    field = f'{{{var_name}}}'
                else:
                    self.import_manager.add_import('glob')
                    globbed_files = f"' '.join(sorted(glob.glob({var_name})))"
                    field = f'{{{globbed_files}}}'

            elif self.__class__.__name__ == 'WhileLoopTranslator' or self.__class__.__name__ == 'ForLoopTranslator' or self.__class__.__name__ == 'ConditionalTranslator':
                field = field.replace(var_match_str, f'{var_name}')
            elif self.__class__.__name__ == 'EchoTranslator' or self.__class__.__name__ == 'AssignmentTranslator':
                field = field.replace(var_match_str, f'{{{var_name}}}')
            else:
                field = field.replace(var_match_str, f'{{{var_name}}}')
        else:
            # if the variable is a python keyword or builtin, add __ to the variable name
            if self.is_keyword_or_builtin(var_name):
                field = f'{{__{var_name}}}'
            elif var_name.isdigit():  # if the field is a number, it is a sys.argv
                field = 'sys.argv[' + var_name + ']'
                if self.__class__.__name__ == 'EchoTranslator':
                    field = f'{{{field}}}'
                else:
                    field = f'{field}'
                self.import_manager.add_import('sys')

            elif var_name == '@':  # if the field is @, it is a sys.argv
                field = 'sys.argv[1:]'
                self.import_manager.add_import('sys')
            else:
                # field = f'{{{var_name}}}'
                pass

        return field


class AssignmentTranslator(ShellTranslator):

    def translate(self):
        line = self.get_first_line()
        if line and line.strip():
            pattern = r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|([^'\"]*))\s*$"
            match = re.match(pattern, line)
            if match:
                var = match.group(1)
                single_quotes_val = match.group(2)
                double_quotes_val = match.group(3)
                no_quotes_val = match.group(4)
                value = single_quotes_val or double_quotes_val or no_quotes_val

                if self.is_keyword_or_builtin(var):
                    var = f'__{var.strip()}'
                var = var.strip()

                if re.search(r'`(.*?)`', value):
                    value = self.substitute_backticks(value)
                    expression = f'{var} = {value}'
                elif re.search(r'\$\{?[a-zA-Z0-9_@]+\}?', value):
                    value = self.substitute_variables(value)
                    if value.startswith('sys.argv'):
                        expression = f'{var} = {value.strip()}'
                    else:
                        expression = f'{var} = f"{value.strip()}"'
                else:
                    expression = f'{var} = f"{value.strip()}"'
                # Save the variable and its value
                self.variable_manager.add_variable(var, value.strip())
                return expression
        return None


class EchoTranslator(ShellTranslator):

    def __init__(self, lines, variable_manager=None, import_manager=None):
        super().__init__(lines, variable_manager, import_manager)

    def translate(self):
        line = self.get_first_line()
        if line and line.startswith('echo'):
            translated_fields = []
            # remove the echo, i.e. echo "hello world" -> "hello world"
            fields = line.split('echo ')[1]
            fields = self._split_by_quotes(fields)  # split respecting quotes

            for field in fields:
                if re.search(r'\$\{?[a-zA-Z0-9_@]+\}?', field):
                    field = self.substitute_variables(field)
                elif re.search(r'`(.*?)`', field):
                    field = self.substitute_backticks(field)
                else:
                    # escape the nested quotes
                    field = field.replace('"', r'\"').replace("'", r"\'")
                    field = f'{field}'
                translated_fields.append(field)

            combined_fields = ' '.join(translated_fields)
            if self.shell_lines[0].glob_parts:
                for glob_part in self.shell_lines[0].glob_parts:
                    # replace the glob parts in shell line with the python glob line
                    # e.g. echo *.py -> print(f'{" ".join(sorted(glob.glob("*.py")))}')
                    combined_fields = combined_fields.replace(
                        f'{glob_part}', f"{{' '.join(sorted(glob.glob('{glob_part}')))}}")
                    return f'print(f"{combined_fields}")'

            if self.has_backticks_variable:
                return f'print({combined_fields})'

            return f'print(f"{combined_fields}")'
        return None

    def _split_by_quotes(self, s):
        fields = []
        field = ''
        quote = None
        prev_char = None
        for char in s:
            if char == quote:  # end of quote
                quote = None
            elif quote is not None:  # inside a quote
                field += char
            elif char in '"\'':  # start of quote
                if not re.search(r'glob.glob\(.*\)', s):
                    quote = char
                else:
                    field += char
            elif char == ' ':  # end of field
                # ignore multiple spaces when not inside a quote
                if prev_char != ' ':
                    fields.append(field)
                    field = ''
            else:  # inside a field
                field += char
            prev_char = char
        if field:  # add the last field
            fields.append(field)
        return fields


class ReadTranslator(ShellTranslator):
    def translate(self):
        line = self.get_first_line()
        if line and line.startswith('read'):
            var = line.split()[1]
            self.variable_manager.add_variable(var, var)
            return f'{var} = input()'
        return None


class CDTranslator(ShellTranslator):

    def translate(self):
        line = self.get_first_line()
        if line and line.startswith('cd '):
            self.import_manager.add_import('os')
            dir = line[3:]  # remove the cd from the start of line
            return f'os.chdir({repr(dir)})'
        return None


class ExitTranslator(ShellTranslator):

    def translate(self):
        line = self.get_first_line()
        if line and line.startswith('exit'):
            self.import_manager.add_import('sys')
            return f'sys.exit(0)'
        return None


class ConditionalTranslator(ShellTranslator):
    def __init__(self, lines, variable_manager, import_manager=None):
        super().__init__(lines, variable_manager, import_manager)
        self.current_index = 0

    def translate(self):
        if self.shell_lines[self.current_index].line.startswith('if'):
            return self._translate_if()

    def _parse_condition(self, line):
        # command is test or [, condition is the rest
        command, *condition = re.findall(r'[^"\s]\S*|".+?"', line)
        if command == 'test':
            # remove the semicolon at the end of the condition
            if condition[-2].endswith(';'):
                condition[-2] = condition[-2].strip(';')
                # remove the 'then' at the end of the condition
                condition = condition[:-1]

            result = TestOperationTranslator(' '.join(condition)).translate()

            if isinstance(result, tuple):
                operand1, operator, operand2 = result
                variable_pattern = re.compile(r'\$[a-zA-Z0-9_@]+')
                if re.search(variable_pattern, operand1):
                    operand1 = self.substitute_variables(operand1)

                if operand2 and re.search(variable_pattern, operand2):
                    operand2 = self.substitute_variables(operand2)

                return f'{operand1} {operator} {operand2}'
            elif isinstance(result, str):
                self.import_manager.add_import('os')
                return result

        else:
            return ''

    def _translate_if(self):
        if_lines = []
        while self.current_index < len(self.shell_lines):
            line = self.shell_lines[self.current_index].line.strip()
            if line.startswith('if'):
                condition = self._parse_condition(line.split(' ', 1)[1])
                if_lines.append(f'if {condition}:')
            elif line.startswith('elif'):
                condition = self._parse_condition(line.split(' ', 1)[1])
                if_lines.append(f'elif {condition}:')
            elif line.startswith('else'):
                if_lines.append('else:')
            elif line.startswith('fi'):
                self.current_index += 1
                break
            elif line.startswith('then'):
                self.current_index += 1
                continue
            else:
                translated_line, _ = translate_line(
                    self.shell_lines, self.current_index, '    ', self.variable_manager, self.import_manager)
                if translated_line[0] and translated_line[0].strip():
                    if_lines.append(translated_line[0])
            self.current_index += 1
        return if_lines, self.current_index


class ForLoopTranslator(ShellTranslator):

    def __init__(self, shell_lines: list[LineParser], current_index, variable_manager, nesting_stack, import_manager):
        super().__init__(shell_lines, variable_manager, import_manager)
        self.current_index = current_index
        self.nesting_stack = nesting_stack

    def match_iterator_iterable(self, line):
        pattern = re.compile(r'for\s+(.+)\s+in\s+(.+)')
        match = pattern.match(line.line)
        if match:
            iterator = match.group(1)  # the variable name
            iterable = match.group(2)  # the iterable
            return iterator, iterable
        return None, None

    def translate(self):
        python_lines = []

        current_line = self.shell_lines[self.current_index]

        iterator, iterable = self.match_iterator_iterable(
            current_line)

        if current_line.has_glob():
            self.import_manager.add_import('glob')
            iterable = f"sorted(glob.glob(\"{iterable}\"))"
            self.nesting_stack.append(f"for {iterator} in {iterable}:")
        else:
            self.nesting_stack.append(f"for {iterator} in {iterable.split()}:")

        self.variable_manager.add_variable(iterator, iterator)

        # add the for loop to the python code
        python_lines.append(
            f"    " * (len(self.nesting_stack) - 1) + self.nesting_stack[-1])

        # translate the loop body
        i = self.current_index + 1
        while i < len(self.shell_lines):
            line = self.shell_lines[i].line.strip()
            if line == 'done':
                self.nesting_stack.pop()
                if not self.nesting_stack:
                    i += 1
                    break
                else:
                    i += 1
                    continue
            # if the line is a nested for loop
            if line.startswith('for'):
                for_loop_translator = ForLoopTranslator(
                    self.shell_lines, i, variable_manager, self.nesting_stack, import_manager)
                # recursively translate the nested for loop
                translated_for, line_used = for_loop_translator.translate()
                for l in translated_for:
                    python_lines.append(
                        "    " * len(self.nesting_stack) + l)

                i += line_used
            else:
                translated_line, line_used = translate_line(
                    self.shell_lines, i, "    " * len(self.nesting_stack), variable_manager, import_manager)
                if translated_line[0] and translated_line[0].strip():
                    python_lines.append(translated_line[0])
                i += line_used
        return python_lines, i - self.current_index

class WhileLoopTranslator(ShellTranslator):
    def __init__(self, shell_lines: list[LineParser], current_index, variable_manager, nesting_stack, import_manager):
        super().__init__(shell_lines, variable_manager, import_manager)
        self.current_index = current_index
        self.nesting_stack = nesting_stack

    def match_condition(self, line):
        # match while test condition
        # while test -z $var -> -z $var
        # while test $var1 = $var2 -> $var1 = $var2
        test_pattern = re.compile(r'while\s+test\s+(.+)')
        test_match = test_pattern.match(line.line)
        if test_match:
            condition = test_match.group(1)
            return condition

        # match while [ condition ]
        bracket_pattern = re.compile(r'while\s+\[\s+(.+)\s+\]')
        bracket_match = bracket_pattern.match(line.line)
        if bracket_match:
            condition = bracket_match.group(1)
            return condition

        return None

    def translate(self):
        python_lines = []

        condition = self.match_condition(self.shell_lines[self.current_index])

        operand1, operator, operand2 = TestOperationTranslator(
            condition).translate()

        variable_pattern = re.compile(r'\$[a-zA-Z0-9_@]+')
        if re.search(variable_pattern, operand1):
            operand1 = self.substitute_variables(operand1)

        if operand2 and re.search(variable_pattern, operand2):
            operand2 = self.substitute_variables(operand2)

        condition = f'{operand1} {operator} {operand2}'

        # push new level to the stack
        self.nesting_stack.append(f"while {condition}:")

        # add the while loop to the python code
        python_lines.append(
            f"    " * (len(self.nesting_stack) - 1) + self.nesting_stack[-1])

        # translate the loop body
        i = self.current_index + 1
        while i < len(self.shell_lines):
            line = self.shell_lines[i].line.strip()
            if line == 'done':
                self.nesting_stack.pop()
                if not self.nesting_stack:
                    i += 1
                    break
                else:
                    i += 1
                    continue
            # if the line is a nested while loop
            if line.startswith('while'):
                while_loop_translator = WhileLoopTranslator(
                    self.shell_lines, i, variable_manager, self.nesting_stack, import_manager)
                # recursively translate the nested while loop
                translated_while, end_index = while_loop_translator.translate()
                for l in translated_while:
                    python_lines.append("    " * len(self.nesting_stack) + l)

                i = end_index
            else:
                translated_line, _ = translate_line(
                    self.shell_lines, i, "    " * len(self.nesting_stack), variable_manager, import_manager)
                if translated_line[0] and translated_line[0].strip():
                    python_lines.append(translated_line[0])
                i += 1

        return python_lines, i


def translate_line(shell_lines, current_index, indentation, variable_manager, import_manager):
    line_obj = shell_lines[current_index]
    line = line_obj.line
    comment = line_obj.comment
    if line.startswith('for'):
        nesting_stack = []
        for_loop_translator = ForLoopTranslator(
            shell_lines, current_index, variable_manager, nesting_stack, import_manager)
        translated_for, lines_used = for_loop_translator.translate()
        return [line for line in translated_for], lines_used

    elif line.startswith('while'):
        nesting_stack = []
        while_loop_translator = WhileLoopTranslator(
            shell_lines, current_index, variable_manager, nesting_stack, import_manager)
        translated_while, lines_used = while_loop_translator.translate()
        return [line for line in translated_while], lines_used

    elif line.startswith('if'):
        nesting_stack = []
        conditional_translator = ConditionalTranslator(
            shell_lines[current_index:], variable_manager, import_manager)
        translated_if, lines_used = conditional_translator.translate()
        return [indentation + line for line in translated_if], lines_used

    else:
        # ignore the lines that are not translated
        if line in ['do', 'done', 'then', 'fi']:
            return [indentation + comment], 1

        # these translators only translate one line
        translators = [AssignmentTranslator,
                       EchoTranslator, ReadTranslator, ExitTranslator, CDTranslator]
        for Translator in translators:
            translator = Translator(
                [line_obj], variable_manager, import_manager)
            translated_line = translator.translate()
            if translated_line is not None:
                return [indentation + translated_line + comment], 1

        commands = line.split()
        if commands:  # if the line is not translated by the translators above, it is a external command
            import_manager.add_import('subprocess')
            for i in range(len(commands)):
                # if the command contains a variable
                if re.search(r'\$[a-zA-Z0-9_@]+', commands[i]):
                    commands[i] = translator.substitute_variables(commands[i])
                else:
                    commands[i] = f"'{commands[i]}'"

            if 'sys.argv[1:]' in commands:
                translated_line = f'subprocess.run([{", ".join(commands[:-1])}] + {commands[-1]})'
            else:
                translated_line = f"subprocess.run([{', '.join(commands)}])"

            return [indentation + translated_line + comment], 1

    # if the line is not translated by the translators above, return the original line
    return [indentation + line + comment], 1


class VariableManager:
    def __init__(self):
        self.variables = {}

    def add_variable(self, var_name, var_value):
        self.variables[var_name] = var_value

    def get_variables(self):
        return self.variables


class ImportManager:
    def __init__(self):
        self.imports = set()

    def add_import(self, module_name):
        self.imports.add(module_name)

    def get_imports(self):
        return self.imports


if __name__ == '__main__':
    shell_path = sys.argv[1]

    variable_manager = VariableManager()
    import_manager = ImportManager()
    python_code = []

    # shell_path = 'demo03.sh'
    # shell_path = 'for_read0.sh'

    with open(shell_path) as f:
        shell_code = f.readlines()
    # remove the shebang
    shell_code = shell_code[1:]
    # divide the code into code lines and comments
    shell_lines = [LineParser(line, import_manager) for line in shell_code]
    i = 0
    print('#!/usr/bin/env python3 -u')
    # to reduce multiple empty lines to one
    prev_line_empty = False
    while i < (len(shell_lines)):
        translated_line, line_used = translate_line(
            shell_lines, i, '', variable_manager, import_manager)
        translated_line = '\n'.join(translated_line)
        if translated_line:
            python_code.append(translated_line)
            prev_line_empty = False
        elif not prev_line_empty:
            python_code.append('')
            prev_line_empty = True
        i += line_used

    # print the imports in alphabetical order
    for import_name in sorted(import_manager.get_imports()):
        print(f'import {import_name}')

    print('\n'.join(python_code))
