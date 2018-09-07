#coding: utf-8
"""
GPLv3
"""

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Bool, Eval, Not

__all__ = ['presence', 'origin', 'seasonal', 'uicn', 'UicnTaxon', 'cricat_pays_taxon']

STATES = {
    'readonly': ~Eval('active', True),
}

DEPENDS = ['active']

_STATUS = [
    ('EX', u"""ÉTEINT (EX)"""),
    ('EW', u"""ÉTEINT À L’ÉTAT SAUVAGE (EW)"""),
    ('CR', u"""EN DANGER CRITIQUE D’EXTINCTION (CR)"""),
    ('EN', u"""EN DANGER (EN)"""),
    ('VU', u"""VULNÉRABLE (VU)"""),
    ('NT', u"""QUASI MENACÉ (NT)"""),
    ('LC', u"""PRÉOCCUPATION MINEURE (LC)"""),
    ('DD', u"""DONNÉES INSUFFISANTES (DD)"""),
    ('NE', u"""NON ÉVALUÉ (NE)"""),
]

         
class presence(ModelSQL, ModelView):
    u"""Présence"""
    __name__ = 'uicn.presence'
    _rec_name = 'name'

    code = fields.Char(
            string = u"""Code de présence""",
            required = False,
            readonly = False,
        )

    name = fields.Char(
            string = u"""Libellé court du code de présence""",
            required = False,
            readonly = False,
        )
        
    lib_long = fields.Text(
            string = u"""Libellé long du code de présence""",
            required = False,
            readonly = False,
        )
        
class origin(ModelSQL, ModelView):
    u"""Origine"""
    __name__ = 'uicn.origin'
    _rec_name = 'name'

    code = fields.Char(
            string = u"""Code origine""",
            required = False,
            readonly = False,
        )

    name = fields.Char(
            string = u"""Libellé court du code origine""",
            required = False,
            readonly = False,
        )
        
    lib_long = fields.Text(
            string = u"""Libellé long du code origine""",
            required = False,
            readonly = False,
        )
        
class seasonal(ModelSQL, ModelView):
    u"""Saison"""
    __name__ = 'uicn.seasonal'
    _rec_name = 'name'

    code = fields.Char(
            string = u"""Code saison""",
            required = False,
            readonly = False,
        )

    name = fields.Char(
            string = u"""Libellé court du code saison""",
            required = False,
            readonly = False,
        )
        
    lib_long = fields.Text(
            string = u"""Libellé long du code saison""",
            required = False,
            readonly = False,
        )        

        
class uicn(ModelSQL, ModelView):
    u"""UICN"""
    __name__ = 'uicn.uicn'
    _rec_name = 'binomial'

    binomial = fields.Char(
            string = u"""Nom UICN""",
            help = u"""Nom de l'espèce retenu à l'UICN""",
            required = False,
            readonly = False,
        )
        
    id_num = fields.Char(
            string = u"""Taxon ID""",
            help = u"""Identifiant unique UICN""",
            required = False,
            readonly = False,
        )    

    taxon = fields.Many2Many('uicn.uicn-taxinomie.taxinomie',
            'uicn',
            'taxon',
            string=u"""Taxons""",
            states=STATES,
            depends=DEPENDS
        )
        
    basinid = fields.Integer(
            string = u"""ID Bassin""",            
            readonly = False,
        ) 
        
    presence = fields.Many2One(
            'uicn.presence',
            ondelete='CASCADE',
            string=u'Présence',
            help=u"""Présence""",
            readonly=False,
        )
        
    origin = fields.Many2One(
            'uicn.origin',
            ondelete='CASCADE',
            string=u"""Origine""",
            help=u"""Origine""",
            readonly=False,
        )
        
    seasonal = fields.Many2One(
            'uicn.seasonal',
            ondelete='CASCADE',
            string=u"""Saison""",
            help=u"""Saison""",
            readonly=False,
        )  
        
    compiler = fields.Char(
            string = u"""Responsable""",
            help = u"""Responsable du polygone de l'espèce""",
            required = False,
            readonly = False,
        )
        
    year = fields.Integer(
            string = u"""Année""",
            help = u"""Année de mise à jour par le responsable du polygone de l'espèce""",
            required = False,
            readonly = False,
        )              

    citation = fields.Char(
            string = u"""Citation""",
            help = u"""Citation de l'espèce""",
            required = False,
            readonly = False,
        )            

    source = fields.Char(
            string = u"""Source""",
            help = u"""Source""",
            required = False,
            readonly = False,
        )
        
    dist_comm = fields.Char(
            string = u"""Distribution""",
            help = u"""Distribution de l'espèce""",
            required = False,
            readonly = False,
        )        

    island = fields.Char(
            string = u"""Ilôt""",
            help = u"""Ilôt""",
            required = False,
            readonly = False,
        )
        
    subspecies = fields.Char(
            string = u"""Sous-espèce""",
            help = u"""Sous-espèce""",
            required = False,
            readonly = False,
        )        
 
    subpop = fields.Char(
            string = u"""Sous-population""",
            help = u"""Sous-population""",
            required = False,
            readonly = False,
        )      
        
    tax_comm = fields.Text(
            string = u"""Commentaires""",
            help = u"""Commentaires""",
            required = False,
            readonly = False,
        )         
        
    legend = fields.Char(
            string = u"""Légende""",
            help = u"""Légende de l'espèce""",
            required = False,
            readonly = False,
        )
        
    status = fields.Selection(
            _STATUS, 
            'Statuts',
            help=u"""Critères et catégories de l'espèce au niveau mondial""",
        )

    catcri = fields.One2Many('uicn.cricat_pays_uicn', 'taxon',
            string = u"""Catégorie et critères""",
            help = u"""Catégorie et critères de l'espèce""",
            required = False,
            readonly = False,
        )            

    geom = fields.MultiPolygon(string=u"""Geometry""", srid=2154,
            required=False, readonly=False)
            
    @staticmethod
    def default_active():
        return True
        
class UicnTaxon(ModelSQL):
    'Uicn - Taxon'
    __name__ = 'uicn.uicn-taxinomie.taxinomie'
    _table = 'uicn_taxon_rel'
    uicn = fields.Many2One('uicn.uicn', 'binomial', ondelete='CASCADE',
            required=True)
    taxon = fields.Many2One('taxinomie.taxinomie', 'nom_complet',
        ondelete='CASCADE', required=True)
        
class cricat_pays_taxon(ModelSQL, ModelView):
    u"""Catégorie et critères de l'espèce par pays"""
    __name__ = 'uicn.cricat_pays_uicn'
    _rec_name = 'pays'


    pays = fields.Many2One('country.country', ondelete='CASCADE',
            string = u"""pays""",
            required = False,
            readonly = False,
        )

    division = fields.Many2One('country.subdivision', ondelete='CASCADE',
            string = u"""division""",
            required = False,
            readonly = False,
        )

    catcri = fields.Many2One('uicn.catcri', ondelete='CASCADE',
            string = u"""catégorie""",
            required = False,
            readonly = False,
        )

    taxon = fields.Many2One('taxinomie.taxinomie', ondelete='CASCADE',
            string = u"""taxon""",
            required = False,
            readonly = False,
        )              
