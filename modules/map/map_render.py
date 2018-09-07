#!/usr/bin/python
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
from cStringIO import StringIO
import math

import cairo
from osgeo import ogr, osr
import ModestMaps
from PIL import Image

from trytond.modules.geotools.tools import check_envelope
from trytond.pool import Pool
from trytond.tools.misc import file_open

class OSMCustomProvider(ModestMaps.OpenStreetMap.Provider):
    def __init__(self, url):
        ModestMaps.OpenStreetMap.Provider.__init__(self)
        self.url = url

    def getTileUrls(self, coordinate):
        return ('%s/%d/%d/%d.png' % (self.url, coordinate.zoom, coordinate.column, coordinate.row),)


class MapRender(object):
    def __init__(self, width, height, bbox, with_bg=False):
        check_envelope(bbox)
        self.width = width
        self.height = height
        self.ll = (bbox[0], bbox[2])
        self.ur = (bbox[1], bbox[3])
        self.legends = []
        self.img_format = 'JPG'

        MapConf = Pool().get('map.conf')
        conf = MapConf.search([])
        if with_bg:
            if len(conf) == 0:
                self.provider = 'OPENSTREETMAP'
                provider = ModestMaps.builtinProviders['OPENSTREETMAP']()
            elif conf[0].map_provider == 'OPENSTREETMAP_CUSTOM':
                self.provider = 'OPENSTREETMAP'
                provider = OSMCustomProvider(conf[0].osm_url)
            else:
                self.provider = conf[0].map_provider
                if self.provider is None:
                    self.provider = 'OPENSTREETMAP'
                provider = ModestMaps.builtinProviders[self.provider]()

            dimensions = ModestMaps.Core.Point(self.width, self.height)
            locationLL = ModestMaps.Geo.Location(self.ll[1], self.ll[0])
            locationUR = ModestMaps.Geo.Location(self.ur[1], self.ur[0])
            self.map = ModestMaps.mapByExtent(provider, locationLL, locationUR, dimensions)
        else:
            self.map = None

        if len(conf) != 0:
            self.img_format = conf[0].img_format

        self.has_bg = False

        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(self.surface)

        # Clear the image
        self.ctx.set_source_rgb(1.0, 1.0, 1.0)
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()

    def add_bg(self):
        img = self.map.draw(True, False)
        img_fp = StringIO()
        img.save(img_fp, 'PNG')
        img_fp.seek(0)
        surface = cairo.ImageSurface.create_from_png(img_fp)
        self.ctx.set_source_surface(surface)
        self.ctx.paint()
        self.has_bg = True

    def _loc_to_xy(self, _x, _y):
        if self.map:
            l = ModestMaps.Geo.Location(_y, _x)
            p = self.map.locationPoint(l)
            return p.x, p.y
        else:
            x = (_x - self.ll[0]) * self.width / (self.ur[0] - self.ll[0])
            y = (_y - self.ll[1]) * self.height / (self.ur[1] - self.ll[1])
            y = self.height - y
            return x, y

    def _set_bgstyle(self, ctx, bgstyle, bgcolor):
        if bgstyle == '.':
            # 30, 30 space in horizontal/vertical
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 30, 30)
            _ctx = cairo.Context(surface)
            _ctx.set_source_rgba(*bgcolor)
            _ctx.arc(2 + bgcolor[0], 2 + bgcolor[1], 3, 0, 2 * math.pi)
            _ctx.fill()
            pattern = cairo.SurfacePattern(surface)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            ctx.set_source(pattern)
        elif bgstyle == '+':
            # 60, 60 space in horizontal/vertical
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 60, 60)
            _ctx = cairo.Context(surface)
            _ctx.set_source_rgba(*bgcolor)
            _ctx.rectangle(2, 2, 10, 10)
            _ctx.fill()
            pattern = cairo.SurfacePattern(surface)
            pattern.set_extend(cairo.EXTEND_REPEAT)
            ctx.set_source(pattern)        
        else:
            ctx.set_source_rgba(*bgcolor)

    def _add_linestring_gdal(self, linestring, linestyle, color, bgstyle, bgcolor):
        for point_no in xrange(linestring.GetPointCount()):
            x = linestring.GetX(point_no)
            y = linestring.GetY(point_no)
            x, y = self._loc_to_xy(x, y)

            if point_no == 0:
                self.ctx.move_to(x, y)
            else:
                self.ctx.line_to(x, y)

    def add_linestring_gdal(self, linestring, linestyle, color, bgstyle, bgcolor):
        self._add_linestring_gdal(linestring, linestyle, color, bgstyle, bgcolor)
        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(3)
        if linestyle == '--':
            self.ctx.set_dash([5, 5], 1)
        else:
            self.ctx.set_dash([], 0)
        self.ctx.stroke()

        centroid = linestring.Centroid()
        return self._loc_to_xy(centroid.GetX(), centroid.GetY())

    def add_point_gdal(self, point, linestyle, color, bgstyle, bgcolor):
        x = point.GetX()
        y = point.GetY()
        x, y = self._loc_to_xy(x, y)

        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(1)
        self.ctx.arc(x, y, 5, 0, 2 * math.pi)
        self.ctx.fill()
        return x + 10, y - 10

    def add_polygon_gdal(self, polygon, linestyle, color, bgstyle, bgcolor):
        for linestring in polygon:
            for point_no in xrange(linestring.GetPointCount()):
                self._add_linestring_gdal(linestring, linestyle, color, bgstyle, bgcolor)

        self._set_bgstyle(self.ctx, bgstyle, bgcolor)
        self.ctx.fill_preserve()

        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(1)
        if linestyle == '--':
            self.ctx.set_dash([5, 5], 1)
        else:
            self.ctx.set_dash([], 0)
        self.ctx.stroke()

        centroid = polygon.Centroid()
        return self._loc_to_xy(centroid.GetX(), centroid.GetY())

    def add_legend(self, legend, linestyle, color, bgstyle, bgcolor):
        if legend is None:
            return
        legends = [_legend[0] for _legend in self.legends]
        if legend not in legends:
            self.legends.append((legend, linestyle, color, bgstyle, bgcolor))

    def _add_label(self, x, y, label, color):
        if label is not None:
            xbearing, ybearing, _width, _height, xadvance, yadvance = \
                self.ctx.text_extents(label)
            self.ctx.set_source_rgba(*color)
            self.ctx.move_to(x - _width / 2, y - _height / 2)
            self.ctx.show_text(label)

    def plot_geom(self, geom, label, legend=None, linestyle='-', bgstyle=None, color=(1, 0, 0, 1), bgcolor=(0, 0, 0, 0)):
        if not isinstance(geom, ogr.Geometry):
            raise NotImplementedError()

        if not geom.GetGeometryType() in (ogr.wkbPolygon, ogr.wkbLineString, ogr.wkbPoint,
                                          ogr.wkbMultiPolygon, ogr.wkbMultiLineString, ogr.wkbMultiPoint):
            raise NotImplementedError()

        self.add_legend(legend, linestyle, color, bgstyle, bgcolor)

        # Mono part geometries
        if geom.GetGeometryType() == ogr.wkbPolygon:
            x, y = self.add_polygon_gdal(geom, linestyle, color, bgstyle, bgcolor)
            self._add_label(x, y, label, color)
        elif geom.GetGeometryType() == ogr.wkbLineString:
            x, y = self.add_linestring_gdal(geom, linestyle, color, bgstyle, bgcolor)
            self._add_label(x, y, label, color)
        elif geom.GetGeometryType() == ogr.wkbPoint:
            x, y = self.add_point_gdal(geom, linestyle, color, bgstyle, bgcolor)
            self._add_label(x, y, label, color)
        else:
            # Multi part geometries
            for obj in geom:
                if geom.GetGeometryType() == ogr.wkbMultiPolygon:
                    x, y = self.add_polygon_gdal(obj, linestyle, color, bgstyle, bgcolor)
                elif geom.GetGeometryType() == ogr.wkbMultiLineString:
                    x, y = self.add_linestring_gdal(obj, linestyle, color, bgstyle, bgcolor)
                elif geom.GetGeometryType() == ogr.wkbMultiPoint:
                    x, y = self.add_point_gdal(obj, linestyle, color, bgstyle, bgcolor)
                self._add_label(x, y, label, color)

    def plot_legend(self):
        """Plot the map legend. The legend entries are gathered during
        plot_geom() calls."""
        if len(self.legends) == 0:
            return
        OFFSET = (10, 10)
        BORDER = (10, 10)
        SYMBOL = (40, 10)
        width = self.width
        height = self.height
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        legend_width = 0
        legend_height = BORDER[1]

        # Legend text
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_font_size(15)
        for legend_no, legend in enumerate(self.legends):
            text, linestyle, color, bgstyle, bgcolor = legend
            xbearing, ybearing, _width, _height, xadvance, yadvance = \
                ctx.text_extents(text)

            legend_height += _height + BORDER[1]
            if legend_width < _width:
                legend_width = _width

            # Draw legend text
            ctx.set_source_rgb(0, 0, 0)
            ctx.move_to(OFFSET[0] + BORDER[0] * 2 + SYMBOL[0], height - legend_height)
            ctx.show_text(text)

            # Draw legend symbol
            if linestyle != '_':
                ctx.set_line_width(1)
                ctx.rectangle(OFFSET[0] + BORDER[0], height - legend_height - _height, SYMBOL[0], SYMBOL[1])

            if bgcolor is not None:
                self._set_bgstyle(ctx, bgstyle, bgcolor)
                ctx.fill_preserve()
            ctx.set_source_rgba(*color)

            if linestyle == '--':
                ctx.set_dash([5, 5], 1)
            else:
                ctx.set_dash([], 0)

            if linestyle == '_':
                ctx.set_line_width(3)
                ctx.move_to(OFFSET[0] + BORDER[0], height - legend_height - (_height / 2))
                ctx.line_to(OFFSET[0] + BORDER[0] + SYMBOL[0], height - legend_height - (_height / 2))

            ctx.stroke()

        ctx.set_line_width(1)

        # Add the "Legend" title
        xbearing, ybearing, _width, _height, xadvance, yadvance = \
            ctx.text_extents(u"Légende")
        if legend_width < _width:
            legend_width = _width
        legend_height += _height + BORDER[1]
        ctx.set_source_rgb(0, 0, 0)
        ctx.move_to(OFFSET[0] + BORDER[0] * 2 + SYMBOL[0], height - legend_height)
        ctx.show_text(u"Legend")

        # Black line border
        self.ctx.rectangle(OFFSET[0], height - legend_height - OFFSET[1] - BORDER[1], legend_width + 3 * BORDER[0] + SYMBOL[0], legend_height)
        self.ctx.set_source_rgb(1, 1, 1)
        self.ctx.fill_preserve()
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.set_dash([], 0)
        self.ctx.stroke()

        self.ctx.set_source_surface(surface)
        self.ctx.paint()

        # Add OpenStreetMap copyright
        if self.has_bg and self.provider == 'OPENSTREETMAP':
            text = u'© OpenStreetMap'
            self.ctx.set_font_size(10)
            xbearing, ybearing, width, height, xadvance, yadvance = \
                self.ctx.text_extents(text)

            # Draw legend text
            self.ctx.set_source_rgb(0, 0, 0)
            self.ctx.move_to(self.width - width - height, self.height - (2 * height))
            self.ctx.show_text(text)
            self.ctx.stroke()

    def plot_compass(self):
        self.plot_image('map/resources/compass.png', self.width - 100, 20)

    def plot_image(self, tryton_filename, x, y):
        img = file_open(tryton_filename, 'rb')
        surface = cairo.ImageSurface.create_from_png(img)
        self.ctx.set_source_surface(surface, x, y)
        self.ctx.paint()

    def plot_scaling(self):
        line = ogr.Geometry(ogr.wkbLineString)
        line.AddPoint_2D(self.ll[0], self.ll[1])
        line.AddPoint_2D(self.ll[0] + 0.1, self.ll[1])
        src = osr.SpatialReference()
        src.SetWellKnownGeogCS("EPSG:4326")
        line.AssignSpatialReference(src)
        dst = osr.SpatialReference()
        dst.ImportFromEPSG(2154)
        line.TransformTo(dst)

        px1, _ = self._loc_to_xy(self.ll[0], self.ll[1])
        px2, _ = self._loc_to_xy(self.ll[0] + 0.1, self.ll[1])

        # Length of one meter in pixel
        px_meter = float(px2 - px1) / line.Length()

        factor = 1
        while True:
            # scale_m = [1, 2, 3.., 8, 9, 10, 20, 30..., 90, 100, 200, 300...]
            scale_m = float(10 ** (factor / 10) * (factor % 10))
            scale_px = int(scale_m * px_meter)
            if scale_px > 100:
                break

            factor += 1

        if scale_m >= 1000.0:
            label = '%01.1fkm' % (scale_m / 1000.0)
        else:
            label = '%im' % scale_m

        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.set_line_width(1)

        # Position of the 0
        x = self.width / 2.0 - scale_px / 2.0
        y = self.height - 20
        self.ctx.move_to(x, y - 5)
        self.ctx.line_to(x, y)
        self.ctx.line_to(x + scale_px, y)
        self.ctx.line_to(x + scale_px, y - 5)
        self.ctx.set_font_size(10)
        xbearing, ybearing, _width, _height, xadvance, yadvance = \
            self.ctx.text_extents('0')
        self.ctx.move_to(x - _width / 2, y - 5 - _height)
        self.ctx.show_text('0')
        xbearing, ybearing, _width, _height, xadvance, yadvance = \
            self.ctx.text_extents(label)
        self.ctx.move_to(x + scale_px - _width / 2, y - 5 - _height)
        self.ctx.show_text(label)
        self.ctx.stroke()

    def plot_title(self, title):
        """Plot the map title"""
        OFFSET = (10, 10)
        BORDER = (10, 10)
        width = self.width
        height = self.height
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        title_width = 0
        title_height = BORDER[1]

        # Title text
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_font_size(15)
        for line_no, line in enumerate(title.splitlines()):
            xbearing, ybearing, _width, _height, xadvance, yadvance = \
                ctx.text_extents(line)

            if title_width < _width:
                title_width = _width

            # Draw title text
            ctx.set_source_rgb(0, 0, 0)
            ctx.move_to(OFFSET[0] + BORDER[0],
                        OFFSET[1] + BORDER[1] + title_height)
            title_height += _height + BORDER[1]
            ctx.show_text(line)

        # Black line border
        self.ctx.rectangle(OFFSET[0],
                           OFFSET[1],
                           title_width + BORDER[0] * 2,
                           title_height)
        self.ctx.set_source_rgb(1, 1, 1)
        self.ctx.fill_preserve()
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.set_dash([], 0)
        self.ctx.stroke()

        self.ctx.set_source_surface(surface)
        self.ctx.paint()

    def save(self, filename):
        img = self.render()
        fp = open(filename, 'wb')
        fp.write(img)
        fp.close()

    def render(self):
        fp = StringIO()
        self.surface.write_to_png(fp)
        fp.seek(0)
        if self.img_format == 'PNG':
            img = fp.read()
        else:
            jpg = Image.open(fp)
            img = StringIO()
            jpg.save(img, 'JPEG')
            img.seek(0)
            img = img.read()
        return img
