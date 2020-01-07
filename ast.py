from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Union
from enum import Enum


class AstNode(ABC):
    @property
    def childs(self)->Tuple['AstNode', ...]:
        return ()

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

    def visit(self, func: Callable[['AstNode'], None])->None:
        func(self)
        map(func, self.childs)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class NumNode(AstNode):
    def __init__(self, num: str):
        super().__init__()
        self.num = float(num)

    def __str__(self) -> str:
        return str(self.num)


class StrConstNode(AstNode):
    def __init__(self, l_par: str, string: str, r_par: str):
        super().__init__()
        self.string = str(string)

    def __str__(self) -> str:
        return str(self.string)


class ColumnNode(AstNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)

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


class FuncNode(AstNode):
    def __init__(self, func_name: str, param: AstNode):
        self.param = param
        self.name = func_name

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return self.param,

    def __str__(self) -> str:
        return str(self.name)


class StarNode(AstNode):
    def __init__(self, star: str):
        super().__init__()

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



class TableNode(AstNode):
    def __init__(self, table_name: str):
        super().__init__()
        self.table_name = table_name

    def __str__(self)->str:
        return self.table_name


class FromNode(AstNode):
    def __init__(self, from_,  table: Tuple[TableNode]):
        self.arg = table

    @property
    def childs(self) -> Tuple[TableNode]:
        return self.arg

    def __str__(self)->str:
        return 'FROM'

class OnExprNode(AstNode):
    def __init__(self, *args):  # col1: ColumnNode, op: str, col2: ColumnNode
        if len(args) == 3:
            self.col1 = args[0]
            self.col2 = args[2]
            self.op = args[1]
            self.not_ = False
        elif len(args) == 4:
            self.col1 = args[1]
            self.col2 = args[3]
            self.op = args[2]
            self.not_ = True

    @property
    def childs(self) -> Tuple[ColumnNode]:
        return self.col1, self.col2

    def __str__(self):
        return self.op if not self.not_ else "NOT" + self.op


class AndFromNode(AstNode):
    def __init__(self, arg1: OnExprNode, and_: str = '', arg2: OnExprNode = None):
        if arg2:
            self.args = (arg1, arg2)
        else:
            self.args = [arg1]

    @property
    def childs(self) -> Tuple[OnExprNode]:
        return self.args

    def __str__(self):
        return "AND"


class OrFromNode(AstNode):
    def __init__(self, arg1: AndFromNode, or_: str = '', arg2: AndFromNode = None):
        if arg2:
            self.args = (arg1, arg2)
        else:
            self.args = [arg1]

    @property
    def childs(self) -> Tuple[AndFromNode]:
        return self.args

    def __str__(self)->str:
        return "OR"


class OnNode(AstNode):
    def __init__(self, on: str, cond: OrFromNode):
        self.cond = cond

    @property
    def childs(self) -> Tuple[ColumnNode]:
        return self.cond,

    def __str__(self):
        return "ON"


class JoinExprNode(AstNode):
    def __init__(self, *args):  #, table1: TableNode, join: str,  table2: TableNode, on: OnNode):
        if len(args) == 1:
            self.flag = 1
            self.table1 = args[0]
        elif len(args) == 4:
            self.flag = 2
            self.join = args[1]
            self.table1 = args[0]
            self.table2 = args[2]
            self.on = args[3]

    @property
    def childs(self) -> (TableNode, TableNode, OnNode):
        return (self.table1, self.table2, self.on) if self.flag == 2 else (self.table1 ,)

    def __str__(self)->str:
        return self.join if self.flag == 2 else ""


class SubqueryExistsNode(AstNode):
    def __init__(self, exist,  query):
        self.query = query

    @property
    def childs(self):
        return (self.query,)

    def __str__(self):
        return "subquery EXIST"


class SubqueryInNode(AstNode):
    def __init__(self, col, in_,  query):
        self.col = col
        self.query = query

    @property
    def childs(self):
        return (self.col, self.query)

    def __str__(self):
        return "subquery IN"

class OpBlockNode(AstNode):
    def __init__(self, sign: str, col_nodes: Tuple[ColumnNode]):
        self.sign = sign
        self.arg = col_nodes
        super().__init__()

    @property
    def childs(self) -> Tuple[ColumnNode]:
        return self.arg

    def __str__(self):
        return self.sign


class AndNode(AstNode):
    def __init__(self, arg1: OnExprNode, and_: str = '', arg2: OnExprNode = None):
        if arg2:
            self.args = (arg1, arg2)
        else:
            self.args = [arg1]

    @property
    def childs(self) -> Tuple[OnExprNode]:
        return self.args

    def __str__(self):
        return "AND"

class OrNode(AstNode):
    def __init__(self, arg1: AndNode, or_: str = '', arg2: AndNode = None):
        if arg2:
            self.args = (arg1, arg2)
        else:
            self.args = [arg1]

    @property
    def childs(self) -> Tuple[AndNode]:
        return self.args

    def __str__(self)->str:
        return "OR"

class WhereNode(AstNode):
    def __init__(self, where: str, or_nodes: Tuple[OrNode]):
        self.arg = or_nodes

    @property
    def childs(self) -> Tuple[OrNode]:
        return self.arg

    def __str__(self)->str:
        return 'WHERE'


'''
class QueryNode(AstNode):
    def __init__(self, select: SelectNode, from_: FromNode, where: WhereNode = None):
        super().__init__()
        self.select = select
        self.from_ = from_
        self.where = where

    @property
    def childs(self) -> Tuple[SelectNode, FromNode]:
        if self.where is None:
            return self.select, self.from_
        else:
            return self.select, self.from_, self.where

    def __str__(self)->str:
        return str("query")
'''
class QueryNode(AstNode):
    def __init__(self, *blocks: Tuple):
        super().__init__()
        self.blocks = blocks[:-1]

    @property
    def childs(self) -> Tuple[SelectNode]:
        return self.blocks

    def __str__(self)->str:
        return str("query")

