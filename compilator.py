import myparser, ast, table
from enum import Enum
import os
import myparser
from typing import Callable, Tuple, Optional, Union
from table import Table
import random


def compilate(tables: Tuple[Table], query: ast.QueryNode) -> Table:
    context = ast.QueryContext(tables)
    res = query.execute(context)
    return res
