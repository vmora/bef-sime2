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

Copyright (c) 2012-2013 Bio Eco Forests <contact@bioecoforests.com>
Copyright (c) 2012-2013 Pascal Obstetar
Copyright (c) 2012-2013 Pierre-Louis Bonicoli

Référentiel des statuts de protection en France.
"""

from trytond.transaction import Transaction

from collections import OrderedDict
from datetime import date
import os

from osgeo import osr

from trytond.model import ModelView, ModelSingleton, ModelSQL, fields
from trytond_gis import fields as geofields
from trytond.wizard import Wizard, StateView, StateAction, Button, StateTransition
from trytond.pyson import Bool, Eval, Not
from trytond.pool import PoolMeta, Pool

from trytond.modules.qgis.qgis import QGis
from trytond.modules.qgis.mapable import Mapable


class Type(ModelSQL, ModelView):
    u'Type of protected area'
    __name__ = 'protection.type'

    @classmethod
    def __setup__(cls):
        super(Type, cls).__setup__()
        err = u'A type of protected area with the same name already exists.'
        cls._sql_constraints = [('name_uniq', 'UNIQUE(name)', err)]

    name = fields.Char(
            string=u'Space name',
            required=True
        )

    code = fields.Char(
            string=u'Space code',
            required=True
        )

class Area(Mapable, ModelSQL, ModelView):
    u'Protected area'
    __name__ = 'protection.area'

    id_mnhn = fields.Char(
            string=u'ID national',
            help=u'National identifiant',
            required=True
        )

    name = fields.Char(
            string=u'Site name',
            help=u'Site name',
            required=True
        )

    date = fields.Date(
            string=u'Date'
        )
    version = fields.Date(
            string=u'Date de version',
        )

    geom = geofields.MultiPolygon(
            string=u'Geometry',
            select=True
        )
    boundingBoxX1 = fields.Float(
            string=u'Bounding box x1'
        )
    boundingBoxY1 = fields.Float(
            string=u'Bounding box y1'
        )
    boundingBoxX2 = fields.Float(
            string=u'Bounding box x2'
        )
    boundingBoxY2 = fields.Float(
            string=u'Bounding box y2'
        )
    

    typo = fields.Char(
            string=u'Area type',
            required=True
        )

    espace = fields.Many2One(
            'protection.type',
            ondelete='RESTRICT',
            string=u'Type of protected area',
            required=True,
            select=True
        )

    url = fields.Function(
            fields.Char(
                string=u"URL",
                readonly=True,
                depends=['typo', 'id_mnhn'],
            ),
            '_get_url',
        )

    def _get_url(self, ids):
        base = "http://inpn.mnhn.fr/"
        domain = ""
        if self.typo == u"Espaces Protégés":
            domain = "espace/protege/"
        elif self.typo == "Natura 2000":
            domain = "site/natura2000/"
        elif self.typo == "Inventaires d'Espaces Naturels":
            domain = "zone/znieff/"
        return "%s%s%s"%(base, domain, self.id_mnhn)

    @classmethod
    def default_espace(cls):
        espace = Transaction().context.get('espace')
        model = Pool().get('protection.type')
        ids = model.search([('name', '=', espace)], limit=1)
        return ids[0]

    area_image = fields.Function(
                    fields.Binary(
                            string=u'Image',
                            help=u'Image'
                        ),
            'get_image'
        )
    area_map = fields.Binary(
            string=u'Map',
            help=u'Map'
        )

    def get_image(self, ids):
        return self._get_image('area_image.qgs', 'carte')

    def get_map(self, ids):
        return self._get_image('area_map.qgs', 'carte')                        
    
    COLOR = (1, 0.1, 0.1, 1)
    BGCOLOR = (1, 0.1, 0.1, 0.1)

    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.name is None:
                continue
            cls.write([record], {'area_map': cls.get_map(record, 'map')})    
    
    @classmethod
    def __setup__(cls):
        super(Area, cls).__setup__()
        cls._buttons.update({           
            'area_edit': {},
            'generate': {},
        })
               
    @classmethod
    @ModelView.button_action('protection.report_area_edit')
    def area_edit(cls, ids):
        pass


class AreaQGis(QGis):
    __name__ = 'protection.area.qgis'
    TITLES = {'protection.area': u'Area'}


TYPES = [('D', u'Directed'), ('I', u'Integral')]

class ReserveBiologique(Mapable, ModelSQL, ModelView):
    u'Biological reserve'
    __name__ = 'protection.reserve_biologique'

    id_mnhn = fields.Char(
            string=u'ID national',
            help=u'National identifiant',
            required=True
        )

    name = fields.Char(
            string=u'Site name',
            help=u'Site name',
            required=True
        )

    date = fields.Date(
            string=u'Date'
        )
    version = fields.Date(
            string=u'Date de version',
        )

    mixte = fields.Boolean(
            string=u'Mixte',
            help=u'Mixte',
        )

    geom = geofields.MultiPolygon(
            string=u'Geometry',
            select=True
        )
    boundingBoxX1 = fields.Float(
            string=u'Bounding box x1'
        )
    boundingBoxY1 = fields.Float(
            string=u'Bounding box y1'
        )
    boundingBoxX2 = fields.Float(
            string=u'Bounding box x2'
        )
    boundingBoxY2 = fields.Float(
            string=u'Bounding box y2'
        )

    type = fields.Selection(
            TYPES,
            string=u'Type',
            required=True,
            sort=False
        )

    espace = fields.Many2One(
            'protection.type',
            ondelete='RESTRICT',
            string=u'Type of protected area',
            required=True,
            select=True
        )

    url = fields.Function(
            fields.Char(
                string=u"URL",
                readonly=True,
                depends=['typo', 'id_mnhn'],
            ),
            '_get_url',
        )

    def _get_url(self, ids):
        base = "http://inpn.mnhn.fr/espace/protege/"
        return "%s%s"%(base, self.id_mnhn)

    @staticmethod
    def default_type():
        return 'D'

    rb_image = fields.Function(
                fields.Binary(
                        string=u'Image',
                        help=u'Image'
                    ),
            'get_image'
        )
    rb_map = fields.Binary(
            string=u'Map',
            help=u'Map'
        )

    def get_image(self, ids):
        return self._get_image('rb_image.qgs', 'carte')

    def get_map(self, ids):
        return self._get_image('rb_map.qgs', 'carte')                        
    
    COLOR = (1, 0.1, 0.1, 1)
    BGCOLOR = (1, 0.1, 0.1, 0.1)

    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.name is None:
                continue
            cls.write([record], {'rb_map': cls.get_map(record, 'map')})  

    @classmethod
    def __setup__(cls):
        super(ReserveBiologique, cls).__setup__()
        cls._buttons.update({           
            'reserve_biologique_edit': {},
            'generate': {},
        })
               
    @classmethod
    @ModelView.button_action('protection.report_rb_edit')
    def reserve_biologique_edit(cls, ids):
        pass


class ReserveBiologiqueQGis(QGis):
    __name__ = 'protection.reserve.biologique.qgis'
    TITLES = {'protection.reserve_biologique': u'Reserve biologique'}


class Zico(Mapable, ModelSQL, ModelView):
    u'ZICO area'
    __name__ = 'protection.zico'

    id_diren = fields.Char(
            string=u'ID diren',
            help=u'National identifiant',
            required=True
        )
    id_iba = fields.Char(
            string=u'ID iba',
            help=u'National identifiant',
            required=True
        )
    id_spn = fields.Char(
            string=u'ID spn',
            help=u'National identifiant',
            required=True
        )

    version = fields.Date(
            string=u'Date de version',
        )
    
    name = fields.Char(
            string=u'Site name',
            help=u'Site name',
            required=True
        )

    espace = fields.Many2One(
            'protection.type',
            ondelete='RESTRICT',
            string=u'Type of protected area',
            required=True,
            select=True
        )

    geom = geofields.MultiPolygon(
            string=u'Geometry',
            select=True
        )
    boundingBoxX1 = fields.Float(
            string=u'Bounding box x1'
        )
    boundingBoxY1 = fields.Float(
            string=u'Bounding box y1'
        )
    boundingBoxX2 = fields.Float(
            string=u'Bounding box x2'
        )
    boundingBoxY2 = fields.Float(
            string=u'Bounding box y2'
        )

    zico_image = fields.Function(
            fields.Binary(
                    string=u'Image',
                    help=u'Image'
                ),
            'get_image'
        )
    zico_map = fields.Binary(
            string=u'Map',
            help=u'Map'
        )

    def get_image(self, ids):
        return self._get_image('zico_image.qgs', 'carte')

    def get_map(self, ids):
        return self._get_image('zico_map.qgs', 'carte')                          
    
    COLOR = (1, 0.1, 0.1, 1)
    BGCOLOR = (1, 0.1, 0.1, 0.1)

    @classmethod
    @ModelView.button
    def generate(cls, records):
        for record in records:
            if record.name is None:
                continue
            cls.write([record],  {'zico_map': cls.get_map(record, 'map')})  

    @classmethod
    def __setup__(cls):
        super(Zico, cls).__setup__()
        cls._buttons.update({           
            'zico_edit': {},
            'generate': {},
        })
               
    @classmethod
    @ModelView.button_action('protection.report_zico_edit')
    def zico_edit(cls, ids):
        pass


class ZicoQGis(QGis):
    __name__ = 'protection.zico.qgis'
    TITLES = {'protection.zico': u'ZICO'}

class GenerateAll(Wizard):
    __name__ = 'protection.generateall'

    @classmethod
    def execute(cls, session, data, state_name):
        model = Pool().get('protection.area')
        records = model.browse(Transaction().context.get('active_ids'))
        for record in records:
            record.generate([record])
        return []
