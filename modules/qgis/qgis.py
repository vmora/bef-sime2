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

from collections import OrderedDict
from copy import deepcopy
import datetime
import inspect
import os
import time
from urllib import quote_plus

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from genshi.filters import Translator
from relatorio.reporting import Report as RelatorioReport, MIMETemplateLoader

from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.modules.geotools.tools import envelope_union, osr_geo_from_field
from trytond.modules.wfs.wfs import TRYTON_FIELDS
from trytond.pool import Pool
from trytond.report import Report, ReportFactory, TranslateFactory
from trytond.transaction import Transaction

__all__ = ['QGis', 'QGisConf', 'Version']


TRYTON_TO_QGIS = {
    'multipolygon': 'Polygon',
    'polygon': 'Polygon',
    'multilinestring': 'Line',
    'linestring': 'Line',
    'multipoint': 'Point',
    'point': 'Point',
}

# Qgis edition widgets code:
QGIS_WIDGET_RELATIONAL = 15
QGIS_WIDGET_HIDDEN = 11


def get_wfs_id_filter(ids):
    """Returns an ogc formatted filter from an id or a list of ids"""
    xml = '<ogc:Filter>'

    if isinstance(ids, list):
        if ids == []:
            xml += '<ogc:PropertyIsEqualTo>' \
                '<ogc:PropertyName>id</ogc:PropertyName>' \
                '<ogc:Literal>-1</ogc:Literal>' \
                '</ogc:PropertyIsEqualTo>'
        else:
            xml += '<ogc:Or>'
            for _id in ids:
                xml += '<ogc:PropertyIsEqualTo>' \
                    '<ogc:PropertyName>id</ogc:PropertyName>' \
                    '<ogc:Literal>%s</ogc:Literal>' \
                    '</ogc:PropertyIsEqualTo>' % _id
            xml += '</ogc:Or>'
    else:
        xml += '<ogc:PropertyIsEqualTo>' \
            '<ogc:PropertyName>id</ogc:PropertyName>' \
            '<ogc:Literal>%s</ogc:Literal>' \
            '</ogc:PropertyIsEqualTo>' % ids
    xml += '</ogc:Filter>'

    _filter = 'FILTER=' + quote_plus(xml)
    return _filter

class Version(ModelSQL, ModelView):
    u'Version de QGIS'
    __name__ = 'qgis.version'
    _rec_name = 'name'

    code = fields.Char(
            string = u'Version de QGIS disponible',
            required = True,
        )
    name = fields.Char(
            string = u'Libellé de la version de QGIS',
            required = True,
        ) 


class QGisConf(ModelSingleton, ModelSQL, ModelView):
    'QGis'
    __name__ = 'qgis.conf'    

    version = fields.Char(            
                string=u'Version utilisée de QGIS',
                required=True,
                on_change_with=['vv']
            )
            
    vv = fields.Many2One(
                'qgis.version',
                string=u'Version proposée de QGIS',
                required=True
            )
            
    def on_change_with_version(self):
        if self.vv is not None:            
            return str(self.vv.code)       

