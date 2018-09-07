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
from trytond.pool import Pool

__all__ = ['rang', 'habitat', 'statut', 'taxinomie', 'statut_pays_taxon']

class rang(ModelSQL, ModelView):
    u'Rang'
    __name__ = 'taxinomie.rang'
    _rec_name = 'description'

    code = fields.Char(
            string = u'Code',
            help = u'Code du rang',
        )
    description = fields.Char(
            string = u'Libellé',
            help = u'Libellé du code',
        )

class habitat(ModelSQL, ModelView):
    u'Habitat'
    __name__ = 'taxinomie.habitat'
    _rec_name = 'description'

    code = fields.Integer(
            string = u'Code',
            help = u'Identifiant de l\'habitat',
        )
    description = fields.Char(
            string = u'Description',
            help = u'Description de l\'habitat',
        )
    remarques = fields.Text(
            string = u'Remarques',
            help = u'Remarques sur l\'habitat',
        )

class statut(ModelSQL, ModelView):
    u'Statut'
    __name__ = 'taxinomie.statut'
    _rec_name = 'description'

    code = fields.Char(
            string = u'Code',
        )
    description = fields.Char(
            string = u'Description',
        )
    definition = fields.Text(
            string = u'Définition',
        )

class taxinomie(ModelSQL, ModelView):
    u'Taxinomie'
    __name__ = 'taxinomie.taxinomie'
    _rec_name = 'lb_nom'

    #MNHN
    regne = fields.Char(
            string = u'Règne',
            help = u'Règne auquel le taxon appartient (champ calculé à partir du CD_TAXSUP)',
        )
    phylum = fields.Char(
            string = u'Phylum',
            help = u'Embranchement auquel le taxon appartient (champ calculé à partir du CD_TAXSUP)',
        )
    classe = fields.Char(
            string = u'Classe',
            help = u'Classe à laquelle le taxon appartient (champ calculé à partir du CD_TAXSUP)',
        )
    ordre = fields.Char(
            string = u'Ordre',
            help = u'Ordre auquel le taxon appartient (champ calculé à partir du CD_TAXSUP)',
        )
    famille = fields.Char(
            string = u'Famille',
            help = u'Famille à laquelle le taxon appartient (champ calculé à partir du CD_TAXSUP)',
        )
    group1_inpn = fields.Char(
            string = u'Groupe1',
            help = u'Groupe1 INPN',
        )
    group2_inpn = fields.Char(
            string = u'Groupe2',
            help = u'Groupe2 INPN',
        )
    cd_nom = fields.Char(
            string = u'Taxon ID',
            help = u'Identifiant unique (CD_NOM) du nom scientifique',
        )
    cd_taxsup = fields.Char(
            string = u'Taxon supérieur',
            help = u'Identifiant (CD_NOM) du taxon supérieur',
        )
    cd_ref = fields.Char(
            string = u'Taxon de référence',
            help = u'Identifiant (CD_NOM) du taxon de référence (nom retenu)',
        )
    rang = fields.Many2One(
            'taxinomie.rang',
            string = u'Rang taxonomique',
            help = u'Rang taxonomique (lien vers RANG)',
        )
    lb_nom = fields.Char(
            string = u'Nom scientifique',
            help = u'Nom scientifique du taxon (sans l’autorité)',
        )
    lb_auteur = fields.Char(
            string = u'Auteur',
            help = u'Autorité du taxon (Auteur, année, gestion des parenthèses)',
        )
    nom_complet = fields.Char(
            string = u'Nom complet',
            help = u'Combinaison des champs pour donner le nom complet (~LB_NOM+" "+LB_AUTEUR)',
        )
    nom_complet_html = fields.Char(
            string = u'Nom complet HTML',
            help = u'Combinaison des champs pour donner le nom complet (~LB_NOM+" "+LB_AUTEUR) avec balises HTML',
        )
    nom_valide = fields.Char(
            string = u'Nom valide',
            help = u'Le NOM_COMPLET du CD_REF',
        )
    nom_vern = fields.Char(
            string = u'Nom vernaculaire',
            help = u'Noms vernaculaires français',
        )
    nom_vern_eng = fields.Char(
            string = u'Nom vernaculaire anglais',
            help = u'Noms vernaculaires anglais',
        )
    habitat = fields.Many2One(
            'taxinomie.habitat',
            string = u'Habitat',
            help = u'Code de l\'habitat (lien vers HABITATS)',
        )
    statut = fields.One2Many(
            'taxinomie.statut_pays_taxon',
            'taxon',
            string = u'Statut du taxon',
            help = u'Statut biogéographique (lien vers STATUTS)',
        )
    url = fields.Char(
            string = u'URL',
            help = u'URL',
        )
    protection = fields.Many2Many(
            'taxinomie.taxinomie-taxinomie.espece_type',
            'taxon',
            'espece_type',
            string=u'Protection',
            help=u'Protection juridique des espèces',                       
        )
     

class statut_pays_taxon(ModelSQL, ModelView):
    u'Statut Taxons'
    __name__ = 'taxinomie.statut_pays_taxon'
    _rec_name = 'pays'

    pays = fields.Many2One(
            'country.country',
            string = u'Pays',
        )
    division = fields.Many2One(
            'country.subdivision',
            string = u'Division',
        )
    statut = fields.Many2One(
            'taxinomie.statut',
            string = u'Statut',
        )
    taxon = fields.Many2One(
            'taxinomie.taxinomie',
            string = u'Taxon',
        )

