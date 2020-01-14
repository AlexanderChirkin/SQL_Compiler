from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Union
from enum import Enum
from table import Table
import exceptions

class Gruop:
    def __init__(self, table_name: str, col_name: str, val):
        self.table_name = table_name
        self.column_name = col_name
        self.value = val
        self.matched_list = []

class Var:
    def __init__(self, value, col_name: str, t_name: str, alias: str = ''):
        self.t_name = t_name
        self.value = value
        self.col_name = col_name
        self.alias = alias

class VirtualTable:
    def __init__(self):
        self.tables = []
        self.matched_list = []
        self.groups = []

    def createVTFromT(self, table: Table):
        self.tables = [table]
        for r in range(0, len(table.table)):
            self.matched_list.append([r])

    def get_rows(self):
        for match in self.matched_list:
            row = []
            for index, value in enumerate(match):
                for key, value2 in dict.items(self.tables[index].table[value]):
                    row.append(Var(key, value2, self.tables[index]))
            yield row

    def __str__(self) -> str:
        result = ""
        for match in self.matched_list:
            for index, num in enumerate(match):
                for col_name, value in self.tables[index].table[num].items():
                    result += '{:^30}'.format(value)
            result += '\n'
        return result

    def grops_contain(self, value):
        for g in self.groups:
            if g.value == value:
                return g
        return None



class Type(Enum):
    STR = 1
    NUM = 2
    TABLE = 3
    BOOL = 4
    STAR = 5
    NULL = 6

class QueryContext:
    def __init__(self):
        self.db = {}
        self.aliases = {}

    def get_alias_by_name(self, name: str):
        for al, t in self.aliases.items():
            if t is self.aliases[name] and al != name:
                return al
        return ''

    def get_name_by_alias(self, alias:str) -> str:
        if alias in self.db:  # это уже имя таблицы   ?(или алиас, который назван также как и одна из таблиц в бд не использующаяся в запросе)
            return alias
        for key, a in self.aliases.items():  # это точно алиас
            if a is self.aliases[alias] and key != alias:
                if key in self.db:
                    return key

    def get_name_by_col_name(self, col_name) -> str:
        for key, a in self.aliases.items():
            if col_name in a.titles:
                return self.get_name_by_alias(key)


class ContextOn:
    def __init__(self):
        self.vars = []
        self.columns_for_agr = {}

    def find_col(self, name: str):
        for t in self.tables:
            if name in t:
                return t[name]
                break
        else:
            raise exceptions.UnknownColumn("unknown column " + name)

    def find_by_col_name(self, col_name: str):
        for v in self.vars:
            if v.col_name == col_name:
                return v.value
        raise exceptions.UnknownColumn("unknown column " + col_name)

    def find_by_table_and_col(self, t_name: str, col_name: str):
        for v in self.vars:
            if (v.alias == t_name or v.t_name == t_name) and v.col_name == col_name:
                return v.value
        raise exceptions.UnknownColumn("unknown column " + col_name)


class AstNode(ABC):
    @property
    def childs(self)->Tuple['AstNode', ...]:
        return ()

    #@property
    #def value(self): # str, float, table, bool
    #    return self.value

    @property
    def typ(self) -> Type:
        return self.type_

    @abstractmethod
    def __str__(self)->str:
        pass

    @property
    def tree(self)->[str, ...]:
        res = [str(self) + "   " + str(type(self))]
        childs = self.childs
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            #print(child)
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res

    def full_up_context_table(self, context: QueryContext):
        if isinstance(self, TableNode):
            if self.name in context.db:
                context.aliases[self.name] = context.db[self.name]
                if self.alias:
                    if str(self.alias) not in context.aliases:
                        context.aliases[str(self.alias)] = context.db[self.name]
                    else:
                        raise exceptions.RepeatedDeclareAlias("Alias " + str(self.alias) + " were declare before")
            else:
                raise exceptions.UnknownTable('Unknown table ' + self.name)
        if self.childs:
            for child in self.childs:
                child.full_up_context_table(context)


    def visit(self, func: Callable[['AstNode'], None])->None:
        func(self)
        map(func, self.childs)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None



class NumNode(AstNode):
    def __init__(self, num: str):
        super().__init__()
        self.num = float(num)
        self.type_ = Type.NUM

    def __str__(self) -> str:
        return str(self.num)

    def get_type(self, context) -> Type:
        return Type.NUM

    def get_value(self, context) -> float:
        return self.num

