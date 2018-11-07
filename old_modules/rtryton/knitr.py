
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

from trytond.report import Report
from trytond.pool import  Pool
from .r_tools import dataframe, py2r

from rpy2 import robjects
from collections import namedtuple

import tempfile
import shutil
import stat
import os

FieldInfo = namedtuple('FieldInfo', ['name', 'ttype'])


def add_to_map(ids, model_name, list_map):
    """
    Breadth first search of dependent records,
    this function is called recursively
    ids is a set of ids
    """
    assert(isinstance(ids, set))
    if not ids or model_name[0:4] == 'res.': return False

    added = False

    if model_name not in list_map:
        list_map[model_name] = set(ids)
        added = True
    else:
        old_len = len(list_map[model_name])
        list_map[model_name] = list_map[model_name].union(ids)
        added = len(list_map[model_name]) > old_len

    if not added: return False

    model = Pool().get(model_name)
    for name, ttype in model._fields.iteritems():
        if ttype._type == 'many2one' or ttype._type == 'one2one':
            added |= add_to_map(
                    set([ val[name] for val in model.read(list(ids), [name]) if val[name] ]), 
                    ttype.model_name, list_map)
        elif ttype._type == 'many2many' or ttype._type == 'one2many':
            ido = set()
            for rec in model.read(list(ids), [name]):
                ido = ido.union( set(rec[name]) )
            added |= add_to_map( ido, ttype.get_target().__name__, list_map )
    if not added: 
        return False
    add = False
    for k, i in list_map.iteritems(): 
        if k != model_name: 
            add |= add_to_map(i, k, list_map)
    return True


def save_rdata(ids, model_name, filename):
    """save data from model and one level of joined data (one2one, one2many, many2many and many2one)"""
    
    list_map = {}
    add_to_map( set(ids), model_name, list_map ) 

    df = {}

    tmpdir = os.path.dirname(filename)
    imagedir = tmpdir + "/images"
    os.mkdir(imagedir)

    for mod_name, id_list in list_map.iteritems():
        model = Pool().get(mod_name)
        records = model.search([('id', 'in', list(id_list))])       
        fields_info = [FieldInfo(name, ttype._type)
                           for name,ttype in model._fields.iteritems()
                           if  ttype._type in py2r]

        df[mod_name] = dataframe(records, fields_info)

        print("saving in Rdata: ", mod_name, list(id_list))
        """ save images """        
        for name,ttype in model._fields.iteritems():
            if ttype._type == "binary" and name[-4:] == "_map":

                for record in records:                    
                    value = getattr(record, name)
                    imgpath = os.path.join(imagedir, (str(record)+'_'+name).replace(',','_').replace('.','_')+'.png')
                    print("SAVING ", imgpath)
                    imgfile = open(imgpath,'wb')
                    imgfile.write(value)        

    for mod_name, dfr in df.iteritems():        
        robjects.r.assign(mod_name, dfr)
    robjects.r("save(list=c("+','.join(["'"+mod_name+"'" for mod_name, dfr in df.iteritems()])+
            "), file='"+filename+"')")

class PdfReport(Report):
    __name__ = 'rtryton.pdfreport'

    @classmethod
    def execute(cls, ids, data):

        tmpdir = tempfile.mkdtemp()

        os.chmod(tmpdir, 
                stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IXGRP|stat.S_IRGRP)
        dot_rdata = os.path.join(tmpdir, data['model']+'.Rdata')

        save_rdata(ids, data['model'], dot_rdata)

        ActionReport = Pool().get('ir.action.report')
        action_reports = ActionReport.search([
                ('report_name', '=', cls.__name__)
                ])
        input_file = os.path.join(tmpdir, cls.__name__+'.Rnw')
        output_file = os.path.join(tmpdir, cls.__name__+'.pdf')
        with open(input_file, 'w') as template:
            template.write("<<Initialisation, echo=F, cache=T>>=\n")
            template.write("load('"+dot_rdata+"')\n")
            template.write("opts_knit$set(base.dir = '"+tmpdir+"')\n")
            template.write("@\n\n")
            if action_reports[0].report_content_custom:
                template.write(action_reports[0].report_content_custom)
            else:
                template.write(action_reports[0].report_content)

        robjects.r("setwd('"+tmpdir+"')")
        robjects.r("library('knitr')")
        robjects.r("knit2pdf('"+input_file+"')")

        buf = None
        with open(output_file, 'rb') as out:
            buf = buffer(out.read())

        #shutil.rmtree(tmpdir)
        return ('pdf', 
                buf,
                action_reports[0].direct_print, 
                action_reports[0].name )

class HtmlReport(Report):
    __name__ = 'rtryton.htmlreport'

    @classmethod
    def execute(cls, ids, data):

        tmpdir = tempfile.mkdtemp()
        os.chmod(tmpdir, 
                stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IXGRP|stat.S_IRGRP)
        dot_rdata = os.path.join(tmpdir, data['model']+'.Rdata')
        save_rdata(ids, data['model'], dot_rdata)

        ActionReport = Pool().get('ir.action.report')
        action_reports = ActionReport.search([
                ('report_name', '=', cls.__name__)
                ])

        input_file = os.path.join(tmpdir, cls.__name__+'.Rmd')
        output_file = os.path.join(tmpdir, cls.__name__+'.html')
        with open(input_file, 'w') as template:
            template.write("```{r Initialisation, echo=F, cache=T}\n")
            template.write("load('"+dot_rdata+"')\n")
            template.write("opts_knit$set(base.dir = '"+tmpdir+"')\n")
            template.write("```\n\n")
            if action_reports[0].report_content_custom:
                template.write(action_reports[0].report_content_custom)
            else:
                template.write(action_reports[0].report_content)

        robjects.r("library('knitr')")
        robjects.r("knit2html('"+input_file+"', '"+output_file+"')")

        buf = None
        with open(output_file, 'rb') as out:
            buf = buffer(out.read())

        #shutil.rmtree(tmpdir)
        return ('html', 
                buf,
                action_reports[0].direct_print, 
                action_reports[0].name )
