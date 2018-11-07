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
Copyright (c) 2013 Pierre-Louis Bonicoli

"""

from trytond.pool import Pool

from .data import Data, DataSourceModel, DataSourceScript, Script
from .view import DataView
from .knitr import HtmlReport, PdfReport

def register():
    Pool.register(
        Data, 
        DataSourceModel, 
        Script, 
        DataSourceScript, 
        DataView,
        module='rtryton',
        type_='model'
    )

    Pool.register(
        HtmlReport,
        PdfReport,
        module='rtryton',
        type_='report'
    )

