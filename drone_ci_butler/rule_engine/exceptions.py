from typing import List, Union


class InvalidCondition(Exception):
    pass


class NotStringOrListOfStrings(Exception):
    def __init__(self, v: Union[List[str], str]):
        super().__init__(f"got invalid value {v} {type(v)}")
