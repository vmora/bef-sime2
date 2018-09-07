#coding: utf-8
"""
GPLv3
"""

from trytond.pool import Pool
from rapport_environnemental import *

def register():
    Pool.register(
        configuration,    
        surface_statut_buffer,
        Opensurface_statut_bufferStart,        
        TaxonUicnPlace,
        OpenTaxonUicnPlaceStart,
        line_place_area,
        Openline_place_areaStart,
        module='rapport_environnemental', type_='model')
    Pool.register(        
        Opensurface_statut_buffer,
        OpenTaxonUicnPlace,
        GenerateAreaMap,
        Openline_place_area,
        module='rapport_environnemental', type_='wizard')
    Pool.register(
        line_place_areaQGis,
        module='rapport_environnemental', type_='report')
