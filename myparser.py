from contextlib import suppress
import inspect

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from ast import *


def make_parser():

    #---------------------------------Грамматика блока SELECT------------------------------------------

    INVERTED_COMMA = pp.Literal('\'')
    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    MULT, ADD, CONC = pp.oneOf(('* /')), pp.oneOf(('+ -')), pp.Literal('||')
    SELECT = pp.Keyword("SELECT")
    DISTINCT = pp.Keyword('DISTINCT')
    star = pp.Literal('*')

    column = pp.Regex(r'\w+(\.\w+)?')
    num = ppc.fnumber
    str_const = INVERTED_COMMA + pp.Word(pp.alphas + pp.nums + "_" + " ") + INVERTED_COMMA
    func_name = pp.Word(pp.alphas + pp.nums + "_")

    conc = pp.Forward()
    func_select = func_name + LPAR + (pp.delimitedList(conc) | star) + RPAR
    group_idf = func_select | num | str_const | column | LPAR + conc + RPAR  #| LPAR + add + RPAR
    mult = group_idf + pp.ZeroOrMore(MULT + group_idf)
    add = mult + pp.ZeroOrMore(ADD + mult)
    conc << add + pp.ZeroOrMore(CONC + add)
    select_expr = conc

    select = SELECT + pp.Optional(DISTINCT) + (
                pp.Group(pp.delimitedList(select_expr)) | star)  # col_name + pp.ZeroOrMore(',' + col_name)


    #---------------------------------------Блок FROM------------------------------------------------"

    LEFT_JOIN = pp.Keyword('LEFT JOIN')
    RIGHT_JOIN = pp.Keyword('RIGHT JOIN')
    FULL_JOIN = pp.Keyword('FULL JOIN')
    JOIN = pp.Keyword('JOIN')
    ON = pp.Keyword('ON')

    EQ = pp.Literal('=')
    GR= pp.Literal('>')
    LESS = pp.Literal('<')
    GR_OR_EQ = pp.Literal('>=')
    LESS_OR_EQ = pp.Literal('<=')
    NOT_EQ = pp.Literal('<>')
    COMP_OP = GR_OR_EQ | LESS_OR_EQ | NOT_EQ | GR | LESS | EQ

    AND = pp.Keyword('AND')
    OR = pp.Keyword('OR')
    NOT = pp.Keyword('NOT')

    or_from = pp.Forward()
    bool_expr_on = select_expr + COMP_OP + select_expr
    group_on = bool_expr_on | LPAR + or_from + RPAR
    and_from = group_on + pp.ZeroOrMore(AND + group_on)
    or_from << and_from + pp.ZeroOrMore(OR + and_from)
    on = ON + or_from
    table = pp.Forward()
    JOIN_OP = LEFT_JOIN | RIGHT_JOIN | FULL_JOIN | JOIN
    join_expr = table + pp.ZeroOrMore(JOIN_OP + table + on)
    table << ppc.identifier + pp.Optional(pp.Word(pp.srange("[a-z0-9_]")))  # pp.delimitedList(alias , ".", combine=True)  #
    FROM = pp.Keyword('FROM')
    from_ = FROM + pp.Group(pp.delimitedList(join_expr))  # table_name + pp.ZeroOrMore(',' + table_name)

    # ****************  Блок WHERE **********************************

    WHERE = pp.Keyword('WHERE')
    EXISTS = pp.Keyword('EXISTS') | pp.Keyword('NOT EXISTS')
    ANY = pp.Keyword('ANY')
    ALL = pp.Keyword('ALL')
    IN = pp.Keyword('IN') | pp.Keyword('NOT IN')

    query = pp.Forward()

    subquery = LPAR + query + RPAR

    conc_= pp.Forward()
    func_select_ = func_name + LPAR + (conc_ | star) + RPAR
    group_idf_ = func_select_ | num | str_const | column | subquery | LPAR + conc_ + RPAR  # | LPAR + add + RPAR
    mult_ = group_idf_ + pp.ZeroOrMore(MULT + group_idf_)
    add_ = mult_ + pp.ZeroOrMore(ADD + mult_)
    conc_ << add_ + pp.ZeroOrMore(CONC + add_)
    select_expr_ = conc_

    subquery_in = select_expr_ + IN + LPAR + query + RPAR
    subquery_exists = EXISTS + LPAR + query + RPAR
    subquery_any_all = select_expr_ + COMP_OP + (ANY | ALL) + LPAR + query + RPAR

    or_from_ = pp.Forward()
    bool_expr_on_ = select_expr_ + COMP_OP + select_expr_
    bool_subquery = subquery_in | subquery_exists | subquery_any_all
    group_on_ = bool_subquery | bool_expr_on_ | LPAR + or_from_ + RPAR
    and_from_ = group_on_ + pp.ZeroOrMore(AND + group_on_)
    or_from_ << and_from_ + pp.ZeroOrMore(OR + and_from_)

    where = WHERE + pp.Group(pp.delimitedList(or_from_))

    """
    op_block = column + (gr_or_eq | less_or_eq | not_eq | eq | gr | less) + column
    and_block = op_block + pp.ZeroOrMore(AND + op_block)
    or_block = and_block + pp.ZeroOrMore(OR + and_block)

    where_node = WHERE + or_block
    #query = select_node + from_node + pp.Optional(where_node) 
  
    query = select
    """
    #---------------------------------------------Блок GROUP BY----------------------------------------------
    GROUP_BY = pp.Keyword('GROUP BY')

    group_by = GROUP_BY + column




    query << select + from_ + pp.Optional(where) + pp.Optional(group_by) + ';'
    start = query



    def set_parse_action_magic(rule_name: str, parser: pp.ParserElement)->None:
        if rule_name == rule_name.upper():
            return
        if rule_name in ('mult', 'add', 'conc'):
            def bin_op_parse_action(s, loc, tocs):
                node = tocs[0]
                d = list(tocs)
                for i in range(1, len(tocs) - 1, 2):
                    node = BinOpNode(BinOp(tocs[i]), node, tocs[i + 1])
                return node
            parser.setParseAction(bin_op_parse_action)
        elif rule_name in ('bool_expr_on', 'bool_expr_on_'):
            def bool_expr_on_parse_action(s, loc, tocs):
                tocs[1] = CompOp(tocs[1])
                node = BoolExprOnNode(*tocs)
                return node
            parser.setParseAction(bool_expr_on_parse_action)
        elif rule_name == 'subquery_any_all':
            def subquery_any_all_parse_action(s, loc, tocs):
                tocs[1] = CompOp(tocs[1])
                node = SubqueryAnyAllNode(*tocs)
                return node
            parser.setParseAction(subquery_any_all_parse_action)
        elif rule_name in ('and_from', 'or_from', 'and_from_', 'or_from_'):
            def bool_expr_on_parse_action(s, loc, tocs):
                node = tocs[0]
                for i in range(1, len(tocs) - 1, 2):
                    node = BoolFromNode(node, tocs[i], tocs[i + 1])
                return node
            parser.setParseAction(bool_expr_on_parse_action)
        elif rule_name == 'join_expr':
            def join_expr_parse_action(s, loc, tocs):
                node = tocs[0]
                for i in range(1, len(tocs) - 1, 3):
                    node = JoinExprNode(node, tocs[i], tocs[i + 1], tocs[i+2])
                return node
            parser.setParseAction(join_expr_parse_action)
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls_str = cls
                cls = eval(cls)
                if not inspect.isabstract(cls):
                    def parse_action(s, loc, tocs):
                        print(type(cls), cls_str, tocs)
                        return cls(*tocs)

                    parser.setParseAction(parse_action)
        '''
        if rule_name == 'col_name':
            def col_name_action(s, loc, tocs):
                print('tocs len is ', len(tocs))
                for i in range(10):
                    print(tocs[i])
                node = ColumnNode(tocs[0])
                return node
            parser.setParseAction(col_name_action)
        elif rule_name == 'table_name':
            def table_name_action(s, loc, tocs):
                node = TableNode(tocs[0])
                return node
            parser.setParseAction(table_name_action)
        elif rule_name == 'star':
            def star_action(s, loc, tocs):
                node = StarNode()
                return node
            parser.setParseAction(star_action)
        elif rule_name == 'select_node':
            def select_action(s, loc, tocs):
                if tocs[1] == 'DISTINCT':
                    if isinstance(tocs[2], StarNode):
                        node = SelectNode(True, tocs[2:])
                    else:
                        node = SelectNode(True, tocs[2])
                else:
                    if isinstance(tocs[1], StarNode):
                        node = SelectNode(False, tocs[1:])
                    else:
                        node = SelectNode(False, tocs[1])
                return node
            parser.setParseAction(select_action)
        elif rule_name == 'query':
            def query_action(s, loc, tocs):
                if isinstance(tocs[2], WhereNode):
                    node = QueryNode(tocs[0], tocs[1], tocs[2])
                else:
                    node = QueryNode(tocs[0], tocs[1])
                return node
            parser.setParseAction(query_action)
        elif rule_name == 'from_node':
            def from_action(s, loc, tocs):
                node = FromNode(tocs[1])
                return node
            parser.setParseAction(from_action)
        elif rule_name == 'on_node':
            def on_action(s, loc, tocs):
                node = OnNode(tocs[1], tocs[3])
                return node
            parser.setParseAction(on_action)
        elif rule_name == 'join_node':
            def join_action(s, loc, tocs):
                if tocs[1] == 'JOIN':
                    node = JoinNode(tocs[1], tocs[0], tocs[2], tocs[3])
                elif tocs[1] == 'INNER':
                    node = JoinNode('INNER JOIN', tocs[0], tocs[3], tocs[4])
                elif tocs[1] == 'LEFT':
                    node = JoinNode('LEFT OUTER JOIN', tocs[0], tocs[4], tocs[5])
                elif tocs[1] == 'RIGHT':
                    node = JoinNode('RIGHT OUTER JOIN', tocs[0], tocs[4], tocs[5])
                elif tocs[1] == 'FULL':
                    node = JoinNode('FULL OUTER JOIN', tocs[0], tocs[4], tocs[5])
                return node
            parser.setParseAction(join_action)

        elif rule_name == 'op_block':
            def op_action(s, loc, tocs):
                node = OpBlockNode(tocs[1], (tocs[0], tocs[2]))  # Почему то приходят таблицы, а не столбцы
                return node
            parser.setParseAction(op_action)

        elif rule_name == 'and_block':
            def and_action(s, loc, tocs):
                node = AndBlockNode(tocs[::2])
                return node
            parser.setParseAction(and_action)

        elif rule_name == 'or_block':
            def or_action(s, loc, tocs):
                node = OrNode(tocs[::2])
                return node
            parser.setParseAction(or_action)

        elif rule_name == 'where_node':
            def where_action(s, loc, tocs):
                node = WhereNode(tocs[1:])
                return node
            parser.setParseAction(where_action)

        elif rule_name == 'str_const':
            def str_action(s, loc, tocs):
                node = StrConstNode(tocs[1])
                return node
            parser.setParseAction(str_action)

        elif rule_name == 'conc':
            def conc_action(s, loc, tocs):
                node = ConcNode(tocs[::2])
                return node
            parser.setParseAction(conc_action)

        elif rule_name == 'add':
            def add_action(s, loc, tocs):
                node = AddNode(tocs[::2])
                return node
            parser.setParseAction(add_action)

        elif rule_name == 'mult':
            def mult_action(s, loc, tocs):
                node = BinOpNode(tocs[::2])
                return node
            parser.setParseAction(mult_action)

        elif rule_name == 'num_const':
            def num_action(s, loc, tocs):
                node = NumNode(tocs[0])
                return node
            parser.setParseAction(num_action)
        '''


    for var_name, value in locals().copy().items():
        if isinstance(value, pp.ParserElement):
            set_parse_action_magic(var_name, value)
    return start


parser = make_parser()


def parse(prog: str)->QueryNode:
    print('Создание узлов:')
    temp =  parser.parseString(str(prog))[0]
    print('Создание узлов закончено')
    return temp