#coding: utf-8
"""
GPLv3
"""

from trytond.pool import Pool
from .uicn import *
from .catcri import *

def register():
    Pool.register(
        presence,
        origin,
        seasonal,               
        uicn,
        UicnTaxon,
        catcri,
        cricat_pays_taxon,                            
        module='uicn', type_='model')
