
class CodeWriter:
    class CodeWriterError(Exception):
        pass

    def __init__(self):
        self.indent_count = 0
        self.content = ''
        self.in_fragment = False

    def indent(self):
        if self.in_fragment:
            raise CodeWriter.CodeWriterError('Cannot indent while writing a line fragment')
        self.indent_count = self.indent_count + 1

    def unindent(self):
        if self.in_fragment:
            raise CodeWriter.CodeWriterError('Cannot unindent while writing a line fragment')
        self.indent_count = self.indent_count - 1

    def write(self, code, *args):
        self.write_fragment(code, *args)
        self.new_line()

    def new_line(self):
        self.content = self.content + '\n'.format()
        self.in_fragment = False

    def write_fragment(self, code, *args):
        if self.in_fragment:
            self.content = self.content + code.format(*args)
        else:
            self.content = self.content + ('\t'*self.indent_count).format() + code.format(*args)

        self.in_fragment = True

    def write_to_file(self, file_name):
        if self.in_fragment:
            self.new_line()

        with open(file_name, 'w') as file:
            file.write(self.content)

