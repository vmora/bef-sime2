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

Copyright (c) 2014 Vincent Mora vincent.mora@oslandia.com
Copyright (c) 2012-2013 Bio Eco Forests <contact@bioecoforests.com>
Copyright (c) 2012-2013 Pascal Obstetar
Copyright (c) 2012-2013 Pierre-Louis Bonicoli

Reference implementation for stuff with geometry and map
"""

from trytond.pool import Pool
from trytond.model import Model
from trytond.config import config
from trytond.transaction import Transaction

import shutil
import os
import time
import urllib
from urllib.request import urlopen
import re
from urllib.parse import urlparse, parse_qs, quote, unquote, urlunparse
import xml.dom 
import tempfile
import stat
import codecs

__all__ = [
    'Mapable',
    ]


def bbox_aspect(bbox, width, height, percent_margin = .1):
    """maintain ratio of bbox = [xmin, ymin, xmax, ymax]
    margin is a percentage of bbox
    in case a dimension of bbox is zero, 
    the width or height is taken instead"""
    assert( len(bbox) == 4 )
    dx = bbox[2] - bbox[0]
    dy = bbox[3] - bbox[1]
    margin = max(dx, dy) * percent_margin
    cx, cy = (bbox[0] + bbox[2])/2.0, (bbox[1] + bbox[3])/2.0

    # for special case for horizontal and vertical lines and for points
    if dx > 0 and dy <= 0 : dy = dx * 0.01
    if dx <=0 and dy > 0 : dx = dy * 0.01
    if dx <=0 and dy <= 0 : 
        dx = width
        dy = height

    dx += 2*margin
    dy += 2*margin

    aspect =  float(width) / height # float to avoid integer division
    # float to avoid integer division
    if float(dx) / dy > aspect:
        dy = dx / aspect
    else:
        dx = dy * aspect

    return [ cx - dx/2.0, cy - dy/2.0, 
             cx + dx/2.0, cy + dy/2.0]

class Mapable(Model):
    'Mapable'
    __name__ = 'qgis.mapable'

    DEBUG = True

    def _get_image(self, qgis_filename, composition_name):
        """Return a feature image produced by qgis wms server from a template qgis file
        containing a composition"""
        if self.geom is None:
            return buffer('')

        start = time.time()

        # retrieve attached .qgs file
        [model] = Pool().get('ir.model').search([('model', '=', self.__name__)])

        attachements = Pool().get('ir.attachment').search(
                [('resource', '=', "ir.model,%s"%model.id)])
        attachement = None
        for att in attachements: 
            if att.name == qgis_filename:
                attachement = att
                break
        if not attachement:
            self.raise_user_error("%s has no attachement %s", (self.__name__, qgis_filename))

        # get credentials for qgsi server
        #config = ConfigParser.ConfigParser()
        #config.read(config['qgis_server_conf'])
        #username = config.get('options','username')
        #password = config.get('options','password')
        # 
        # we don't need that anymore, the server will have admin credentials (we will see how) to
        # access the wfs server

        # replace feature id in .qgs file and put credentials in
        if not self.DEBUG:
            tmpdir = tempfile.mkdtemp()
        else:
            tmpdir = '/tmp/'+qgis_filename
            if not os.path.exists(tmpdir): os.mkdir(tmpdir)

        os.chmod(tmpdir, stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IXGRP|stat.S_IRGRP)
        dot_qgs = os.path.join(os.path.abspath(tmpdir), 'proj.qgs')
        dom = xml.dom.minidom.parseString( attachement.data )

        for elem in dom.getElementsByTagName('datasource'):

            basename = os.path.basename(elem.childNodes[0].data)
            for att in attachements: 
                if att.name == basename:
                    filename = os.path.join(os.path.abspath(tmpdir), basename)
                    with open(filename, 'wb') as image:
                        image.write( att.data )
                        elem.childNodes[0].data = filename
                    break

            # check that this is the appropriate layer
            url_parts = urlparse(elem.childNodes[0].data)
            param = parse_qs(url_parts[4])
            if 'TYPENAME' in param and param['TYPENAME'][0].find('tryton:') != -1:
                if 'FILTER' in param :
                    filt = unquote(param['FILTER'][0])
                    filt = re.sub(
                            '<ogc:Literal>.*</ogc:Literal>', 
                            '<ogc:Literal>'+str(self.id)+'</ogc:Literal>', 
                            filt)
                    param.update({'FILTER' : [quote(filt)]})
                #param.update({'username' : [username], 'password' : [password]})
                elem.childNodes[0].data = urlunparse(list(url_parts[0:4]) + 
                        ['&'.join([key+'='+','.join(val) for key, val in param.items()])] + 
                        list(url_parts[5:]))

        # replaces images with linked ones and put them in the temp directory
        for elem in dom.getElementsByTagName('LayoutItem'):
            if elem.hasAttribute('file'):
                basename = os.path.basename(elem.attributes['file'].value)
                for att in attachements: 
                    if att.name == basename:
                        image_file = os.path.join(os.path.abspath(tmpdir), basename)
                        with open(image_file, 'wb') as image:
                            image.write( att.data )
                            elem.attributes['file'].value = image_file
                        break


        with codecs.open(dot_qgs, 'w', 'utf-8') as file_out:
            dom.writexml(file_out, indent='  ')

        # find the composer map aspect ratio and margins
        # from atlas
        map_extends = {};
        compo = dom.getElementsByTagName('Layouts')[0];
        for cmap in compo.getElementsByTagName('Layout'):
            for item in compo.getElementsByTagName('LayoutItem'):
                ext = item.getElementsByTagName('Extent')
                if len(ext):
                    ext = ext[0]
                    width = float(ext.attributes['xmax'].value) \
                        - float(ext.attributes['xmin'].value)
                    height = float(ext.attributes['ymax'].value) \
                        - float(ext.attributes['ymin'].value)
                    atlas_map = item.getElementsByTagName('AtlasMap')[0]
                    map_extends['map0'] = {'w':width, 'h':height, 'margin':.1, 'ext':ext}
                    if atlas_map and atlas_map.attributes['margin']:
                        map_extends['map0'] = {'w':width, 'h':height, 'margin':float(atlas_map.attributes['margin'].value), 'ext':ext}

        layers=[layer.attributes['name'].value for layer in dom.getElementsByTagName('layer-tree-layer')]

        ## compute bbox 
        cursor = Transaction().connection.cursor()
        sql = ('SELECT ST_SRID(geom), ST_Extent(geom) '
            'FROM '+self.__name__.replace('.', '_')+' WHERE id = '+str(self.id)+' GROUP BY id;' )
        cursor.execute(sql)

        [srid, ext] = cursor.fetchone()
        if ext:
            for name, mex in map_extends.items():
                ext = ext.replace('BOX(', '').replace(')', '').replace(' ',',')

                # ajout Pascal Obstetar pour EPSG:4326
                if srid==4326:
                    minlat, minlong, maxlat, maxlong = ext.split(',')
                    ext = ','.join([minlong,minlat,maxlong,maxlat])

                mex['ext'] =  ','.join([str(i) for i in bbox_aspect([float(i) for i in ext.split(',')], mex['w'], mex['h'], mex['margin'])])

        # render image
        url = 'http://localhost:8080/qgis?'+'&'.join([
              'SERVICE=WMS',
              'VERSION=1.3.0',
              'MAP='+dot_qgs,
              'REQUEST=GetPrint',
              'FORMAT=png',
              'TEMPLATE='+quote(composition_name.encode('utf-8')),
              'LAYER='+','.join([quote(l.encode('utf-8')) for l in layers[::-1]]),
              'CRS=EPSG:'+str(config.getint('database', 'srid')),
              'DPI=75']+[name+':EXTENT='+me['ext'] for name, me in map_extends.items()
              ])
        try:
            buf = urlopen(url).read()
        except:
            print('##################### ', time.time() - start, ' to fail on', url)
            raise

        print('##################### ', time.time() - start, 'sec to GetPrint ', url)

        if (str(buf).find('ServiceException') != -1):
            self.raise_user_error("%s qgis-mapserver error:\n%s", (self.__name__, str(buf)))
        
        # TODO uncoment to cleanup, 
        # the directory and its contend are kept for debug
        if not self.DEBUG:
            shutil.rmtree(tmpdir)

        return buf

    @classmethod
    def __setup__(cls):
        super(Mapable, cls).__setup__()
