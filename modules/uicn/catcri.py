#coding: utf-8
"""
GPLv3
"""

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Bool, Eval, Not

__all__ = ['catcri']

STATES = {
    'readonly': ~Eval('active', True),
}

DEPENDS = ['active']

SEPARATOR = ' / '


class catcri(ModelSQL, ModelView):
    u"""Catégories et Critères de l'UICN pour la Liste Rouge"""
    __name__ = 'uicn.catcri'
    _rec_name = 'code'

    code = fields.Char(
            string = u"""Code""",
            help = u"""Code CORINE Biotopes, à 1 ou 2 chiffres suivis au maximum de 6 décimales.""",
            required = True,
            readonly = False,
        )

    name = fields.Char(
            string = u"""Intitulé""",
            help = u"""Intitulé de l'habitat selon la version en français de 1997 ou traduction nouvelle dans le cas de codes non retenus dans cette version mais présents en France.""",
            required = False,
            readonly = False,
        )

    description = fields.Text(
            string = u"""Description""",
            help = u"""Descriptif de l'habitat selon la version en français de 1997 ou traduction nouvelle dans le cas de codes non retenus dans cette version mais présents en France.""",
            required = False,
            readonly = False,
        )    

    parent = fields.Many2One('uicn.catcri', 'Parent',
        states=STATES, depends=DEPENDS)
    childs = fields.One2Many('uicn.catcri', 'parent',
       'Children', states=STATES, depends=DEPENDS)
    active = fields.Boolean('Active')

    @classmethod     
    def __setup__(cls):
        super(catcri, cls).__setup__()
        cls._sql_constraints = [
            ('name_parent_uniq', 'UNIQUE(code, parent)',
                'The label of a code catcri must be unique by parent!'),
        ]
        cls._constraints += [
            ('check_recursion', 'recursive_codes'),
            ('check_name', 'wrong_name'),
        ]
        cls._error_messages.update({
            'recursive_codes': 'You can not create recursive code!',
            'wrong_name': 'You can not use "%s" in name field!' % SEPARATOR,
        })
        cls._order.insert(1, ('code', 'ASC'))

    @staticmethod
    def default_active():
        return True

    def check_name(self):
        if SEPARATOR in self.name:
            return False
        return True

    def get_rec_name(self, name):
        if self.parent:
            return self.parent.get_rec_name(name) + SEPARATOR + self.name
        return self.name

    @classmethod
    def search_rec_name(cls, name, clause):
        if isinstance(clause[2], basestring):
            values = clause[2].split(SEPARATOR)
            values.reverse()
            domain = []
            field = 'code'
            for name in values:
                domain.append((field, clause[1], name))
                field = 'parent.' + field
            ids = cls.search(domain, order=[])
            return [('id', 'in', ids)]
        #TODO Handle list
        return [('code',) + tuple(clause[1:])] 
