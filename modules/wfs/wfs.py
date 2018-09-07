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

from cgi import escape
import logging
import os
import re
import sys
import time
from traceback import format_exception, format_exception_only
from urllib import unquote
from xml.dom.minidom import parseString

from genshi.builder import ElementFactory
from genshi.core import Markup
from genshi.template import TemplateLoader, MarkupTemplate
from psycopg2.extensions import AsIs, QuotedString

from trytond.config import CONFIG
from trytond.model import ModelView
from trytond.pool import Pool
from trytond.rpc import RPC
from trytond.transaction import Transaction

__all__ = ['Wfs']


WFS_NS = 'http://www.opengis.net/wfs'
GML_NS = 'http://www.opengis.net/gml'
OGC_NS = 'http://www.opengis.net/ogc'
WFS_VERSION = '1.1.0'
WFS_REQUESTS = ['getcapabilities', 'describefeaturetype', 'getfeature']
WFS_TYPE = {
    'binary': None,
    #'boolean': 'bool',
    'boolean': '',
    'char': '',
    #'date': 'date',
    'date': '',
    #'datetime': 'time',
    'datetime': '',
    #'float': 'float',
    'float': '',
    'integer': 'integer',
    'many2many': None,
    'many2one': 'decimal',
    'numeric': 'decimal',
    'one2many': None,
    'one2one': 'decimal',
    'reference': None,
    'selection': '',
    'text': '',

    'geometry': 'gml:GeometryPropertyType',
    'point': 'gml:PointPropertyType',
    'linestring': 'gml:LinearRingPropertyType',
    'polygon': 'gml:PolygonPropertyType',
    'multipoint': 'gml:MultiPointPropertyType',
    'multilinestring': 'gml:MultiLinePropertyType',
    'multipolygon': 'gml:MultiPolygonPropertyType',
    'geometrycollection': 'gml:GeometryCollectionPropertyType',
}

WFS_OPERATIONS = {
    'Update': 'write',
    'Insert': 'create',
    'Delete': 'delete',
}

WFS_FILTER_BOOL_OP = ['and', 'or']

WFS_FILTER_OP = {
    'propertyisequalto': '=',
    'propertyisnotequalto': '!=',
    'propertyisgreaterthan': '>',
    'propertyisgreaterthanorequalto': '>=',
    'propertyislessthan': '<',
    'propertyislessthanorequalto': '<=',
}

GEO_TYPES = [
    'geometry',
    'point',
    'linestring',
    'polygon',
    'multipoint',
    'multilinestring',
    'multipolygon',
    'geometrycollection',
]


TRYTON_FIELDS = ['create_uid', 'create_date', 'write_uid', 'write_date', 'rec_name']

logger = logging.getLogger("server")


def get_wfs_type(ttype):
    if WFS_TYPE.get(ttype, None) is not None:
        return {'type': WFS_TYPE[ttype]}
    return {}


def gml2sql(gml, field):
    """Converts GML into a psycopg SQL query"""
    gml = gml.replace('<gml:', '<')
    gml = gml.replace('</gml:', '</')
    gml = QuotedString(gml)
    gml = gml.getquoted()
    if field._type.startswith('multi'):
        # Enforce multi* type
        sql = 'ST_Multi(ST_GeomFromGML(%s))' % gml
    else:
        sql = 'ST_GeomFromGML(%s)' % gml
    gml = AsIs(sql)
    return gml


def _filter2domain(ogc):
    nodeName = ogc.nodeName.split(':', 1)[1].lower()
    if nodeName in WFS_FILTER_BOOL_OP:
        domain = [nodeName.upper()]
        for node in ogc.childNodes:
            if not node.nodeName.startswith('ogc:'):
                continue
            domain.append(_filter2domain(node))
    elif nodeName in WFS_FILTER_OP:
        field = None
        val = None
        for node in ogc.childNodes:
            if not node.nodeName.lower().startswith('ogc:'):
                continue
            if node.nodeName.lower() == 'ogc:propertyname':
                field = node.firstChild.nodeValue
            elif node.nodeName.lower() == 'ogc:literal':
                val = int(node.firstChild.nodeValue)
            else:
                raise Exception('Unsupported filter node: %s' % node.nodeName)
        return [(field, WFS_FILTER_OP[nodeName], val)]
    else:
        raise Exception('Unsupported filter node: %s' % ogc.nodeName)
    return domain


