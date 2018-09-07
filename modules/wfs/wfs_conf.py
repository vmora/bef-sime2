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

import urllib

from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.protocols.http import get_http_url
from trytond.transaction import Transaction

__all__ = ['WfsConf']


class WfsConf(ModelSingleton, ModelSQL, ModelView):
    'WFS server'
    __name__ = 'wfs.conf'

    show_non_geo = fields.Boolean('Show non-geographic models')
    default_geo = fields.Boolean('Enable default geometry',
                                 help='This option lets Tryton gnerate default geometries on WFS'
                                      ' for records containing empty geometries (required for QGis'
                                      ' version < 2.0)')
    prefix_url = fields.Char('Url prefix', help='Prefix to be prepended to the url, for example: https://hostname/.'
                                                ' The prefix is defined automatically when this option is not set.')

    @classmethod
    def get_url(cls):
        """Return the url that answers WFS"""
        conf = cls.search([])
        if len(conf) == 0 or conf[0].prefix_url == '' or conf[0].prefix_url is None:
            url = get_http_url() + '/model/wfs/wfs/wfs'
        else:
            url = conf[0].prefix_url + urllib.quote(Transaction().cursor.database_name.encode('utf-8') + '/')
            url += '/model/wfs/wfs/wfs'
        return url
