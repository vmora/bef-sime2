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
Copyright (c) 2013 Laurent Defert

"""

from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pyson import Equal, Eval

__all__ = ['MapConf']


class MapConf(ModelSingleton, ModelSQL, ModelView):
    'Maps configuration'
    __name__ = 'map.conf'

    map_provider = fields.Selection([
        ('OPENSTREETMAP', 'OpenStreetMap'),
        ('OPENSTREETMAP_CUSTOM', 'OpenStreetMap - custom'),
        ('BLUE_MARBLE', 'Blue marble'),
        #('MAPQUEST_ROAD', 'Map quest road'),
        #('MAPQUEST_AERIAL', 'Map quest aerial'),
        ('MICROSOFT_ROAD', 'Microsoft road'),
        ('MICROSOFT_AERIAL', 'Microsoft aerial'),
        ('MICROSOFT_HYBRID', 'Microsoft hybrid'),
        ('YAHOO_ROAD', 'Yahoo road'),
        ('YAHOO_AERIAL', 'Yahoo aerial'),
        ('YAHOO_HYBRID', 'Yahoo hybrid'),
        #('CLOUDMADE_ORIGINAL', 'CloudMade original'),
        #('CLOUDMADE_FINELINE', 'CloudMade fine line'),
        #('CLOUDMADE_TOURIST', 'CloudMade tourist'),
        #('CLOUDMADE_FRESH',  'CloudMade fresh'),
        #('CLOUDMADE_PALEDAWN', 'CloudMade pale dawn'),
        #('CLOUDMADE_MIDNIGHTCOMMANDER', 'CloudMade midnight commander'),
    ], 'Map provider', required=True)
    osm_url = fields.Char('OSM server url', states={
        'invisible': ~Equal(Eval('map_provider', ''), 'OPENSTREETMAP_CUSTOM'),
        'required': Equal(Eval('map_provider', ''), 'OPENSTREETMAP_CUSTOM'),
    })
    img_format = fields.Selection([
        ('PNG', 'PNG'),
        ('JPG', 'JPG'),
    ], 'Images format', required=True)

    @staticmethod
    def default_osm_url():
        return 'http://tile.openstreetmap.org'

    @staticmethod
    def default_img_format():
        return 'JPG'
