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
import collections

from osgeo import ogr, osr

ogr.UseExceptions()


def check_envelope(env):
    """
    Check envelope / bounding box
    An envelope is composed of 2 points (x1,x2,y1,y2) and x != y.
    """
    if (not isinstance(env, collections.Sequence) or len(env) != 4 or
            env[0] == env[1] or env[2] == env[3]):
        raise ValueError('Invalid envelope: %r', env)


def envelope_union(env1, env2):
    if env1 is None:
        raise ValueError('env1')
    if env2 is None:
        return env1

    env = [
        min(env1[0], env2[0]),
        max(env1[1], env2[1]),
        min(env1[2], env2[2]),
        max(env1[3], env2[3]),
    ]
    return env


def bbox_aspect(env, width, height):
    check_envelope(env)
    env_aspect = (env[1] - env[0]) / (env[3] - env[2])
    aspect = float(width) / float(height)

    if env_aspect > aspect:
        dx = env[1] - env[0]
        dy = dx / aspect
    else:
        dy = env[3] - env[2]
        dx = dy * aspect

    _env = []
    _env += [env[0] + ((env[1] - env[0]) / 2.0) - dx / 2.0]
    _env += [_env[0] + dx]
    _env += [env[2] + ((env[3] - env[2]) / 2) - dy / 2.0]
    _env += [_env[2] + dy]
    return _env


def get_as_epsg4326(records):
    _records = []
    src = None
    dst = osr.SpatialReference()
    dst.SetWellKnownGeogCS("EPSG:4326")
    area = 0
    envelope = None
    for record in records:
        if record is None:
            continue
        geo = ogr.CreateGeometryFromWkt(record.wkt)
        if src is None:
            src = osr.SpatialReference()
            src.ImportFromEPSG(record.srid)
        if geo.GetGeometryType() == ogr.wkbMultiPolygon:
            area += int(geo.GetArea())
        geo.AssignSpatialReference(src)
        geo.TransformTo(dst)
        envelope = envelope_union(geo.GetEnvelope(), envelope)
        _records.append(geo)
    return _records, envelope, area


def osr_geo_from_field(geo_field):
    geo = ogr.CreateGeometryFromWkt(geo_field.wkt)
    srs = geo_field.srid
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(geo_field.srid)
    geo.AssignSpatialReference(srs)
    return geo
