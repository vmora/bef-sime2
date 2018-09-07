# -*- coding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2010 Pascal Obstetar <pascal.obstetar@gmail.com>
#
# Ce logiciel est régi par la licence [CeCILL|CeCILL-B|CeCILL-C] soumise au droit français et
# respectant les principes de diffusion des logiciels libres. Vous pouvez
# utiliser, modifier et/ou redistribuer ce programme sous les conditions
# de la licence CeCILL telle que diffusée par le CEA, le CNRS et l'INRIA
# sur le site "http://www.cecill.info".
#
# En contrepartie de l'accessibilité au code source et des droits de copie,
# de modification et de redistribution accordés par cette licence, il n'est
# offert aux utilisateurs qu'une garantie limitée.  Pour les mêmes raisons,
# seule une responsabilité restreinte pèse sur l'auteur du programme,  le
# titulaire des droits patrimoniaux et les concédants successifs.
#
# A cet égard  l'attention de l'utilisateur est attirée sur les risques
# associés au chargement,  à l'utilisation,  à la modification et/ou au
# développement et à la reproduction du logiciel par l'utilisateur étant
# donné sa spécificité de logiciel libre, qui peut le rendre complexe à
# manipuler et qui le réserve donc à des développeurs et des professionnels
# avertis possédant  des  connaissances  informatiques approfondies.  Les
# utilisateurs sont donc invités à charger  et  tester  l'adéquation  du
# logiciel à leurs besoins dans des conditions permettant d'assurer la
# sécurité de leurs systèmes et ou de leurs données et, plus généralement,
# à l'utiliser et l'exploiter dans les mêmes conditions de sécurité.
#
# Le fait que vous puissiez accéder à cet en-tête signifie que vous avez
# pris connaissance de la licence CeCILL, et que vous en avez accepté les
# termes.
#
#
##############################################################################

from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Population']

class Population(ModelSQL, ModelView):
    'Population des communes'
    __name__ = 'fr.population'
    _rec_name = 'annee'

    @classmethod
    def __setup__(cls):
        super(Population, cls).__setup__()
        cls._error_messages.update({'write_population':
                u'Vous ne pouvez pas modifier la commune d\'une population !'})

    annee = fields.Char(u'Année', help=u'Les chiffres de population '
            u'présentés correspondent à l ensemble des personnes dont la '
            u'résidence habituelle se situe sur le territoire considéré')

    total = fields.Float('Population totale', help=u'Population totale de '
            'la commune')

    pop_0014 = fields.Float(u'0 à 14 ans', help=u'Population de '
            u'0 à 14 ans de la commune')

    pop_1529 = fields.Float(u'15 à 29 ans',
            help=u'Population de 15 à 29 ans de la commune')

    pop_3044 = fields.Float(u'30 à 44 ans',
            help=u'Population de 30 à 44 ans de la commune')

    pop_4559 = fields.Float(u'45 à 59 ans', help=u'Population '
            u'de 45 à 59 ans de la commune')

    pop_6074 = fields.Float(u'60 à 74 ans',
            help=u'Population de 60 à 74 ans de la commune')

    pop_75p = fields.Float(u'75 ans et plus',
            help=u'Population de 75 ans et plus de la commune')

    com = fields.Many2One('fr.commune', ondelete='CASCADE',
            string='com', select=True)


