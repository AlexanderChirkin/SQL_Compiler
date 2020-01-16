import exceptions
from typing import List, Tuple, Dict


class Table:
    def __init__(self, *args):
        if len(args) == 2:
            self._init_parse_table(*args)
        elif len(args) == 3:
            self._init(*args)

    def _init(self, name: str, titles: List[str], table: Dict[str, str]):
        self._name = str(name)
        self._titles = titles
        self._table = table
    
    def _init_parse_table(self, name: str, table: List[List]):  # первая строка таблицы интерпретируется как заголовки столбцов
        self._name = name
        self._titles = table[0]
        self._table = []
        for row in range(1, len(table)):
            line = {}
            for col in range(len(table[0])):
                line[table[0][col]] = table[row][col]
            self._table.append(line)

    @property
    def name(self) -> str:
        return self._name

    @property
    def titles(self) -> List[str]:
        return self._titles

    @property
    def table(self) -> Dict[str, str]:
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


class TableWrapper:
    def __init__(self, name: str, alias: str, table: Table):
        self._name = name
        self._alias = alias
        self._table = table

    @property
    def name(self) -> str:
        return self._name

    @property
    def alias(self) -> str:
        return self._alias

    @property
    def table(self) -> str:
        return self._table

    @property
    def alias_name(self) -> str:
        return self._alias if self._alias else self.name


class Var:
    def __init__(self, value, col_name: str, t_name: str, alias: str = ''):
        self.value = value
        self.col_name = col_name
        self.alias = alias
        self.t_name = t_name

class VarForAgr:
    def __init__(self, col_name: str, t_name: str, alias: str = ''):
        self.value = []
        self.col_name = col_name
        self.alias = alias
        self.t_name = t_name


class QueryContext:
    def __init__(self, tables: List[Table]):
        self._tables = {}  # name => Table
        for t in tables:
            self._tables[t.name] = t
        self._aliases = []  # List[TableWrapper]

    def add_table_to_context(self, name: str, alias: str = ''):
        if name not in self._tables:
            raise exceptions.UnknownTable('Unknown table ' + self.name + ' Table not in query context')
        for al in self._aliases:
            if al.alias == alias:
                raise exceptions.RepeatedDeclareAlias("Alias " + str(alias) + " were declare before")
        self._aliases.append(TableWrapper(name, alias, self._tables[name]))

    def get_table_by_name(self, name: str) -> TableWrapper:
        for tw in self._aliases:
            if tw.name == name:
                return tw

    def get_alias_by_name(self, name: str):
        for al, t in self._aliases.items():
            if t is self._aliases[name] and al != name:
                return al
        return ''

    def get_name_by_alias(self, alias: str) -> str:
        for a in self._aliases:
            if a.alias == alias:
                return a.name

    def get_name_by_col_name(self, col_name) -> str:
        for a in self._aliases:
            if col_name in a.table.titles:
                return a.alias_name

class Gruop:
    def __init__(self, var: Var, matched_list: List[int]):
        self._var = var
        self._matched_list = []
        self._matched_list.append(matched_list)

