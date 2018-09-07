#coding: utf-8
"""
GPLv3
"""

from trytond.pool import Pool
from taxinomie import *
from espece_type import *

def register():
    Pool.register(
        rang,
        habitat,
        statut,
        taxinomie,
        statut_pays_taxon,
        EspeceType,
        TaxonEspeceType,
        module='taxinomie', type_='model')
