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
from datetime import date
import os

from osgeo import osr

from trytond.model import ModelView, ModelSingleton, ModelSQL, fields
from trytond.pyson import Bool, Eval, Not
from trytond.pool import PoolMeta, Pool

from trytond.modules.qgis.qgis import QGis
from trytond.modules.qgis.mapable import Mapable

STATES = {
    'readonly': ~Eval('active', True),
}

DEPENDS = ['active']

class Place(Mapable, ModelView, ModelSQL):
    "Place"
    __name__ = 'place.place'
    _rec_name = 'name'
    
    COLOR = (1, 0.1, 0.1, 1)
    BGCOLOR = (1, 0.1, 0.1, 1)
    
    active = fields.Boolean('Active')
       
    code = fields.Char(
            string = u'Site ID',
            help = u'Site Identifiant',
            required = False,
            states=STATES,
            depends=DEPENDS,
        )

    name = fields.Char(
            string = u'Site name',
            help = u'Short label of site',
            required = False,
            states=STATES,
            depends=DEPENDS,
        )
        
    lib_long = fields.Char(
            string = u'Site label',
            help = u'Long label of site',
            required = False,
            states=STATES,
            depends=DEPENDS,
        )
        
    address = fields.Many2One(
            'party.address',
            'Address',
            states=STATES,
            depends=DEPENDS,
        )
        
    html = fields.Char(
            string = u'HTML',
            help = u'File name of HTML site',
            required = False,
            states=STATES,
            depends=DEPENDS,
        )
        
    geom = fields.MultiPolygon(
            string = u'Geometry',
            srid = 2154,
            help = u'Geometry multipolygonal',            
            states=STATES,
            depends=DEPENDS,
        )
         
    party = fields.One2Many(
            'place.place-party.party',
            'place', 
            'Party',
            )            
    place_image = fields.Function(fields.Binary('Image'), 'get_image')
    place_image_all = fields.Function(fields.Binary('Image all'), 'get_image_all')
    place_image_map = fields.Binary('Image map')

    def get_image(self, ids):
        return self._get_image('place_image.qgs', 'carte')

    def get_image_all(self, ids):
        return self._get_image('place_image_all.qgs', 'carte')

    def get_map(self, ids):
        return self._get_image('place_map.qgs', 'carte')


    @classmethod
    def __setup__(cls):
        super(Place, cls).__setup__()
        cls._buttons.update({
            'lol_edit': {},
            'generate': {},
        })
    
    @staticmethod
    def default_active():
        return True            


    @classmethod
    @ModelView.button_action('place.report_lol_edit')
    def lol_edit(cls, ids):
        pass

    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.name is None:
                continue
            cls.write([record], {'place_image_map': cls.get_map(record, 'map')}) 
            
class PlaceParty(ModelSQL, ModelView):
    'PlaceParty'
    __name__ = 'place.place-party.party'
    _table = 'place_party_rel'

    place = fields.Many2One('place.place', 'Place',
            ondelete='CASCADE', required=True, select=1)
    party = fields.Many2One('party.party', 'Partenaire', ondelete='CASCADE',
            required=True, select=1)

    @classmethod
    def __setup__(cls):
        super(PlaceParty, cls).__setup__()
        
class ObjAreaQGis(QGis):
    __name__ = 'place.place.qgis'
    TITLES = {'place.place': u'areas'}        