class VirtualTable:
    def __init__(self):
        self._tables = []
        self._matched_list = []
        self._groups = []

    def create_VT_from_T(self, table: TableWrapper):
        self._tables = [table]
        for r in range(len(table.table.table)):
            self._matched_list.append([r])

    def create_VT_from_cartesian_product(self, vt1, vt2):
        self._tables.extend(vt1._tables)
        self._tables.extend(vt2._tables)
        for ml1 in vt1._matched_list:
            for ml2 in vt2._matched_list:
                ml = []
                ml.extend(ml1)
                ml.extend(ml2)
                self._matched_list.append(ml)

    def create_VT_from_inner_join(self, vt1, vt2, func_on):
        self._tables.extend(vt1._tables)
        self._tables.extend(vt2._tables)
        for match_line1 in vt1._matched_list:
            for match_line2 in vt2._matched_list:
                context_on = ContextOn()
                context_on.append_vars(vt1.get_vars(match_line1))
                context_on.append_vars(vt2.get_vars(match_line2))
                if func_on(context_on):
                    new_match_line = []
                    new_match_line.extend(match_line1)
                    new_match_line.extend(match_line2)
                    self._matched_list.append(new_match_line)

    def get_vars(self, match_line: List[int]) -> List[Var]:
        vars = []
        for index, num in enumerate(match_line):
            for col_name, value in self._tables[index].table.table[num].items():
                vars.append(Var(value, col_name, self._tables[index].name, self._tables[index].alias))
        return vars

    def get_vars_for_agr(self):
        full_context = []
        for t_index, match_line in enumerate(self._matched_list):
            full_context.append(self.get_vars(match_line))
        vfa_list = []
        for col in range(len(full_context[0])):
            v = full_context[0][col]
            vfa = VarForAgr(v.col_name, v.t_name, v.alias)
            for row in range(len(full_context)):
                vfa.value.append(full_context[row][col].value)
            vfa_list.append(vfa)
        return vfa_list

    def get_cols(self, match_line: List[int]) -> List[str]:
        cols = []
        for index, num in enumerate(match_line):
            for col_name, value in self._tables[index].table.table[num].items():
                cols.append(str(self._tables[index].name) + str(self._tables[index].alias) + col_name)
        return cols

    def delete_some_rows(self, func_del):
        deleted_list = []
        for t_index, match_line in enumerate(self._matched_list):
            context_on = ContextOn()
            context_on.append_vars(self.get_vars(match_line))
            if not func_del(context_on):
                deleted_list.append(t_index)
        for i in range(len(deleted_list) - 1, -1, -1):
            self._matched_list.pop(deleted_list[i])


    def construct_group(self, table_name, col_name) -> None:
        for index, tw in enumerate(self._tables):
            if tw.alias_name == table_name and col_name in tw.table.titles:
                break
        else:
            pass  # exception?

        for math_line in self._matched_list:
            val = self._tables[index].table.table[math_line[index]][col_name]
            group = self.grops_contain(val)
            if group:
                group._matched_list.append(math_line)
            else:
                new_gr = Gruop(Var(val, col_name, tw.name, tw.alias), math_line)
                self._groups.append(new_gr)

    def make_select(self, functions: Tuple):
        result = []
        # if vt._groups:  # сгруппированные таблицы
        #     for group in vt.groups:
        #         line_res = []
        #         context_on = ContextOn()
        #         v = Var(group.value, group.column_name, group.table_name, context.get_alias_by_name(group.table_name))
        #         context_on._vars.append(v)
        #         # заполнить ещё данные для агрегирующих функций
        #         # for i in range(len(group.matched_list[0])):
        #         #     for math in group.matched_list:
        #         #         vt.tables[i].get_column()
        #         for c in self.col:
        #             line_res.append(c.get_value(context_on))
        #         result.append(line_res)
        # else:  # одна таблица
        #result.append(self.get_cols(self._matched_list[0]))
        for t_index, match_line in enumerate(self._matched_list):
            line_res = []
            context_on = ContextOn()
            context_on.append_vars(self.get_vars(match_line))
            context_on.append_clumn_for_agr(self.get_vars_for_agr())
            for f in functions:
                line_res.append(f(context_on))
            result.append(line_res)
        return result


    def get_rows(self):
        for match in self._matched_list:
            row = []
            for index, value in enumerate(match):
                for key, value2 in dict.items(self._tables[index].table[value]):
                    row.append(Var(key, value2, self._tables[index]))
            yield row

    def __str__(self) -> str:
        result = ""
        for match in self._matched_list:
            for index, num in enumerate(match):
                for col_name, value in self._tables[index].table.table[num].items():
                    result += '{:^30}'.format(value)
            result += '\n'
        return result

    def grops_contain(self, value):
        for g in self._groups:
            if g._var.value == value:
                return g
        return None


class ContextOn:
    def __init__(self):
        self._vars = []
        self.columns_for_agr = []
        self.flag_pointer = True

    def find_col(self, name: str):
        for t in self.tables:
            if name in t:
                return t[name]
                break
        else:
            raise exceptions.UnknownColumn("unknown column " + name)

    def find_by_col_name(self, col_name: str):
        for v in self._vars if self.flag_pointer else self.columns_for_agr:
            if v.col_name == col_name:
                return v.value
        raise exceptions.UnknownColumn("unknown column " + col_name)

    def find_by_table_and_col(self, t_name: str, col_name: str):
        for v in self._vars if self.flag_pointer else self.columns_for_agr:
            if (v.alias == t_name or v.t_name == t_name) and v.col_name == col_name:
                return v.value
        raise exceptions.UnknownColumn("unknown column " + col_name)

    def append_vars(self, vars: List[Var]):
        self._vars.extend(vars)

    def append_clumn_for_agr(self, cols: List[VarForAgr]):
        self.columns_for_agr.extend(cols)





