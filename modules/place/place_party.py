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

Copyright (c) 2012-2013 Pascal Obstétar
Copyright (c) 2012-2013 Bio Eco Forests <contact@bioecoforests.com>

"""

from collections import OrderedDict
import os

from osgeo import osr

from trytond.model import ModelView, ModelSingleton, ModelSQL, fields
from trytond_gis import fields as geofields
from trytond.pyson import Bool, Eval, Not
from trytond.pool import PoolMeta, Pool

from trytond.modules.qgis.qgis import QGis
from trytond.modules.qgis.mapable import Mapable

from trytond.transaction import Transaction

__metaclass__ = PoolMeta


class Party(Mapable):
    __name__ = 'party.party'
    _rec_name = 'name'

    COLOR = (1, 0.1, 0.1, 1)
    BGCOLOR = (1, 0.1, 0.1, 1)

    place = fields.Many2Many(
            'place.place-party.party',
            'party',
            'place',
            'Places'
        )
    geom = geofields.MultiPoint(
            string = u'Geometry',
            readonly = False,
            select = True,
        )

    party_image = fields.Function(fields.Binary('Image'), 'get_image')
    party_map = fields.Binary('Image')

    def get_image(self, ids):
        return self._get_image('party_image.qgs', 'carte')

    def get_map(self, ids):
        return self._get_image('party_map.qgs', 'carte')

    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
        cls._buttons.update({
            'lol_edit': {},
            'generate': {},
        })

    @staticmethod
    def default_active():
        return True

    @classmethod
    @ModelView.button_action('place.report_party_edit')
    def lol_edit(cls, ids):
        pass

    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.name is None:
                continue
            cls.write([record], {'party_map': cls.get_map(record, 'map')}) 


class PartyAreaQGis(QGis):
    __name__ = 'party.party.qgis'
    TITLES = {'party.party': u'Party'}
