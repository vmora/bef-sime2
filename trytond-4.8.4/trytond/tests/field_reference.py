# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import ModelSQL, fields
from trytond.pool import Pool


class Reference(ModelSQL):
    'Reference'
    __name__ = 'test.reference'
    reference = fields.Reference('Reference', selection=[
            (None, ''),
            ('test.reference.target', 'Target'),
            ])


class ReferenceTarget(ModelSQL):
    'Reference Target'
    __name__ = 'test.reference.target'
    name = fields.Char('Name', required=True)


class ReferenceRequired(ModelSQL):
    'Reference Required'
    __name__ = 'test.reference_required'
    reference = fields.Reference('Reference', selection=[
            (None, ''),
            ('test.reference.target', 'Target'),
            ], required=True)


def register(module):
    Pool.register(
        Reference,
        ReferenceTarget,
        ReferenceRequired,
        module=module, type_='model')