class QGis(Report):
    __name__ = 'qgis.qgis'
    FIELDS = None
    TITLES = {}

    @classmethod
    def _qgis_color(cls, color):
        return ','.join([str(int(c * 255)) for c in color])

    @classmethod
    def _get_aliases(cls, model_name):
        """Returns the list of column aliases: for each field the wfs column get
        the field's label as an alias"""
        Model = Pool().get(model_name)
        Translation = Pool().get('ir.translation')
        aliases = ''
        for no, field in enumerate(Model._fields):
            if field in TRYTON_TO_QGIS:
                continue
            field = getattr(Model, field)
            title_src = field.string
            if Transaction().language != 'en_US':
                name = '%s,%s' % (model_name, field.name)
                title = Translation.get_source(name, 'field', Transaction().language, title_src)
                if title is None:
                    title = title_src
            else:
                title = title_src
            aliases += '<alias field="%s" index="%i" name="%s"/>' % (field.name, no, title)
        return aliases

    @classmethod
    def _add_symbol_style(cls, symbols, geo_field):
        """Update the @symbols@ dictionnary, to set correct symbols type based
        on the @geo_field@ type."""
        if geo_field._type in ('polygon', 'multipolygon'):
            symbols.update({
                'symbols_type': 'fill',
                'symbols_class': 'SimpleFill',
            })
        elif geo_field._type in ('point', 'multipoint'):
            symbols.update({
                'symbols_type': 'marker',
                'symbols_class': 'SimpleMarker',
            })
        elif geo_field._type in ('linestring', 'multilinestring'):
            symbols.update({
                'symbols_type': 'line',
                'symbols_class': 'SimpleLine',
            })
        else:
            raise Exception('Type %s is not handled' % geo_field._type)

    @classmethod
    def get_layer(cls, records, model_name):
        """Return parameters for the model @model_name@.
        If some records of the model are not contained in @records@,
        then those record are returned in a separate layer that will is displayed
        as "Unselected" values.
        """
        # Look for a geometric field
        Field = Pool().get('ir.model.field')
        Model = Pool().get('ir.model')
        RecordModel = Pool().get(model_name)

        geo_field_name = ''
        geo_field = None
        m2o_fields = []
        for attr_name in dir(RecordModel):
            if attr_name in TRYTON_FIELDS:
                continue
            attr = getattr(RecordModel, attr_name)
            if isinstance(attr, fields.Many2One):
                m2o_fields.append(attr)
            if isinstance(attr, fields.Geometry):
                geo_field = attr
                geo_field_name = attr_name

        bbox = None
        unselected = set()
        srid = getattr(RecordModel, geo_field_name).srid

        for record in records:
            geo_value = getattr(record, geo_field_name)
            if geo_value is not None:
                geo = osr_geo_from_field(geo_value)
                bbox = envelope_union(geo.GetEnvelope(), bbox)

        # Look for unselected related records
        for m2o_field in m2o_fields:
            # Find the corresponding one2many field in the parent
            parent_model = Model.search([('model', '=', m2o_field.model_name)], limit=1)[0]
            Parent = Pool().get(m2o_field.model_name)
            o2mfield = Field.search([('ttype', '=', 'one2many'),
                                     ('model', '=', parent_model.id)])

            for o2m in o2mfield:
                parent_field = getattr(Parent, o2m.name)
                if parent_field.model_name == model_name and m2o_field.name == parent_field.field:
                    break
            else:
                continue

            for record in records:
                parent_record = getattr(record, m2o_field.name)
                for child in getattr(parent_record, parent_field.name):
                    if child in records:
                        continue
                    unselected.add(child.id)
            break

        layers = []
        layers.append({
            'model': model_name,
            'title': cls.TITLES.get(model_name, RecordModel.__doc__),
            'layerid': 'tryton_%s' % model_name.replace('.', '_'),
            'geo': True,
            'srid': srid,
            'filter': get_wfs_id_filter(sorted([record.id for record in records])),
            'color': cls._qgis_color(RecordModel.BGCOLOR),
            'color_border': cls._qgis_color(RecordModel.COLOR),
            'edittypes': {'id': {'type': QGIS_WIDGET_HIDDEN}},
            'geo_type': TRYTON_TO_QGIS[geo_field._type],
            'unfolded': 'true',
            'aliases': cls._get_aliases(model_name),
        })

        if len(unselected) != 0:
            layers.append({
                'model': model_name,
                'title': cls.TITLES.get(model_name, RecordModel.__doc__) + ' (unselected)',
                'layerid': 'tryton_unselected_%s' % model_name.replace('.', '_'),
                'geo': True,
                'srid': srid,
                'filter': get_wfs_id_filter(sorted(unselected)),
                'color': '255,255,255,0',
                'color_border': cls._qgis_color(RecordModel.BGCOLOR),
                'edittypes': {'id': {'type': QGIS_WIDGET_HIDDEN}},
                'geo_type': TRYTON_TO_QGIS[geo_field._type],
                'unfolded': 'false',
                'aliases': cls._get_aliases(model_name),
            })
        base_layers = layers

        deps_models = set()
        Record = Pool().get(model_name)
        symbols = []
        # Add dependency tables
        for m2o_field in m2o_fields:
            # Find the corresponding one2many field in the parent
            other_model_name = getattr(Record, m2o_field.name).model_name
            OtherModel = Pool().get(other_model_name)
            other_model = Model.search([('model', '=', other_model_name)], limit=1)[0]

            if OtherModel in deps_models:
                continue
            deps_models.add(OtherModel)

            layer_id = 'tryton_%s' % other_model.model.replace('.', '_')
            layers.append({
                'model': other_model.model,
                'title': cls.TITLES.get(other_model.model, other_model.name),
                'layerid': layer_id,
                'geo': False,
                'filter': None,
                'edittypes': {'id': {'type': QGIS_WIDGET_HIDDEN}},
                'unfolded': 'false',
                'aliases': cls._get_aliases(other_model.model),
            })

            for layer in base_layers:
                layer['edittypes'][m2o_field.name] = {
                    'type': QGIS_WIDGET_RELATIONAL,
                    'layer': layer_id,
                    'value': 'name',
                }

            if symbols == [] and (parent_model is None or other_model_name != parent_model.model):
                symbol_recs = Record.search([('id', 'in', list(unselected) + [record.id for record in records])])
                symbol_recs = set([getattr(symbol_rec, m2o_field.name) for symbol_rec in symbol_recs])
                symbol_recs -= set([None])

                for no, symbol in enumerate(symbol_recs):
                    color = no * 255 / len(symbol_recs)
                    symbols.append({
                        'no': no,
                        'value': symbol.id,
                        'label': symbol.rec_name,
                        'color': '%i,%i,255,255' % (color, color),
                        'color_border': '0,0,0,0',
                    })

                if geo_field._type in ('linestring', 'multilinestring'):
                    none_color = '0,0,0,255'
                else:
                    none_color = '255,255,255,255'

                symbols.append({
                    'no': len(symbol_recs),
                    'value': '',
                    'label': '(None)',
                    'color': none_color,
                    'color_border': '0,0,0,255',
                })

                base_layers[0].update({
                    'symbols': symbols,
                    'symbols_attr': m2o_field.name,
                })

                cls._add_symbol_style(base_layers[0], geo_field)

                if len(base_layers) > 1:
                    symbols = deepcopy(symbols)
                    # Set the border color to black for selected geometries
                    for symbol in symbols:
                        symbol['color_border'] = '0,0,0,255'

                    base_layers[1].update({
                        'symbols': symbols,
                        'symbols_attr': m2o_field.name,
                    })
                    cls._add_symbol_style(base_layers[1], geo_field)

        return layers, bbox, srid

    @classmethod
    def parse(cls, report, records, data, localcontext):
        """Create QGis project file based on the selected record:
            the fields referenced in the model FIELDS variable will each have
            a separate layer in the renderd file.
        """
        User = Pool().get('res.user')
        Translation = Pool().get('ir.translation')
        filename = os.path.join(os.path.dirname(__file__), 'qgis.qgs')
        report = RelatorioReport(filename, 'text/plain', ReportFactory(), MIMETemplateLoader())

        QGisConf = Pool().get('qgis.conf')
        conf = QGisConf.search([])
        if len(conf) != 0:
            version = conf[0].version
        else:
            version = '1.9.0-Master'

        legend = OrderedDict()
        if cls.FIELDS is None:
            layers, bbox, srid = cls.get_layer(records, records[0].__name__)

            for layer in layers:
                legend[layer['title']] = layer
        else:
            layers = []
            bbox = None
            Model = Pool().get(records[0].__name__)
            for field, val in cls.FIELDS.iteritems():
                if val is None:
                    fields = [field]
                else:
                    fields = val.keys()
                sublayers = []
                for _field in fields:
                    recs = getattr(records[0], _field)
                    relation = getattr(Model, _field).model_name
                    _layers, _bbox, srid = cls.get_layer(recs, relation)
                    if _bbox is not None:
                        bbox = envelope_union(_bbox, bbox)
                    sublayers += _layers

                # Remove sublayers that are already added
                _sublayers = []
                for layer in sublayers:
                    if layer['model'] in [_layer['model'] for _layer in layers]:
                        continue
                    _sublayers.append(layer)
                sublayers = _sublayers
                layers += sublayers

                if val is None:
                    for layer in sublayers:
                        legend[layer['title']] = layer
                else:
                    if field not in legend:
                        legend[field] = OrderedDict()
                    for layer in sublayers:
                        legend[field][layer['title']] = layer

        if bbox is None:
            bbox = [
                -357823.2365,
                6037008.6939,
                1313632.3628,
                7230727.3772
            ]

        WfsConf = Pool().get('wfs.conf')
        wfs_url = WfsConf.get_url()

        localcontext.update({
            'data': data,
            'user': User(Transaction().user),
            'formatLang': cls.format_lang,
            'StringIO': StringIO.StringIO,
            'time': time,
            'datetime': datetime,
            'context': Transaction().context,
            'qgis_version': version,
            'wfs_url': wfs_url,
            'bbox': bbox,
            'srid': srid,
            'layers': layers,
            'legend': legend,
        })

        translate = TranslateFactory(cls.__name__, Transaction().language, Translation)
        localcontext['setLang'] = lambda language: translate.set_language(language)
        translator = Translator(lambda text: translate(text))
        report.filters.insert(0, translator)

        localcontext = dict(map(lambda x: (str(x[0]), x[1]), localcontext.iteritems()))

        #Test compatibility with old relatorio version <= 0.3.0
        if len(inspect.getargspec(report.__call__)[0]) == 2:
            data = report(records, **localcontext).render().getvalue()
        else:
            localcontext['objects'] = records  # XXX to remove
            localcontext['records'] = records
            data = report(**localcontext).render()
            if hasattr(data, 'getvalue'):
                data = data.getvalue()
        return ('qgs', data)
