# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import unittest

from trytond.tests.test_tryton import activate_module, with_transaction
from trytond.pool import Pool


class FieldContextTestCase(unittest.TestCase):
    "Test context on field"

    @classmethod
    def setUpClass(cls):
        activate_module('tests')

    @with_transaction()
    def test_context(self):
        pool = Pool()
        Parent = pool.get('test.field_context.parent')
        Child = pool.get('test.field_context.child')
        child = Child()
        child.save()
        parent = Parent(name='foo', child=child)
        parent.save()
        self.assertEqual(parent.child._context['name'], 'foo')

        parent.name = 'bar'
        parent.save()
        self.assertEqual(parent.child._context['name'], 'bar')


def suite():
    func = unittest.TestLoader().loadTestsFromTestCase
    suite = unittest.TestSuite()
    for testcase in (FieldContextTestCase,):
        suite.addTests(func(testcase))
    return suite
