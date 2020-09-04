import dataclasses
from typing import Optional, List


@dataclasses.dataclass
class ConditionClause:
    conditions: Optional[List['ConditionClause']]
    key: Optional[str]
    value: Optional[str]
    join_type: Optional[str]
    operator: Optional[str]


'''
(1=11 and 2=22) or (3=33 and 4=44) can be represented:

{
    'conditions': [
        {
            'conditions': [
                {'key': '1', 'value': '11', 'operator': 'int_eq'},
                {'key': '2', 'value': '22', 'operator': 'int_lte'}
            ],
            'join_type': 'AND'
        },
        {
            'conditions': [
                {'key': '3', 'value': '33', 'operator': 'str_eq'},
                {'key': '4', 'value': '44', 'operator': 'int_gte'}
            ],
            'join_type': 'AND'
        }
    ],
    'join_type': 'OR'
}
'''
