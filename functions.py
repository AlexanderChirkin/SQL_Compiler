#from ast import AstNode
from enum import Enum
from enums import Type
from typing import Callable, Tuple, Optional, Union, List, Dict
import exceptions
import math

class Kind(Enum):
    COMMON = 1
    AGR = 2


class Function:
    def __init__(self, name: str, kind: Kind, in_par: List[Type], _type: Type, func):
        self._name = name
        self._kind = kind
        self._input_parameters = in_par
        self._type = _type
        self._action = func

    @property
    def name(self) -> str:
        return self._name

    @property
    def kind(self) -> Kind:
        return self._kind

    @property
    def input_parameters(self) -> List[Type]:
        return self._input_parameters

    @property
    def type(self) -> Type:
        return self._type

    def execute(self, input_par: List):
        if len(input_par) != len(self._input_parameters):
            raise exceptions.CounOfParametersFunctionError('Wrong count of parameters in ' + self._name)
        # for i in range(len(input_par)):
        #     if input_par[i].get_type() != self._input_parameters[i]:
        #         raise exceptions.TypeOfParameterFunctionError('Incorrect type')
        return self._action(*input_par)


class FunctionsPack:
    def __init__(self):
        self._create_functions()

    def _create_functions(self):
        self._functions = {}
        f = Function('num_to_str', Kind.COMMON, [Type.NUM], Type.STR, str)
        self._functions[f.name] = f
        f = Function('str_to_num', Kind.COMMON, [Type.STR], Type.NUM, float)
        self._functions[f.name] = f
        def lower (in_str):
            in_str.lower()
            return in_str
        f = Function('lower', Kind.COMMON, [Type.STR], Type.STR, lower)
        self._functions[f.name] = f
        def upper (in_str):
            in_str.lower()
            return in_str
        f = Function('upper', Kind.COMMON, [Type.STR], Type.STR, upper)
        self._functions[f.name] = f
        f = Function('length', Kind.COMMON, [Type.STR], Type.NUM, len)
        self._functions[f.name] = f
        f = Function('abs', Kind.COMMON, [Type.NUM], Type.NUM, math.fabs)
        self._functions[f.name] = f
        f = Function('ceil', Kind.COMMON, [Type.NUM], Type.NUM, math.ceil)
        self._functions[f.name] = f
        f = Function('floor', Kind.COMMON, [Type.NUM], Type.NUM, math.floor)
        self._functions[f.name] = f
        f = Function('sqrt', Kind.COMMON, [Type.NUM], Type.NUM, math.sqrt)
        self._functions[f.name] = f

    @property
    def functions(self) -> Dict[str, Function]:
        return self._functions