class StrConstNode(AstNode):
    def __init__(self, l_par: str, string: str, r_par: str):
        super().__init__()
        self.string = str(string)
        self.type_ = Type.STR

    def __str__(self) -> str:
        return str(self.string)

    def get_type(self, context) -> Type:
        return Type.STR

    def get_value(self, context) -> str:
        return self.string


class ColumnNode(AstNode):
    def __init__(self, name: str):
        super().__init__()
        self.full_name = str(name)
        if len(self.full_name.split('.')) == 1:
            self.col_name = self.full_name
            self.table_name = None
        else:
            self.table_name = self.full_name.split('.')[0]
            self.col_name = self.full_name.split('.')[1]

    def __str__(self) -> str:
        return str(self.full_name)

    def get_value(self, context: ContextOn):
        if not self.table_name:
            return context.find_by_col_name(self.col_name)
        else:
            return context.find_by_table_and_col(self.table_name, self.col_name)

    def get_type(self, context: ContextOn) -> Type:
        v = self.get_value(context)
        if len(str(v)) == 0: return Type.NULL
        try:
            v_i = int(v)
            return Type.NUM
        except:
            return Type.STR




class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    CON = '||'


class BinOpNode(AstNode):
    def __init__(self, op: BinOp, arg1: AstNode, arg2: AstNode):  # arg1, arg2: NumNode | ColumnNode | StrConstNode | и др.
        super().__init__()
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def childs(self) -> Tuple[AstNode, AstNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)

    def get_type(self, context) -> Type:
        type1 = self.arg1.get_type(context)
        type2 = self.arg2.get_type(context)
        if type1 != type2:
            raise exceptions.TypeMismatch('Type Mismatch ' + str(self.arg1) + ' and' + str(self.arg2))
        return type1

    def get_value(self, context): # -> STR | NUM
        t = self.get_type(context)
        v1 = self.arg1.get_value(context)
        v2 = self.arg2.get_value(context)
        if t == Type.NUM:
            if self.op == BinOp.ADD:
                return v1+v2
            elif self.op == BinOp.MUL:
                return v1*v2
            elif self.op == BinOp.SUB:
                return v1-v2
            elif self.op == BinOp.DIV:
                return v1/v2
            elif self.op == BinOp.CON:
                raise exceptions.InvalidOperator("Invalid operator" + str(self.op.value) + "for" + str(v1) + "and" + str(v2))
        else:
            if self.op == BinOp.CON:
                return v1+v2
            else:
                raise exceptions.InvalidOperator(
                    "Invalid operator" + str(self.op.value) + "for" + str(v1) + "and" + str(v2))


class FuncSelectNode(AstNode):
    def __init__(self, func_name: str, param: AstNode):
        self.param = param
        self.name = func_name

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return self.param,

    def __str__(self) -> str:
        return str(self.name)

    def get_value(self, context):
        list_func = []
        list_agr = ['sum']
        if self.name in list_func:
            pass
        elif self.name in list_agr:
            pass
        else:
             raise exceptions.UnknownFunction("unknow function " + self.name)


class StarNode(AstNode):
    def __init__(self, star: str):
        super().__init__()
        self.type_ = Type.STAR

    def __str__(self) -> str:
        return "*"


class SelectNode(AstNode):
    def __init__(self, *args): # 'SELECT' ['DISTINCT'] *|Tuple(...)
        if type(args[-1]) == StarNode:
            self.col = args[-1],
        else:
            self.col = args[-1]
        self.distinct = len(args) == 3

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.col

    def __str__(self) -> str:
        return 'SELECT' if not self.distinct else "SELECT DISTINCT"

    def get_value(self, context: QueryContext, vt: VirtualTable): # -> [[], ]
        result = []
        if vt.groups: # сгруппированные таблицы
            for group in vt.groups:
                line_res = []
                context_on = ContextOn()
                v = Var(group.value, group.column_name, group.table_name, context.get_alias_by_name(group.table_name))
                context_on.vars.append(v)
                # заполнить ещё данные для агрегирующих функций
                # for i in range(len(group.matched_list[0])):
                #     for math in group.matched_list:
                #         vt.tables[i].get_column()
                for c in self.col:
                    line_res.append(c.get_value(context_on))
                result.append(line_res)
        else:        # одна таблица
            for t_index, math_line in enumerate(vt.matched_list):
                line_res = []
                context_on = ContextOn()
                for index, num in enumerate(math_line):
                    for col_name, value in vt.tables[index].table[num].items():
                        v = Var(value, col_name, vt.tables[index].name,
                                context.get_alias_by_name(vt.tables[index].name))
                        context_on.vars.append(v)
                for c in self.col:
                    line_res.append(c.get_value(context_on))
                result.append(line_res)
        return result



