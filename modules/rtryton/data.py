#coding: utf-8
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Copyright (c) 2013 Bio Eco Forests <contact@bioecoforests.com>
Copyright (c) 2013 Pierre-Louis Bonicoli
"""

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction

from collections import namedtuple
from rpy2 import robjects
from rpy2.rinterface import RRuntimeError
import pickle

from r_tools import dataframe

FieldInfo = namedtuple('FieldInfo', ['name', 'ttype'])


class Data(ModelView, ModelSQL):
    'a data source'
    __name__ = 'rtryton.data'

    model = fields.One2One('rtryton.datasourcemodel', 'data', 'model',
                           states={'readonly': Bool(Eval('script'))},
                           string='Model')
    script = fields.One2One('rtryton.datasourcescript', 'data', 'script',
                            states={'readonly': Bool(Eval('model'))},
                            string='Script', depends=['model'])
    data = fields.Binary('DataFrame', readonly=True)
    names = fields.Function(fields.Char('Names',
                            help='List of generated data'), 'get_names')

    menu = fields.Many2One('ir.action.act_window', 'Menu', ondelete='CASCADE')

    @classmethod
    def __register__(cls, module_name):
        cursor = Transaction().cursor
        sql ="""CREATE OR REPLACE FUNCTION sort_menu(parent_menu integer) RETURNS void AS $$
            DECLARE
                r record;
                i integer := 1;
            BEGIN
                FOR r IN SELECT id, sequence from ir_ui_menu where parent=parent_menu order by name
                LOOP
                    UPDATE ir_ui_menu sequence SET (sequence) = (i) WHERE id=r.id;
                    i := i + 1;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql"""

        cursor.execute(sql)
        super(Data, cls).__register__(module_name)

    @classmethod
    def __setup__(cls):
        super(Data, cls).__setup__()
        err_msgs = {
            'model_or_script': 'model or script required',
            'r_error': 'Execution of the R script failed:\n\n %s',
        }
        cls._error_messages.update(err_msgs)

    @classmethod
    def create(cls, vlist):
        data = super(Data, cls).create(vlist)
        print "create:", data, vlist
        pool = Pool()
        Menu = pool.get('ir.ui.menu')
        ActWindow = pool.get('ir.action.act_window')
        data_menu = cls.get_parent_menu(pool)
        parent_menu = Menu(data_menu[0].db_id)

        for record in data:
            record.create_dataframe()

            if data_menu:
                action = ActWindow.create([{
                    'name': record.rec_name,
                    'res_model': 'rtryton.view',
                    'context': "{'model': %s }" % record.id,
                }])[0]
                menu = Menu.create([{
                    'name': record.rec_name,
                    'parent': parent_menu,
                    'icon': 'tryton-list',
                    'action': 'ir.action.act_window,%s' % action.id
                }])[0]
                record.menu = menu.id

        cls.reorder_menus(Menu, parent_menu)

        return data

    @classmethod
    def delete(cls, records):

        pool = Pool()
        ActWindow = pool.get('ir.action.act_window')
        filters = [('res_model', '=', 'rtryton.view')]
        for record in records:
            filters.append(['OR',[
                ('name', '=', record.rec_name),
                ('context', '=', "{'model': %s }" % record.id)
                ]
            ])
        actions = ActWindow.search(filters)
        if actions:
            ActWindow.delete(actions)

        data_menu = cls.get_parent_menu(pool)
        if data_menu:
            Menu = pool.get('ir.ui.menu')
            parent_menu = data_menu[0].db_id
            filters = [('icon', '=', 'tryton-list'), ('parent', '=', parent_menu)]
            subfilters = ['OR',]
            for record in records:
                subfilters.append([('name', '=', record.rec_name)])
            filters.append(subfilters)

        menus = Menu.search(filters)
        if menus:
            Menu.delete(menus)

        super(Data, cls).delete(records)

    @staticmethod
    def get_parent_menu(pool):
        ModelData = pool.get('ir.model.data')
        return ModelData.search([
            ('fs_id', '=', 'menu_rtryton_view'),
            ('model', '=', 'ir.ui.menu'),
            ('module', '=', 'rtryton')
        ], limit=1)

    @staticmethod
    def reorder_menus(Menu, parent):
        Transaction().cursor.execute("SELECT sort_menu(%s)", (parent.id,))

    @classmethod
    def validate(cls, data):
        super(Data, cls).validate(data)
        for obj in data:
            if obj.model is None and obj.script is None:
                obj.raise_user_error('model_or_script')

        return True

    def create_dataframe(self):
        """create & save a R dataframe in dataframe field"""
        if self.model is not None:
            ModelField = Pool().get('ir.model.field')
            model_fields = ModelField.search([('model', '=', self.model)])
            model = Pool().get(self.model.model)
            records = model.search([])
            fields_info = [FieldInfo(field.name, field.ttype)
                           for field in model_fields]
            df = dataframe(records, fields_info)
            self.data = buffer(pickle.dumps(df))
            self.save()
        elif self.script is not None:
            # clean R workspace
            # robjects.r['source'] could be used instead of robjects.r
            robjects.r("""rm(list = ls(all.names=TRUE))""")
            try:
                # run code uploaded by users
                try:
                    robjects.r(self.script.code)
                except RRuntimeError, err:
                    self.raise_user_error('r_error', (err,))
                globalenv = robjects.r["globalenv"]()
                try:
                    obj = globalenv['out']
                except LookupError:
                    obj = None
                if isinstance(obj, robjects.DataFrame):
                    self.data = buffer(pickle.dumps(obj))
                else:
                    self.data = None
            finally:
                robjects.r("""rm(list = ls(all.names=TRUE))""")
        else:
            raise NotImplementedError()

    def get_names(self, name):
        if self.model is None:
            return ""
        else:
            return self.model.model


class Script(ModelView, ModelSQL):
    'a R script'
    __name__ = 'rtryton.script'

    inputs = fields.Many2One('rtryton.data', 'Data')
    # TODO use a binary field
    code = fields.Text('Script')
    colnames = fields.Char(u'Données générées', help=u'Noms des données '
                           u'à sauvegarder (séparés par des virgules)')


class DataSourceModel(ModelSQL):
    'Model used as data source'
    __name__ = 'rtryton.datasourcemodel'

    model = fields.Many2One('ir.model', 'Model')
    data = fields.Many2One('rtryton.data', 'Data', ondelete='CASCADE')
    #name = fields.Char('Identifiant')

    @classmethod
    def __setup__(cls):
        super(DataSourceModel, cls).__setup__()
        cls._sql_constraints += [
            ('model_unique', 'UNIQUE(model)',
                'Model must be unique'),
            ('data_unique', 'UNIQUE(data)',
                'Data must be unique'),
            ]


class DataSourceScript(ModelSQL):
    'Script used as data source'
    __name__ = 'rtryton.datasourcescript'

    script = fields.Many2One('rtryton.script', 'Script')
    data = fields.Many2One('rtryton.data', 'Data', ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super(DataSourceScript, cls).__setup__()
        cls._sql_constraints += [
            ('script_unique', 'UNIQUE(script)',
                'Script must be unique'),
            ('data_unique', 'UNIQUE(data)',
                'Data must be unique'),
            ]
