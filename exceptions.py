class UnknownTable(Exception):
    def __init__(self, missing: str):
        self.missing = missing

    def __str__(self):
        return str(self.missing)

class RepeatedDeclareAlias(Exception):
    def __init__(self, missing: str):
        self.missing = missing

    def __str__(self):
        return str(self.missing)

class UnknownColumn(Exception):
    def __init__(self, missing: str):
        self.missing = missing

    def __str__(self):
        return str(self.missing)

class TypeMismatch(Exception):
    def __init__(self, missing: str):
        self.missing = missing

    def __str__(self):
        return str(self.missing)