class CompOp(Enum):
    EQ = '='
    GR = '>'
    LESS = '<'
    GR_OR_EQ = '>='
    LESS_OR_EQ = '<='
    NOT_EQ = '<>'


class BoolExprOnNode(AstNode):
    def __init__(self, expr1: AstNode, op: CompOp, expr2: AstNode):  # select_expr + COMP_OP + select_expr
        self.arg1 = expr1
        self.arg2 = expr2
        self.com_op = op
        self.type_ = Type.BOOL

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.com_op.value)

    def get_value(self, context: ContextOn) -> bool:
        if self.arg1.get_type(context) != self.arg2.get_type(context):
            raise exceptions.TypeMismatch('Type Mismatch ' + str(self.arg1) + ' and' + str(self.arg2))
        v1 = self.arg1.get_value(context)
        v2 = self.arg2.get_value(context)
        if self.com_op == CompOp.EQ:
            return v1 == v2
        elif self.com_op == CompOp.GR:
            return v1 > v2
        if self.com_op == CompOp.LESS:
            return v1 < v2
        if self.com_op == CompOp.GR_OR_EQ:
            return v1 >= v2
        if self.com_op == CompOp.LESS_OR_EQ:
            return v1 <= v2
        if self.com_op == CompOp.NOT_EQ:
            return v1 != v2




class BoolFromNode(AstNode):
    def __init__(self, arg1: BoolExprOnNode, op: str = '', arg2: BoolExprOnNode = None):
        self.arg1 = arg1
        self.arg2 = arg2
        self.op = op
        self.type_ = Type.BOOL

    @property
    def childs(self) -> Tuple[BoolExprOnNode]:
        return self.arg1, self.arg2

    def __str__(self):
        return str(self.op)

    def get_value(self, context) -> bool:
        v1 = self.arg1.get_value(context)
        v2 = self.arg2.get_value(context)
        if self.op == 'AND':
            return v1 and v2
        elif self.op == 'OR':
            return v1 or v2
        else:
            raise exceptions.InvalidOperator("Invalid operator " + self.op)


class TableNode(AstNode):
    def __init__(self, table_name: str, alias: str = None):
        super().__init__()
        self.name = str(table_name)
        self.alias = alias

    def __str__(self) -> str:
        return self.name + " " + str(self.alias) if self.alias else self.name

    def get_value(self, context) -> VirtualTable:
        t = VirtualTable()
        t.createVTFromT(context.aliases[str(self.alias) if self.alias else self.name])
        return t


class FromNode(AstNode):
    def __init__(self, from_, tables: Tuple[AstNode]):  # TableNode | JoinExprNode
        self.args = tables

    @property
    def childs(self) -> Tuple[TableNode]:
        return self.args

    def __str__(self) -> str:
        return 'FROM'


class OnNode(AstNode):
    def __init__(self, on: str, cond: BoolExprOnNode):
        self.cond = cond

    @property
    def childs(self) -> Tuple[ColumnNode]:
        return self.cond,

    def __str__(self):
        return "ON"

    def get_value(self, context: ContextOn) -> bool:
        return self.cond.get_value(context)


class JoinExprNode(AstNode):
    def __init__(self, table1: TableNode, join: str,  table2: TableNode, on: OnNode):  #, table1: TableNode, join: str,  table2: TableNode, on: OnNode):
        self.join = join
        self.table1 = table1
        self.table2 = table2
        self.on = on

    @property
    def childs(self) -> (TableNode, TableNode, OnNode):
        return self.table1, self.table2, self.on

    def __str__(self) -> str:
        return str(self.join)

    def inner_join(self, context: QueryContext) -> VirtualTable:
        new_vt = VirtualTable()
        vt1 = self.table1.get_value(context)
        vt2 = self.table2.get_value(context)
        for t in vt1.tables:
            new_vt.tables.append(t)
        for t in vt2.tables:
            new_vt.tables.append(t)
        for math_line1 in vt1.matched_list:
            for math_line2 in vt2.matched_list:
                context_on = ContextOn()
                for index, num in enumerate(math_line1):
                    for col_name, value in vt1.tables[index].table[num].items():
                        v = Var(value, col_name, vt1.tables[index].name, context.get_alias_by_name(vt1.tables[index].name))
                        context_on.vars.append(v)
                for index, num in enumerate(math_line2):
                    for col_name, value in vt2.tables[index].table[num].items():
                        v = Var(value,col_name, vt2.tables[index].name, context.get_alias_by_name(vt2.tables[index].name))
                        context_on.vars.append(v)
                if self.on.get_value(context_on):
                    new_match_line = []
                    for m in math_line1:
                        new_match_line.append(m)
                    for m in math_line2:
                        new_match_line.append(m)
                    new_vt.matched_list.append(new_match_line)
        return new_vt

    def get_value(self, context: QueryContext) -> VirtualTable:
        return self.inner_join(context)



