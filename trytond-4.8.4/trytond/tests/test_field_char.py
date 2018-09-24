# -*- coding: utf-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import unittest

from trytond import backend
from trytond.exceptions import UserError
from trytond.pool import Pool
from trytond.tests.test_tryton import activate_module, with_transaction
from trytond.transaction import Transaction


class CommonTestCaseMixin:

    @with_transaction()
    def test_create(self):
        "Test create char"
        Char = self.Char()

        char, char_none = Char.create([{
                    'char': "Test",
                    }, {
                    'char': None,
                    }])

        self.assertEqual(char.char, "Test")
        self.assertEqual(char_none.char, None)

    @with_transaction()
    def test_create_unicode(self):
        "Test create unicode"
        Char = self.Char()

        char, = Char.create([{
                    'char': u"é",
                    }])

        self.assertEqual(char.char, u"é")

    @with_transaction()
    def test_search_equals(self):
        "Test search char equals"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Foo",
                    }])

        chars_foo = Char.search([
                ('char', '=', "Foo"),
                ])
        chars_bar = Char.search([
                ('char', '=', "Bar"),
                ])

        self.assertListEqual(chars_foo, [char])
        self.assertListEqual(chars_bar, [])

    @with_transaction()
    def test_search_equals_none(self):
        "Test search char equals None"
        Char = self.Char()
        char, = Char.create([{
                    'char': None,
                    }])

        chars = Char.search([
                ('char', '=', None),
                ])

        self.assertListEqual(chars, [char])

    @with_transaction()
    def test_search_equals_unicode(self):
        "Test search char equals unicode"
        Char = self.Char()
        char, = Char.create([{
                    'char': u"é",
                    }])

        chars = Char.search([
                ('char', '=', u"é"),
                ])

        self.assertListEqual(chars, [char])

    @with_transaction()
    def test_search_equals_non_unicode(self):
        "Test search char equals non unicode"
        Char = self.Char()
        char, = Char.create([{
                    'char': u"é",
                    }])

        chars = Char.search([
                ('char', '=', "é"),
                ])

        self.assertListEqual(chars, [char])

    @with_transaction()
    def test_search_non_equals(self):
        "Test search char non equals"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Foo",
                    }])

        chars_foo = Char.search([
                ('char', '!=', "Foo"),
                ])
        chars_bar = Char.search([
                ('char', '!=', "Bar"),
                ])

        self.assertListEqual(chars_foo, [])
        self.assertListEqual(chars_bar, [char])

    @with_transaction()
    def test_search_non_equals_none(self):
        "Test search char non equals None"
        Char = self.Char()
        char, = Char.create([{
                    'char': None,
                    }])

        chars = Char.search([
                ('char', '!=', None),
                ])

        self.assertListEqual(chars, [])

    @with_transaction()
    def test_search_in(self):
        "Test search char in"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Foo",
                    }])

        chars_foo = Char.search([
                ('char', 'in', ["Foo"]),
                ])
        chars_bar = Char.search([
                ('char', 'in', ["Bar"]),
                ])
        chars_empty = Char.search([
                ('char', 'in', []),
                ])

        self.assertListEqual(chars_foo, [char])
        self.assertListEqual(chars_bar, [])
        self.assertListEqual(chars_empty, [])

    @with_transaction()
    def test_search_in_none(self):
        "Test search char in [None]"
        Char = self.Char()
        char, = Char.create([{
                    'char': None,
                    }])

        chars = Char.search([
                ('char', 'in', [None]),
                ])

        self.assertListEqual(chars, [char])

    @with_transaction()
    def test_search_not_in(self):
        "Test search char not in"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Foo",
                    }])

        chars_foo = Char.search([
                ('char', 'not in', ["Foo"]),
                ])
        chars_bar = Char.search([
                ('char', 'not in', ["Bar"]),
                ])
        chars_empty = Char.search([
                ('char', 'not in', []),
                ])

        self.assertListEqual(chars_foo, [])
        self.assertListEqual(chars_bar, [char])
        self.assertListEqual(chars_empty, [char])

    @with_transaction()
    def test_search_not_in_none(self):
        "Test search char not in [None]"
        Char = self.Char()
        char, = Char.create([{
                    'char': None,
                    }])

        chars = Char.search([
                ('char', 'not in', [None]),
                ])

        self.assertListEqual(chars, [])

    @with_transaction()
    def test_search_like(self):
        "Test search char like"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Bar",
                    }])

        chars_bar = Char.search([
                ('char', 'like', "Bar"),
                ])
        chars_b = Char.search([
                ('char', 'like', "B%"),
                ])
        chars_foo = Char.search([
                ('char', 'like', "Foo"),
                ])
        chars_f = Char.search([
                ('char', 'like', "F%"),
                ])

        self.assertListEqual(chars_bar, [char])
        self.assertListEqual(chars_b, [char])
        self.assertListEqual(chars_foo, [])
        self.assertListEqual(chars_f, [])

    @with_transaction()
    def test_search_ilike(self):
        "Test search char ilike"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Bar",
                    }])

        chars_bar = Char.search([
                ('char', 'ilike', "bar"),
                ])
        chars_b = Char.search([
                ('char', 'ilike', "b%"),
                ])
        chars_foo = Char.search([
                ('char', 'ilike', "foo"),
                ])
        chars_f = Char.search([
                ('char', 'ilike', "f%"),
                ])

        self.assertListEqual(chars_bar, [char])
        self.assertListEqual(chars_b, [char])
        self.assertListEqual(chars_foo, [])
        self.assertListEqual(chars_f, [])

    @with_transaction()
    def test_search_not_like(self):
        "Test search char not like"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Bar",
                    }])

        chars_bar = Char.search([
                ('char', 'not like', "Bar"),
                ])
        chars_b = Char.search([
                ('char', 'not like', "B%"),
                ])
        chars_foo = Char.search([
                ('char', 'not like', "Foo"),
                ])
        chars_f = Char.search([
                ('char', 'not like', "F%"),
                ])

        self.assertListEqual(chars_bar, [])
        self.assertListEqual(chars_b, [])
        self.assertListEqual(chars_foo, [char])
        self.assertListEqual(chars_f, [char])

    @with_transaction()
    def test_search_not_ilike(self):
        "Test search char not like"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Bar",
                    }])

        chars_bar = Char.search([
                ('char', 'not ilike', "bar"),
                ])
        chars_b = Char.search([
                ('char', 'not ilike', "b%"),
                ])
        chars_foo = Char.search([
                ('char', 'not ilike', "foo"),
                ])
        chars_f = Char.search([
                ('char', 'not ilike', "f%"),
                ])

        self.assertListEqual(chars_bar, [])
        self.assertListEqual(chars_b, [])
        self.assertListEqual(chars_foo, [char])
        self.assertListEqual(chars_f, [char])

    @with_transaction()
    def test_write_unicode(self):
        "Test write char unicode"
        Char = self.Char()
        char, = Char.create([{
                    'char': "Foo",
                    }])

        Char.write([char], {
                'char': u"é",
                })

        self.assertEqual(char.char, u"é")


