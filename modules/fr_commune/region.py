# -*- coding: utf-8 -*-

##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (c) 2012-2013 Bio Eco Forests <contact@bioecoforests.com>
# Copyright (c) 2012-2013 Pascal Obstetar
#
#
##############################################################################

from trytond.model import ModelView, ModelSQL, fields
from trytond_gis import fields as geofields

from trytond.modules.geotools.tools import bbox_aspect
from trytond.modules.qgis.qgis import QGis
from trytond.modules.qgis.mapable import Mapable
from trytond.pyson import Bool, Eval, Not, Or, And, Equal, In, If, Id
from trytond.wizard import Wizard
from trytond.pool import  Pool
from trytond.transaction import Transaction

__all__ = ['Region', 'RegionQGis', 'GenerateR']
 

class Region(Mapable, ModelSQL, ModelView):
    u'Région Française'
    __name__ = 'fr.region'
    _rec_name ='nom'

    name = fields.Function(
            fields.Char(
                'Name',
                readonly=True),
            'get_name'
        )
    
    def get_name(self, ids):
        u'Displayed name in the form: name (region code)'
        return '%s (%s)' % (self.nom, self.code)    
        
    def get_rec_name(self, ids):
        u'Displayed name in the form: name (region code)'
        return '%s (%s)' % (self.nom, self.code)
        
    @classmethod
    def search_rec_name(cls, name, clause):
        regions = cls.search([('code',) + clause[1:]], order=[])
        if regions:
            return [('id', 'in', [region.id for region in regions])]
        return [('nom',) + clause[1:]]
                
    nom = fields.Char(
            string=u'Région',
            help=u'Région française',
            required=True,
            select=True
        )                
    code = fields.Char(
            string=u'Code région',
            help=u'Code de la région',
            select=True
        )
    version = fields.Date(
            string=u'Date de version',
            help=u'Date de version',
        )
    geom = geofields.MultiPolygon(
            string=u'Géométrie'
        )
    region_image = fields.Function(
             fields.Binary(
                    'Image'
                ),
            'get_image'
        )
    region_map = fields.Binary(
            string=u'Carte',
            help=u'Régions'
        )
    active = fields.Boolean(
            'Active'
        )
        
    @staticmethod
    def default_active():
        return True
            
    COLOR = (1, 0.1, 0.1, 1)
    BGCOLOR = (1, 0.1, 0.1, 0.4)

    def get_image(self):
        return self._get_image('region_image.qgs', 'carte')

    def get_map(self):
        print("get_map",self.id)
        return self._get_image('region_map.qgs', 'carte')   

    @classmethod
    def __setup__(cls):
        super(Region, cls).__setup__()
        cls._buttons.update({
            'region_edit': {},
            'generate': {},
        })
               
    @classmethod
    @ModelView.button_action('fr.report_region_edit')
    def region_edit(cls, ids):
        pass
        
    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.nom is None:
                continue
            cls.write([record], {'region_map': cls.get_map(record)})

class RegionQGis(QGis):
    __name__ = 'fr.region.qgis'
    TITLES = {'fr.region': u'Région'}

class GenerateR(Wizard):
    __name__ = 'fr.region_generate'

    @classmethod
    def execute(cls, session, data, state_name):
        print("################### GENERATE")
        region = Pool().get('fr.region')
        regions = region.browse(Transaction().context.get('active_ids'))        
        for record in regions:
            record.generate([record])
        return []

