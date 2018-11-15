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

__all__ = ['Departement', 'DepartementQGis', 'GenerateD']
 

class Departement(Mapable, ModelSQL, ModelView):
    u'Département Française'
    __name__ = 'fr.departement'
    _rec_name ='nom'
    
    region = fields.Many2One(
            'fr.region',
            string=u'Région',
            help=u'région',
        )

    name = fields.Function(
            fields.Char(
                'Name',
                readonly=True),
            'get_name'
        )
        
    def get_name(self, ids):
        u'Displayed name in the form: name (departement code)'
        return '%s (%s)' % (self.nom, self.code)
        
    def get_rec_name(self, ids):
        u'Displayed name in the form: name (departement code)'
        return '%s (%s)' % (self.nom, self.code)

    @classmethod
    def search_rec_name(cls, name, clause):
        departements = cls.search([('code',) + clause[1:]], order=[])
        if departements:
            return [('id', 'in', [departement.id for departement in departements])]
        return [('nom',) + clause[1:]]
                        
    nom = fields.Char(
            string=u'Département',
            help=u'Département français',
            required=True,
            select=True
        )                
    code = fields.Char(
            string=u'Code département',
            help=u'Code de la département',
            select=True
        )
    version = fields.Date(
            string=u'Date de version',
            help=u'Date de version',
        )
    geom = geofields.MultiPolygon(
            string=u'Géométrie'
        )
    departement_image = fields.Function(
             fields.Binary(
                    'Image'
                ),
            'get_image'
        )
    departement_map = fields.Binary(
            string=u'Carte',
            help=u'Départements'
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
        return self._get_image('departement_image.qgs', 'carte')

    def get_map(self):
        return self._get_image('departement_map.qgs', 'carte')   

    @classmethod
    def __setup__(cls):
        super(Departement, cls).__setup__()
        cls._buttons.update({           
            'departement_edit': {},
            'generate': {},
        })
               
    @classmethod
    @ModelView.button_action('fr.report_departement_edit')
    def departement_edit(cls, ids):
        pass
        
    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.nom is None:
                continue                                              
            cls.write([record], {'departement_map': cls.get_map(record)})

class DepartementQGis(QGis):
    __name__ = 'fr.departement.qgis'
    TITLES = {'fr.departement': u'Département'}

class GenerateD(Wizard):
    __name__ = 'fr.departement_generate'

    @classmethod
    def execute(cls, session, data, state_name):
        departement = Pool().get('fr.departement')
        departements = departement.browse(Transaction().context.get('active_ids'))        
        for record in departements:
            record.generate([record])
        return []

