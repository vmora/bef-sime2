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

from trytond.modules.geotools.tools import bbox_aspect
from trytond.modules.qgis.qgis import QGis
from trytond.modules.qgis.mapable import Mapable
from trytond.pyson import Bool, Eval, Not, Or, And, Equal, In, If, Id
from trytond.wizard import Wizard
from trytond.pool import  Pool
from trytond.transaction import Transaction

__all__ = ['Canton', 'CantonQGis', 'GenerateCa']
 

class Canton(Mapable, ModelSQL, ModelView):
    u'Canton Français'
    __name__ = 'fr.canton'
    _rec_name ='code'
    
    region = fields.Many2One(
            'fr.region',
            string=u'Région',
            help=u'région',
        )    
    departement = fields.Many2One(
            'fr.departement',
            string=u'Département',
            help=u'Département',
        )
    commune = fields.Many2One(
            'fr.commune',
            string=u'Commune',
            help=u'Bureau central',
        )
    name = fields.Function(
            fields.Char(
                'Name',
                readonly=True),
            'get_name'
        )
        
    def get_name(self, ids):
        u'Displayed name in the form: name (canton code)'
        return '%s (%s)' % (self.nom, self.code)            
        
    @classmethod
    def search_rec_name(cls, name, clause):
        cantons = cls.search([('code',) + clause[1:]], order=[])
        if cantons:
            return [('id', 'in', [canton.id for canton in cantons])]
        return [('nom',) + clause[1:]]
                
    nom = fields.Char(
            string=u'Canton',
            help=u'Canton',
            required=True,
            select=True
        )                
    code = fields.Char(
            string=u'Code canton',
            help=u'Code du canton',
            select=True
        )
    version = fields.Date(
            string=u'Date de version',
            help=u'Date de version',
        )
    geom = fields.MultiPolygon(
            string=u'Géométrie',
            srid=2154,
            select=True
        )
    canton_image = fields.Function(
             fields.Binary(
                    'Image'
                ),
            'get_image'
        )
    canton_map = fields.Binary(
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

    def get_image(self, ids):
        return self._get_image('canton_image.qgs', 'carte')

    def get_map(self, ids):
        return self._get_image('canton_map.qgs', 'carte')   

    @classmethod
    def __setup__(cls):
        super(Canton, cls).__setup__()
        cls._buttons.update({           
            'canton_edit': {},
            'generate': {},
        })
               
    @classmethod
    @ModelView.button_action('fr.report_canton_edit')
    def canton_edit(cls, ids):
        pass
        
    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.nom is None:
                continue                                              
            cls.write([record], {'canton_map': cls.get_map(record, 'map')})

class CantonQGis(QGis):
    __name__ = 'fr.canton.qgis'
    TITLES = {'fr.canton': u'Canton'}

class GenerateCa(Wizard):
    __name__ = 'fr.canton_generate'

    @classmethod
    def execute(cls, session, data, state_name):
        canton = Pool().get('fr.canton')
        cantons = canton.browse(Transaction().context.get('active_ids'))        
        for record in cantons:
            record.generate([record])
        return []

