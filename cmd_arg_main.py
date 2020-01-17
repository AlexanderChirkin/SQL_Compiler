import sys, os
import argparse
from typing import List
from excel_reader import get_tables_from_excel
import exceptions
import myparser
from compilator import compilate


def create_parser():
    parser = argparse.ArgumentParser(prog='SQL-Compiler', description='commands: ', epilog='Use "exit" to exit')
    parser.add_argument('-l', '--load', nargs='+', help='load tables in memory', metavar='path')
    parser.add_argument('-r', '--remove', nargs='+', help='remove tables from memory', metavar='table_name')
    parser.add_argument('-s', '--show', action='store_true', default=False, help='show tables in memory')
    parser.add_argument('-q', '--query', action='store_true', default=False, help='go to write query')
    return parser


class CmdInterface:
    def __init__(self):
        self.tables = {}
        self.parser = create_parser()

    def main_loop(self):
        self.parser.print_help()
        while True:
            print('> ', end='')
            line = input()
            if line.strip() == 'exit':
                break
            try:
                namespace = self.parser.parse_args(line.split())
                # print(namespace)
                if namespace.show:
                    self.print()
                elif namespace.load:
                    self.load(paths=namespace.load)
                elif namespace.remove:
                    self.remove(names=namespace.remove)
                elif namespace.query:
                    self.query()
            except BaseException as e:  # но пока мне говорят хватит - я продолжаю
                pass

    def load(self, paths: List[str]):
        for path in paths:
            for table in get_tables_from_excel(path):
                self.tables[table.name] = table
                print('table {0} from {1} loaded successfully'.format(table.name, path))

    def print(self):
        print('{0} tables in memory'.format(len(self.tables)))
        for t in self.tables.values():
            print(t)

    def remove(self, names: List[str]):
        for name in names:
            if name in self.tables:
                self.tables.pop(name)
                print('table {0} removed'.format(name))
            else:
                exceptions.TableError('table {0} not exist in memory'.format(name))

    def query(self):
        print('Write query:')
        text_query = ' '
        while text_query[-1] != ';':
            print('...: ', end='')
            text_query += input()
        print('query: ')
        print(text_query)
        print('result: ')
        prog = myparser.parse(text_query)
        print('syntax analyse:')
        print(*prog.tree, sep=os.linesep)
        res = compilate(self.tables.values(), prog)
        print('semantic analyse:')
        for line in res:
            print(line)


if __name__ == '__main__':
    cmd_interface = CmdInterface()
    cmd_interface.main_loop()
