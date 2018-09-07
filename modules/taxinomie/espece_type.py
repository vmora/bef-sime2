#coding: utf-8

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

import logging
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['EspeceType', 'TaxonEspeceType']

class EspeceType(ModelSQL, ModelView):
    u'Espèce typologie protection'
    __name__ = 'taxinomie.espece_type'
    _rec_name = 'intitule'

    cd_protection = fields.Char(
            string = u'CD PROTECTION',
            help = u'CD PROTECTION',
        )
    article = fields.Char(
            string = u'ARTICLE',
            help = u'ARTICLE',
        )
    intitule = fields.Char(
            string = u'INTITULÉ',
            help = u'INTITULÉ',
        )
    arrete = fields.Char(
            string = u'ARRÊTÉ',
            help = u'ARRÊTÉ',
        )
    url_inpn = fields.Char(
            string = u'URL INPN',
            help = u'URL INPN',
        )
    url = fields.Char(
            string = u'URL',
            help = u'URL',
        )                            
    date_arrete = fields.Integer(
            string = u'DATE ARRÊTÉ',
            help = u'DATE ARRÊTÉ',
        )
    type = fields.Char(
            string = u'ARTICLE',
            help = u'ARTICLE',
        )
        
class TaxonEspeceType(ModelSQL):
    u'Taxon - Espèce type'
    __name__ = 'taxinomie.taxinomie-taxinomie.espece_type'
    _table = 'taxinomie_espece_type_rel'
    taxon = fields.Many2One(
            'taxinomie.taxinomie',
            string=u'Taxon',
            ondelete='CASCADE',
            required=True
        )
    espece_type = fields.Many2One(
            'taxinomie.espece_type',
            string=u'Espèce type',
            ondelete='CASCADE',
            required=True
        )               
