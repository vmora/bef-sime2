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

from trytond.model import ModelView
from trytond.pool import Pool
from trytond.rpc import RPC
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateAction, StateView, Button

import pickle
from rpy2 import robjects

from .r_tools import none2r


class DataView(ModelView):
    'Dynamic View'
    __name__ = 'rtryton.view'
    _rec_name = 'id'
    data = None

    @classmethod
    def __setup__(cls):
        super(DataView, cls).__setup__()
        cls.__rpc__.update({
            'search': RPC(),
            'read': RPC(),
        })

    @classmethod
    def read_data(cls):
        if cls.data is None:
            record = Transaction().context.get('model')
            if record:
                Data = Pool().get('rtryton.data')
                data = Data(record)
                dataframe = robjects.conversion.ri2py(pickle.loads(data.data))

                assert isinstance(dataframe, robjects.DataFrame)

                cls.data = dataframe

                for index, header in enumerate(cls.data.colnames):
                    header = header.decode('utf-8')
                    header = header.encode('ascii', errors='ignore')
                    cls.data.colnames[index] = header
        return cls.data

    @classmethod
    def fields_view_get(cls, view_id=None, view_type='form'):
        """
        Return a view definition.
        If view_id is None the first one will be used of view_type.
        The definition is a dictionary with keys:
           - model: the model name
           - arch: the xml description of the view
           - fields: a dictionary with the definition of each field in the view
        """
        fields = {}
        arch = "<tree string=\"View\">"
        data = cls.read_data()
        for header in data.colnames:
            if header in ('write_date', 'create_date'):
                continue
            fields[header] = {'loading': 'eager', 'name': header,
                              'searchable': False, 'required': False,
                              'help': '', 'states': '{}', 'readonly': False,
                              'type': 'char', 'select': False,
                              'string': header}
            arch += "<field name=\"%s\"/>" % header
        arch += "</tree>"
        return ({'type': u'tree',
                 'view_id': None,
                 'field_childs': None,
                 'model': 'rtryton.view',
                 'fields': fields,
                 'arch': arch})

    @classmethod
    def search(cls, *args, **kwargs):
        data = cls.read_data()
        if data : return list(xrange(1, data.nrow))
        return []

    @classmethod
    def read(cls, ids, fields_names=None):
        result = []
        data = cls.read_data()
        # select rows
        rows = data.rx(robjects.IntVector(ids), True)
        for row in rows.iter_row():
            attributes = {'id': int(row.rownames[0]),
                          'rec_name': row.colnames[0]}
            # copy attributes
            try:
                for header in row.colnames:
                    if header in ('id', 'rec_name', 'write_date',
                                  'create_date'):
                        continue
                    value = row.rx(header)[0]
                    if isinstance(value, robjects.vectors.FactorVector):
                        attributes[header] = value.levels[0]
                    elif isinstance(value, robjects.vectors.IntVector):
                        attributes[header] = value[0]
                    else:
                        raise NotImplementedError()

                    #if attributes[header] in none2r.values():
                    #    attributes[header] = None

                result.append(attributes)
            except Exception, err:
                print err
        return result
