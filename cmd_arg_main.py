import sys
import argparse
from typing import List


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-h2', '--help2', action='store_true', default=False)
    parser.add_argument('-q', '--query', action='store_true', default=False)
    parser.add_argument('-s', '--show', action='store_true', default=False)
    parser.add_argument('-r', '--remove', nargs='+')
    parser.add_argument('-l', '--load', nargs='+', type=argparse.FileType())

    return parser

def print_help():
    print("""
    commands:
      -h2, --help2                              show this help message
      -l p1 [p2 ...], --load p1 [p2 ...]        load tables in memory. p1, p2 - pathes to excel-tables
      -r t1 [t2 ...], --remove t1 [t2 ...]      remove tables from memory. t1, t2 - names of tables
      -s, --show                                show tables in memory
      -q, --query                               go to write query
      
      Use "exit" to exit
    """)


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


def main():
    parser = createParser()
    print_help()
    while True:
        print('> ', end='')
        line = input()
        if line == 'exit':
            break
        try:
            namespace = parser.parse_args(line.split(' '))
            print(namespace)
            if namespace.help2:
                print_help()
            elif namespace.show:
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
