from pypika.terms import Criterion
from pypika.utils import format_alias_sql


class ExistsCriterion(Criterion):

    def __init__(self, subquery, alias=None):
        super().__init__(alias)
        self.subquery = subquery

    def get_sql(self, **kwargs):
        sql = 'EXISTS' + self.subquery.get_sql(subquery=True)
        return format_alias_sql(sql, alias=self.alias)
