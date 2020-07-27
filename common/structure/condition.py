from typing import Optional, List

import deserialize


@deserialize.default('conditions', None)
@deserialize.default('key', None)
@deserialize.default('value', None)
@deserialize.default('join_type', 'OR')
class ConditionClause:
    conditions: Optional[List['ConditionClause']]
    key: str
    value: str
    join_type: str


'''
(1=11 and 2=22) or (3=33 and 4=44) can be represented:

{
    'conditions': [
        {
            'conditions': [
                {'key': '1', 'value': '11'},
                {'key': '2', 'value': '22'}
            ],
            'join_type': 'AND'
        },
        {
            'conditions': [
                {'key': '3', 'value': '33'},
                {'key': '4', 'value': '44'}
            ],
            'join_type': 'AND'
        }
    ],
    'join_type': 'OR'
}
'''
