

class Error(Exception):
    pass


class FormatError(Error):
    pass


class InvalidInput(Error):
    pass


class ConflictError(Error):
    pass


def load_tabular_data(inp, separator='\0'):
    rows = []
    for line in inp:
        line = line.strip()
        if not line or line.startswith('#'):
            # skip empty lines and comments
            continue

        fields = line.split(separator)
        rows.append(fields)

    return rows


def save_tabular_data(outp, rows, separator='\0'):
    for fields in rows:
        line = separator.join(fields) + '\n'
        outp.write(line)


class ExternalCommandModule(object):

    supported_directives = {}
    commands = ()
    unprocessed = ()
    processed = ()

    def load_commands(self, inp, separator=':'):
        commands = []
        unprocessed = []
        rows = load_tabular_data(inp, separator=separator)
        for fields in rows:
            directive = fields[0]
            args = fields[1:]
            command = (directive, args)
            if directive not in self.supported_directives:
                unprocessed.append(command)
                continue

            commands.append(command)

        self.commands = commands
        self.unprocessed = unprocessed

        return commands, unprocessed


    def output_unprocessed(self, outp, unprocessed=None, separator=':'):
        if unprocessed is None:
            unprocessed = self.unprocessed
        rows = (((directive,) + tuple(args)) for directive, args in unprocessed)
        save_tabular_data(outp, rows, separator=separator)


    def execute_commands(self, commands=None):
        if commands is None:
            commands = self.commands

        output = []

        for directive, args in commands:
            command_method = self.supported_directives[directive]
            if command_method is None:
                continue

            fields = command_method(*args)
            if fields:
                output.append(fields)

        self.output = output


    def process_output(self, output=None):
        if output is None:
            output = self.output

        return output


    def save_output(self, outp, output=None, separator=':'):
        if output is None:
            output = self.output

        if output:
            save_tabular_data(outp, output, separator=separator)


    def main(self):

        import sys
        import traceback

        exc = None
        exit_code = 0

        try:
            commands, unprocessed = self.load_commands(sys.stdin, separator=':')
        except FormatError as exc:
            exit_code = 1
        except Exception as exc:
            exit_code = 127

        if exc is not None:
            traceback.print_exc()
            sys.exit(exit_code)

        exc = None
        try:
            self.output_unprocessed(sys.stdout, unprocessed, separator=':')
        except Exception as exc:
            exit_code = 126

        if exc is not None:
            traceback.print_exc()
            sys.exit(exit_code)

        exc = None
        try:
            output = self.execute_commands(commands)
        except Exception as exc:
            exit_code = 125

        if exc is not None:
            traceback.print_exc()
            sys.exit(exit_code)

        exc = None
        try:
            output = self.process_output(output=output)
        except Exception as exc:
            exit_code = 124

        if exc is not None:
            traceback.print_exc()

        exc = None
        try:
            self.save_output(sys.stdout, output=output)
        except Exception as exc:
            exit_code = 123

        if exc is not None:
            traceback.print_exc()

        sys.exit(exit_code)