class SubqueryExistsNode(AstNode):
    def __init__(self, exists,  query):
        self.query = query
        self.exists = str(exists)

    @property
    def childs(self):
        return (self.query,)

    def __str__(self):
        return self.exists


class SubqueryInNode(AstNode):
    def __init__(self, expr, in_, query):
        self.expr = expr
        self.query = query
        self.in_ = str(in_)

    @property
    def childs(self):
        return (self.expr, self.query)

    def __str__(self):
        return self.in_


class SubqueryAnyAllNode(AstNode):
    def __init__(self, expr, comp_op, any_all: str, query):
        self.expr = expr
        self.copm_op = comp_op
        self.any_all = any_all
        self.query = query

    @property
    def childs(self):
        return (self.expr, self.query)

    def __str__(self):
        return str(self.copm_op.value) + str(self.any_all)


class WhereNode(AstNode):
    def __init__(self, where: str, bool_node: Tuple[AstNode]):
        self.arg = bool_node

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.arg

    def __str__(self) -> str:
        return 'WHERE'

    def get_value(self, context: QueryContext, table: VirtualTable ) -> VirtualTable:
        deleted_list = []
        for t_index, math_line in enumerate(table.matched_list):
            context_on = ContextOn()
            for index, num in enumerate(math_line):
                for col_name, value in table.tables[index].table[num].items():
                    v = Var(value, col_name, table.tables[index].name, context.get_alias_by_name(table.tables[index].name))
                    context_on.vars.append(v)
            if not self.arg[0].get_value(context_on):
                deleted_list.append(t_index)
        for i in range(len(deleted_list)-1, -1, -1):
            table.matched_list.pop(deleted_list[i])
        return table



class GroupByNode(AstNode):
    def __init__(self, group_by: str, column: ColumnNode):
        self.column = column

    @property
    def childs(self) -> Tuple['Column']:
        return self.column,

    def __str__(self) -> str:
        return 'GROUP BY'

    def get_value(self, context: QueryContext, vt: VirtualTable) -> VirtualTable:
        col_name = self.column.col_name
        if self.column.table_name:
            table_name = context.get_name_by_alias(self.column.table_name)
        else:
            table_name = context.get_name_by_col_name(col_name)
        for index, t in enumerate(vt.tables):
            if t is context.aliases[table_name]:
                index_table_in_VT = index
                break
        else:
            pass #exception

        for math_line in vt.matched_list:
            val = vt.tables[index_table_in_VT].table[math_line[index_table_in_VT]][col_name]
            group = vt.grops_contain(val)
            if group:
                group.matched_list.append(math_line)
            else:
                new_gr = Gruop(table_name, col_name, val)
                new_gr.matched_list.append(math_line)
                vt.groups.append(new_gr)
        return vt




class QueryNode(AstNode):
    def __init__(self, *blocks: Tuple):
        super().__init__()
        self.blocks = blocks[:-1]

    @property
    def childs(self) -> Tuple[SelectNode]:
        return self.blocks

    def __str__(self) -> str:
        return str("query")

    def cartesian_product(self, table1: VirtualTable, table2: VirtualTable) -> VirtualTable:
        table = VirtualTable()
        table.tables.extend(table1.tables)
        table.tables.extend(table2.tables)
        for ml1 in table1.matched_list:
            for ml2 in table2.matched_list:
                ml = []
                ml.extend(ml1)
                ml.extend(ml2)
                table.matched_list.append(ml)
        return table


    def execute(self, context: QueryContext) -> VirtualTable:
        for child in self.childs:
            if isinstance(child, FromNode):
                child.full_up_context_table(context) # заносим таблицы из from в контекст
                table = child.childs[0].get_value(context)
                for i in range(1, len(child.childs)): # таблица может получиться с несколькими одинаковыми именами столбцов
                    table = self.cartesian_product(table, child.childs[i].get_value(context))

                #return table
                for child in self.childs:
                    if isinstance(child, WhereNode):
                        table = child.get_value(context, table)

                for child in self.childs:
                    if isinstance(child, GroupByNode):
                        table = child.get_value(context, table)

                for child in self.childs:
                    if isinstance(child, SelectNode):
                        table = child.get_value(context, table)

                return table
