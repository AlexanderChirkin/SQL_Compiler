import exceptions
from typing import List, Tuple
class Table:
    def __init__(self, *args):
        if len(args) == 2:
            self.init_parse_table(*args)
        elif len(args) == 3:
            self.init(*args)

    def init(self, name, titles, table):
        self._name = name   # str
        self._titles = titles  # List[str]
        self._table = table # List[dict[]]
    
    def init_parse_table(self, name, table):
        self._name = name
        self._titles = table[0]
        self._table = []
        for row in range(1, len(table)):
            line = {}
            for col in range(len(table[0])):
                line[table[0][col]] = table[row][col]
            self._table.append(line)

    @property
    def name(self):
        return self._name

    @property
    def titles(self):
        return self._titles

    @property
    def table(self):
        return self._table

    def get_column(self, name: str, rows: Tuple[int] = ()) -> Tuple:
        if name not in self.titles:
            exceptions.UnknownColumn('unknown column ' + name)
        if not rows:
            rows = range(len(self.table))
        columns = []
        for row in rows:
            columns.append(self.table[row][columns])
        return columns

    def __str__(self):
        result = ""
        result += '   ' + self.name + '\n'
        for title in self.titles:
            result += '{:^30}'.format(title)
        result += '\n'
        for line in self.table:
            for title in self.titles:
                result += '{:^30}'.format(line[title])
            result += '\n'
        return result

    def cartesian_product(self, table):
        new_table = []
        for line in self.table:
            for new_line in table.table:
                cp_line = line.copy()
                for key in table.titles:
                    cp_line[key] = new_line[key]
                new_table.append(cp_line)
        self._table = new_table
        self._titles.extend(table.titles)

    def left_join(self, table, cond):
        new_table = []
        for line in self._table:
            flg = False
            for new_line in table.table:
                if cond(line, new_line):
                    flg = True
                    cp_line = line.copy()
                    for key in table.titles:
                        cp_line[key] = new_line[key]
                    new_table.append(cp_line)
            if not flg:
                cp_line = line.copy()
                for key in table.titles:
                    cp_line[key] = "Null"
                new_table.append(cp_line)
        self._table = new_table
        self._titles.extend(table.titles)

    def join(self, table, cond):
        new_table = []
        for line in self._table:
            for new_line in table.table:
                if cond(line, new_line):
                    cp_line = line.copy()
                    for key in table.titles:
                        cp_line[key] = new_line[key]
                    new_table.append(cp_line)
        self._table = new_table
        self._titles.extend(table.titles)