class FieldCharTestCase(unittest.TestCase, CommonTestCaseMixin):
    "Test Field Char"

    @classmethod
    def setUpClass(cls):
        activate_module('tests')

    def Char(self):
        return Pool().get('test.char')

    @with_transaction()
    def test_create_without_default(self):
        "Test create char without default"
        Char = Pool().get('test.char')

        char, = Char.create([{}])

        self.assertEqual(char.char, None)

    @with_transaction()
    def test_create_with_default(self):
        "Test create char without default"
        Char = Pool().get('test.char_default')

        char, = Char.create([{}])

        self.assertEqual(char.char, "Test")

    @with_transaction()
    def test_create_required_with_value(self):
        "Test create char required with value"
        Char = Pool().get('test.char_required')

        char, = Char.create([{
                    'char': "Test",
                    }])

        self.assertEqual(char.char, "Test")

    @with_transaction()
    def test_create_required_without_value(self):
        "Test create char required without value"
        Char = Pool().get('test.char_required')

        with self.assertRaises(UserError):
            Char.create([{}])

    @with_transaction()
    def test_create_required_with_empty(self):
        "Test create char required with empty"
        Char = Pool().get('test.char_required')

        with self.assertRaises(UserError):
            Char.create([{
                        'char': '',
                        }])

    @with_transaction()
    def test_create_size_valid(self):
        "Test create char with size"
        Char = Pool().get('test.char_size')

        char, = Char.create([{
                    'char': "Test",
                    }])

        self.assertEqual(char.char, "Test")

    @with_transaction()
    def test_create_size_invalid(self):
        "Test create char with invalid size"
        Char = Pool().get('test.char_size')

        # XXX: should be UserError but postgresql raises DataError
        with self.assertRaises(Exception):
            Char.create([{
                        'char': "foobar",
                        }])

    @with_transaction()
    def test_write(self):
        "Test write char"
        Char = Pool().get('test.char')
        char, = Char.create([{
                    'char': "Foo",
                    }])

        Char.write([char], {
                'char': "Bar",
                })

        self.assertEqual(char.char, "Bar")

    @with_transaction()
    def test_write_none(self):
        "Test write char None"
        Char = Pool().get('test.char')
        char, = Char.create([{
                    'char': "Foo",
                    }])

        Char.write([char], {
                'char': None,
                })

        self.assertEqual(char.char, None)

    @with_transaction()
    def test_write_size_invalid(self):
        "Test write char with invalid size"
        Char = Pool().get('test.char_size')

        char, = Char.create([{
                    'char': "Test",
                    }])

        # XXX: should be UserError but postgresql raises DataError
        with self.assertRaises(Exception):
            Char.write([char], {
                    'char': 'foobar',
                    })