def filter2domain(ogc):
    if ogc == '':
        return []

    # Hack to ensure compatibility with a QGis 1.8
    if 'ogc:' not in ogc:
        ogc = re.sub(r'<([^/][^>]+)', r'<ogc:\1', ogc)
        ogc = re.sub(r'</', r'</ogc:', ogc)

    ogc = '<?xml version="1.0" encoding="UTF-8"?>\n<ogc:Filter xmlns:ogc="%s">%s</ogc:Filter>' % (OGC_NS, ogc)
    ogc = parseString(ogc)
    ogc = ogc.firstChild.firstChild

    if ogc.nodeName.lower() != 'ogc:filter':
        raise Exception('Invalid filter: %s' % ogc.nodeName)

    for child in ogc.childNodes:
        if child.nodeName.lower().startswith('ogc:'):
            domain = _filter2domain(child)
            return domain
    return []


class WfsRequest(object):
    def __init__(self):
        self.tmpl_loader = TemplateLoader(
            os.path.join(os.path.dirname(__file__), 'templates'),
            auto_reload=True,
            default_class=MarkupTemplate,
        )
        WfsConf = Pool().get('wfs.conf')
        conf = WfsConf.search([])

        if len(conf) == 0:
            self.show_non_geo = False
            self.default_geo = False
        else:
            self.show_non_geo = conf[0].show_non_geo
            self.default_geo = conf[0].default_geo

        self.url = WfsConf.get_url()
        self.model_access = Pool().get('ir.model.access')
        self.field_access = Pool().get('ir.model.field.access')

    def access_check(self, model, field=None, mode='read', raise_exception=True):
        allowed = True
        try:
            allowed &= self.model_access.check(model, mode, raise_exception=False)
            if field is not None:
                allowed &= self.field_access.check(model, [field], mode, raise_exception=False)
        except:
            allowed = False

        if not allowed and raise_exception:
            raise Exception('Permission denied')
        return allowed

    def _parse_args(self, **kw):
        _kw = {}
        for arg, val in kw.iteritems():
            if isinstance(val, str):
                _kw[arg.lower()] = unquote(val)

        if 'acceptversions' in _kw:
            version = _kw.pop('acceptversions')
            if WFS_VERSION not in version.split(','):
                raise Exception('Unsupported version, server version %s, client version %s' % (WFS_VERSION, version))

        if 'version' in _kw:
            self.version = _kw.pop('version')
            if self.version.split('.') > WFS_VERSION.split('.'):
                logger.warning('Wfs version of client is superior than our version (1.1.0)')
        else:
            self.version = ''

        service = _kw.pop('service', 'wfs').lower()
        if service != 'wfs':
            raise Exception('Invalid service %s, expected WFS' % service)

        if 'srsname' in _kw:
            _kw['srsname'] = int(_kw['srsname'].split('::')[1])
        return _kw

    def handle(self, **kw):
        _kw = self._parse_args(**kw)
        request = _kw.pop('request').lower()

        if request in WFS_REQUESTS and hasattr(self, request):
            return getattr(self, request)(**_kw)
        return self.getcapabilities()

    def getcapabilities(self, bbox=[], srsname=0, **kw):
        Field = Pool().get('ir.model.field')
        features = []
        models = []
        if bbox != []:
            bbox = [float(nbr) for nbr in bbox.split(',')]

        domain = ['OR'] + [[('ttype', '=', geo_type)] for geo_type in GEO_TYPES]
        fields = Field.search(domain)
        for field in fields:
            model = field.model.model
            if not self.access_check(model, raise_exception=False):
                continue
            Model = Pool().get(model)
            records = Model.search([], limit=1)

            # Check the table contains records in the bbox
            models.append(model)
            cursor = Transaction().cursor
            table = model.replace('.', '_')
            if Model.table_query() : table = '('+Model.table_query()[0]%tuple(Model.table_query()[1])+') AS mytable'
            col = field.name
            if bbox != [] and srsname != 0:
                sql = 'SELECT ST_Extent(Box2D(%(col)s)) FROM %(table)s WHERE\
                    ST_Intersects(\
                        ST_SetSRID(\
                            ST_MakeBox2D(\
                                ST_MakePoint(%(xmin)s, %(ymin)s),\
                                ST_MakePoint(%(xmax)s, %(ymax)s)\
                            ), %(srsname)s\
                        ), %(col)s )' % {
                        'col': col,
                        'table': table,
                        'xmin' : bbox[0],
                        'ymin' : bbox[1],
                        'xmax' : bbox[2],
                        'ymax' : bbox[3],
                        'srsname' : srsname}
                cursor.execute(sql)
            else:
                try: 
                    cursor.execute('SELECT ST_Estimated_Extent(\'%s\', \'%s\');' % (table, col))
                except:
                    cursor.connection.rollback()
                    cursor.execute('SELECT ST_Extent(Box2D(%s)) FROM %s;' % (col, table))


            feature_bbox = cursor.fetchall()
            if len(feature_bbox) != 0 and len(feature_bbox[0]) != 0 and feature_bbox[0][0] is not None:
                feature_bbox = feature_bbox[0][0]
                feature_bbox = feature_bbox.replace('BOX(', '')
                feature_bbox = feature_bbox.replace(')', '')
                tl, ur = feature_bbox.split(',')
                feature_bbox = tl.split(' ') + ur.split(' ')
            else:
                feature_bbox = None

            features.append({
                'title': field.model.name,
                'name': field.model.model,
                'srs': 'EPSG:%s' % getattr(Model, field.name).srid,
                'bbox': feature_bbox,
            })

        if self.show_non_geo:
            Model = Pool().get('ir.model')
            domain = [('model', '!=', model) for model in models]
            for model in Model.search(domain):
                if not self.access_check(model.model, raise_exception=False):
                    continue
                m = Pool().get(model.model)
                if not hasattr(m, 'search'):
                    continue

                records = m.search([], limit=1)
                features.append({
                    'title': model.name,
                    'name': model.model,
                    'srs': '',
                    'bbox': None,
                })

        # Sort models
        features = sorted(features, key=lambda x: x['title'])

        wfs_capabilities = self.tmpl_loader.load('wfs_capabilities.xml')
        rendered = wfs_capabilities.generate(name='Tryton',
                                             title='Tryton WFS module',
                                             abstract='Tryton WFS module',
                                             url=self.url,
                                             features=features).render()
        return rendered

    def describefeaturetype(self, typename, **kw):
        tryton, model = typename.split(':', 1)
        if tryton != 'tryton':
            raise Exception('Unknown feature type %s' % typename)
        self.access_check(model)
        Fields = Pool().get('ir.model.field')
        fields = Fields.search([('model.model', '=', model)])

        elements = []
        for field in fields:
            if field.name in TRYTON_FIELDS:
                continue
            if not self.access_check(model, field.name, raise_exception=False):
                continue
            nillable = 'true'
            if hasattr(field, 'required') and field.required:
                nillable = 'false'

            if get_wfs_type(field.ttype) == {}:
                continue

            element = {
                'name': field.name,
                'type': get_wfs_type(field.ttype),
                'nillable': nillable,
            }
            elements.append(element)

        wfs_featuretype = self.tmpl_loader.load('wfs_featuretype.xml')
        rendered = wfs_featuretype.generate(name=fields[0].model.model,
                                            elements=elements).render()
        return rendered

    def getfeature(self, typename, filter='', srsname=0, maxfeatures=1024, bbox=[], **kw):
        tryton, model = typename.split(':', 1)
        if tryton != 'tryton':
            raise Exception('Unknown feature %s' % typename)

        self.access_check(model)

        if bbox != []:
            bbox = [float(nbr) for nbr in bbox.split(',')]

        Fields = Pool().get('ir.model.field')
        fields = Fields.search([('model.model', '=', model)])
        Model = Pool().get(model)
        factory = ElementFactory()
        cursor = Transaction().cursor
        records = None
        filter_domain = filter2domain(filter)

        # Find a geometry field and select records in the bbox if there is one
        if bbox != []:
            for field in fields:
                if field.ttype not in GEO_TYPES:
                    continue

                if not self.access_check(model, field.name, raise_exception=False):
                    continue

                sql = 'SELECT id FROM %(table)s WHERE\
                    ST_Intersects(\
                        ST_SetSRID(\
                            ST_MakeBox2D(\
                                ST_MakePoint(%(xmin)s, %(ymin)s),\
                                ST_MakePoint(%(xmax)s, %(ymax)s)\
                            ), %(srsname)s\
                        ), %(col)s\
                    ) LIMIT %(maxfeatures)s' % {
                            'table' : model.replace('.', '_'), 
                            'col' : field.name,
                            'xmin' : bbox[0],
                            'ymin' : bbox[1],
                            'xmax' : bbox[2],
                            'ymax' : bbox[3],
                            'srsname' : srsname,
                            'maxfeatures' : maxfeatures }
                cursor.execute(sql)
                domain = [[('id', '=', col[0])] for col in cursor.fetchall()]
                if len(domain) == 0:
                    continue
                domain = ['AND', filter_domain, [['OR'] + domain]]
                records = Model.search(domain, limit=maxfeatures)
                break
        else:
            records = Model.search(filter_domain, limit=maxfeatures)

        if not records: records = []
        print len(records), ' features returned'

        fbbox = None
        elems = []
        for record in records:
            elem = getattr(factory, 'gml:featureMember')
            tag = getattr(factory, 'tryton:%s' % model)(fid='%s.%i' % (model, record.id))
            elem.children.append(tag)
            elems.append(elem)

            for field in fields:
                if field.name in TRYTON_FIELDS:
                    continue

                if not self.access_check(model, field.name, raise_exception=False):
                    continue

                if get_wfs_type(field.ttype) == {}:
                    continue

                if field.ttype in GEO_TYPES:
                    cursor.execute('SELECT ST_AsGML(%s) FROM %s WHERE id=%s' % (field.name, model.replace('.', '_'), record.id))
                    ret = cursor.fetchall()
                    if ret[0][0] is None and self.default_geo:
                        # when there is no geometry, create one
                        if bbox == []:
                            if srsname == 0 or srsname == 2154:
                                srsname = 2154
                                # EPSG:2154 projected boundaries
                                fbbox = [
                                    -357823.2365,
                                    6037008.6939,
                                    1313632.3628,
                                    7230727.3772
                                ]
                            else:
                                # TODO: handle this case
                                raise Exception('You must specify a bounding box when using an srsname different of EPSG:2154')
                        else:
                            fbbox = bbox

                        xmin = fbbox[0] + ((fbbox[2] - fbbox[0]) * 0.25)
                        xmax = fbbox[0] + ((fbbox[2] - fbbox[0]) * 0.75)
                        ymin = fbbox[1] + ((fbbox[3] - fbbox[1]) * 0.25)
                        ymax = fbbox[1] + ((fbbox[3] - fbbox[1]) * 0.75)

                        if field.ttype == 'multipolygon':
                            cursor.execute("SELECT ST_AsGML(ST_GeomFromEWKT('srid=%i;multipolygon( ((%s %s, %s %s, %s %s, %s %s, %s %s)) )'))" %
                                           (srsname,
                                            xmin, ymin,
                                            xmin, ymax,
                                            xmax, ymax,
                                            xmax, ymin,
                                            xmin, ymin), ())
                            val = Markup(cursor.fetchall()[0][0])
                        elif field.ttype == 'multilinestring':
                            cursor.execute("SELECT ST_AsGML(ST_GeomFromEWKT('srid=%i;multilinestring( (%s %s, %s %s, %s %s, %s %s) )'))" %
                                           (srsname,
                                            xmin, ymin,
                                            xmin, ymax,
                                            xmax, ymax,
                                            xmax, ymin), ())
                            val = Markup(cursor.fetchall()[0][0])
                        elif field.ttype == 'multipoint':
                            cursor.execute("SELECT ST_AsGML(ST_GeomFromEWKT('srid=%i;multipoint(%s %s, %s %s)'))" %
                                           (srsname,
                                            xmin, ymin,
                                            xmin, ymax), ())
                            val = Markup(cursor.fetchall()[0][0])
                    elif ret[0][0] is None:
                        val = ''
                    else:
                        val = Markup(ret[0][0])
                else:
                    val = getattr(record, field.name)
                    if val is None:
                        val = ''
                    elif field.ttype == 'many2one':
                        val = val.id

                _field = getattr(ElementFactory(), 'tryton:%s' % field.name)()
                _field.children.append(val)
                tag.children.append(_field)

        wfs_feature = self.tmpl_loader.load('wfs_feature.xml')
        rendered = wfs_feature.generate(url=self.url,
                                        ttype='tryton:%s' % model,
                                        elems=elems).render()
        return rendered

    def post(self, data, **kw):
        data = parseString(data)
        data = data.firstChild
        if data.nodeName != 'Transaction':
            raise Exception('Invalid transaction')

        inserts = []
        deletes = []
        updates = []

        _kw = self._parse_args(**kw)
        srsname = _kw.get('srsname', 0)

        for trans_type in ('Delete', 'Update', 'Insert'):
            for transaction in data.childNodes:
                if transaction.nodeName != trans_type:
                    continue
                if transaction.nodeName in ('Update', 'Delete'):
                    typename = transaction.getAttribute('typeName')
                    tryton, model = typename.split(':', 1)
                else:
                    if transaction.firstChild is None:
                        raise Exception('Invalid transaction')
                    typename = transaction.firstChild.nodeName
                    model = typename
                    tryton = 'tryton'

                tryton_op = WFS_OPERATIONS[transaction.nodeName]
                self.access_check(model, mode=tryton_op)

                Model = None
                try:
                    Model = Pool().get(model)
                except:
                    pass

                if Model is None or tryton != 'tryton':
                    raise Exception('Unknown feature type %s' % typename)

                if srsname == 0:
                    for field in Model._fields.itervalues():
                        if field._type in GEO_TYPES:
                            srsname = field.srid
                            break
                    else:
                        raise Exception('Srid is not set, cannot modify geometry')

                geo_field = None
                field = None
                value = None
                record_id = None
                to_delete = []
                record = {}
                if transaction.nodeName in ('Update', 'Delete'):
                    children = transaction.childNodes
                elif transaction.nodeName == 'Insert':
                    children = transaction.firstChild.childNodes

                for child in children:
                    if transaction.nodeName in ('Update', 'Delete'):
                        if child.nodeName == 'Property':
                            for property in child.childNodes:
                                if property.nodeName == 'Name':
                                    field = property.firstChild.data
                                    self.access_check(model, field, mode=tryton_op)
                                elif property.nodeName == 'Value':
                                    if (property.hasChildNodes() and
                                            property.firstChild.namespaceURI == GML_NS):
                                        value = gml2sql(property.firstChild.toxml(), getattr(Model, field))
                                        geo_field = field
                                    else:
                                        if property.firstChild is not None:
                                            value = property.firstChild.nodeValue
                                        else:
                                            value = None
                                else:
                                    raise Exception('Unhandled node type %s' % property.nodeName)

                        elif child.nodeName == 'Filter':
                            for subchild in child.childNodes:
                                if subchild.nodeName == 'FeatureId':
                                    fid = subchild.getAttribute('fid')
                                    _model, record_id = fid.rsplit('.', 1)
                                    if transaction.nodeName == 'Delete':
                                        to_delete.append(int(record_id))

                                    if model != _model:
                                        raise Exception('fid doesn\'t match the typename of the model (%s != %s)' % (model, _model))
                                else:
                                    raise Exception('Unhandled node type %s' % child.nodeName)
                        else:
                            raise Exception('Unhandled node type %s' % child.nodeName)
                    elif transaction.nodeName == 'Insert':
                        field = child.nodeName
                        if (child.hasChildNodes() and
                                child.firstChild.namespaceURI == GML_NS):
                            value = gml2sql(child.firstChild.toxml(), getattr(Model, field))
                            geo_field = field
                        else:
                            if child.firstChild is None:
                                value = None
                            else:
                                value = child.firstChild.nodeValue

                    if trans_type != 'Delete':
                        if field == 'id':
                            continue

                        if getattr(Model, field).readonly:
                            continue

                    record[field] = value

                if transaction.nodeName == 'Insert' and record != {}:
                    if geo_field is not None:
                        value = record.pop(geo_field)
                    record = Model.create([record])[0]
                    if geo_field is not None:
                        cursor = Transaction().cursor
                        cursor.execute('UPDATE %s SET %s = %s WHERE id = %%s' %
                                       (model.replace('.', '_'), field, value), (record.id,))
                    inserts.append('%s.%i' % (model, record.id))
                elif transaction.nodeName == 'Delete':
                    Model.delete(to_delete)
                    to_delete = ['%s.%s' % (model, _id) for _id in to_delete]
                    deletes += to_delete
                elif transaction.nodeName == 'Update' and record != {}:
                    fields = record.keys()
                    sql = 'UPDATE %s SET ' % model.replace('.', '_')
                    sql += ', '.join(['%s = %%s' % field for field in fields])
                    sql += ' WHERE id = %s'

                    sql_args = [record[field] for field in fields]
                    sql_args.append(record_id)
                    cursor = Transaction().cursor
                    cursor.execute(sql, sql_args)
                    updates.append('%s.%s' % (model, record_id))

        wfs_trans_summary = self.tmpl_loader.load('wfs_trans_response.xml')
        rendered = wfs_trans_summary.generate(updates=updates,
                                              deletes=deletes,
                                              inserts=inserts).render()
        return rendered

    def format_exc(self):
        wfs_error = self.tmpl_loader.load('wfs_error.xml')
        if CONFIG['log_level'].upper() == 'DEBUG':
            tb_s = ''.join(format_exception(*sys.exc_info()))
            for path in sys.path:
                tb_s = tb_s.replace(path, '')
        else:
            tb_s = ''.join(format_exception_only(*sys.exc_info()[:2]))

        error_msg = escape(tb_s.decode('utf-8'))
        rendered = wfs_error.generate(error_msg=error_msg).render()
        return rendered


class Wfs(ModelView):
    'Wfs'
    __name__ = 'wfs.wfs'

    @classmethod
    def __setup__(cls):
        super(Wfs, cls).__setup__()
        cls.__rpc__.update({
            'wfs': RPC(),
            'wfs_POST': RPC(False),
        })

        if len(CONFIG['http']) == 0:
            raise Exception('You have to enable the http protocol in tryton.conf in order to use this module.')

    @classmethod
    def wfs(cls, **kw):
        begin = time.time()
        req = WfsRequest()
        try:
            ret = req.handle(**kw)
        except Exception:
            logger.exception('Wfs request failure')
            ret = req.format_exc()
        #logger.debug('WFS response: %s', ret)
        logger.debug('WFS request handled in %0.1fs', (time.time() - begin))
        return ret

    @classmethod
    def wfs_POST(cls, data, **kw):
        logger.debug('WFS post content: %s', data)
        begin = time.time()
        req = WfsRequest()
        try:
            ret = req.post(data, **kw)
        except Exception:
            logger.exception('Wfs POST request failure')
            ret = req.format_exc()
        #logger.debug('WFS POST response: %s', ret)
        logger.debug('WFS POST request handled in %0.1fs', (time.time() - begin))
        return ret
