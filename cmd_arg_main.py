import sys
import argparse
from typing import List


def createParser():
    parser = argparse.ArgumentParser(prog='SQL-Compiler', description='commands:', epilog='Use "exit" to exit')
    parser.add_argument('-l', '--load', nargs='+', type=argparse.FileType(), help='load tables in memory', metavar='path')
    parser.add_argument('-r', '--remove', nargs='+', help='remove tables from memory', metavar='table_name')
    parser.add_argument('-s', '--show', action='store_true', default=False, help='show tables in memory')
    parser.add_argument('-q', '--query', action='store_true', default=False, help='go to write query')
    return parser


def print_tables():
    print("Show all tables  ... ...")


def load_tables(pathes: List):
    print('add tables:')
    for table in pathes:
        print(table)


def remove_tables(names: List[str]):
    print("remove tables:")
    for name in names:
        print('Try to remove table ' + name)


def query():
    print('Write query:')
    text_query = ' '
    while text_query[-1] != ';':
        print('...: ', end='')
        text_query += input()
    print('Query: ')
    print(text_query)
    print('Result: ')


def main():
    parser = createParser()
    parser.print_help()
    while True:
        print('> ', end='')
        line = input()
        if line == 'exit':
            break
        try:
            namespace = parser.parse_args(line.split(' '))
            #print(namespace)
            if namespace.show:
                print_tables()
            elif namespace.load:
                load_tables(pathes=namespace.load)
            elif namespace.remove:
                remove_tables(names=namespace.remove)
            elif namespace.query:
                query()
        except BaseException:  # но пока мне говорят хватит - я продолжаю
            continue


if __name__ == '__main__':
    main()