class FieldCharTranslatedTestCase(unittest.TestCase, CommonTestCaseMixin):
    "Test Field Char Translated"

    @classmethod
    def setUpClass(cls):
        activate_module('tests')

    def Char(self):
        return Pool().get('test.char_translate')


@unittest.skipUnless(backend.name() == 'postgresql',
    "unaccent works only on postgresql")
class FieldCharUnaccentedTestCase(unittest.TestCase):
    "Test Field Char with unaccented searches"

    @classmethod
    def setUpClass(cls):
        super(FieldCharUnaccentedTestCase, cls).setUpClass()
        activate_module('tests')
        cls._activate_extension()

    @classmethod
    def tearDownClass(cls):
        super(FieldCharUnaccentedTestCase, cls).tearDownClass()
        cls._deactivate_extension()

    @classmethod
    @with_transaction()
    def _activate_extension(cls):
        connection = Transaction().connection
        cursor = connection.cursor()
        cursor.execute('CREATE EXTENSION "unaccent"')
        connection.commit()
        cls._clear_unaccent_cache()

    @classmethod
    @with_transaction()
    def _deactivate_extension(cls):
        connection = Transaction().connection
        cursor = connection.cursor()
        cursor.execute('DROP EXTENSION "unaccent"')
        connection.commit()
        cls._clear_unaccent_cache()

    @classmethod
    def _clear_unaccent_cache(cls):
        Database = backend.get('Database')
        Database._has_unaccent.clear()

    @with_transaction()
    def test_normal_search(self):
        "Test searches without the unaccented feature"
        Char = Pool().get('test.char_unaccented_off')
        char, = Char.create([{
                    'char': u'Stéphanie',
                    }])

        chars_stephanie = Char.search([
                ('char', 'ilike', 'Stephanie'),
                ])

        self.assertListEqual(chars_stephanie, [])

    @with_transaction()
    def test_accented_search(self):
        "Test searches of accented value"
        Char = Pool().get('test.char_unaccented_on')
        char, = Char.create([{
                    'char': u'Stéphanie',
                    }])

        chars_stephanie = Char.search([
                ('char', 'ilike', 'Stephanie'),
                ])

        self.assertListEqual(chars_stephanie, [char])

    @with_transaction()
    def test_unaccented_search(self):
        "Test searches of unaccented value"
        Char = Pool().get('test.char_unaccented_on')
        char, = Char.create([{
                    'char': u'Stephanie',
                    }])

        chars_stephanie = Char.search([
                ('char', 'ilike', 'Stéphanie'),
                ])
        self.assertListEqual(chars_stephanie, [char])

    @with_transaction()
    def test_unaccented_translated_search(self):
        "Test unaccented translated search"
        pool = Pool()
        Char = pool.get('test.char_unaccented_translate')
        Lang = pool.get('ir.lang')

        lang, = Lang.search([
                ('translatable', '=', False),
                ('code', '!=', 'en'),
                ], limit=1)
        lang.translatable = True
        lang.save()
        char, = Char.create([{
                    'char': u'School',
                    }])

        with Transaction().set_context(lang=lang.code):
            trans_char = Char(char.id)
            trans_char.char = u'École'
            trans_char.save()

            chars_ecole = Char.search([
                    ('char', 'ilike', 'Ecole'),
                    ])
            self.assertListEqual(chars_ecole, [char])


def suite():
    suite_ = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite_.addTests(loader.loadTestsFromTestCase(FieldCharTestCase))
    suite_.addTests(loader.loadTestsFromTestCase(FieldCharTranslatedTestCase))
    suite_.addTests(loader.loadTestsFromTestCase(FieldCharUnaccentedTestCase))
    return suite_
