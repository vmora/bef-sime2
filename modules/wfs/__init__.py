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

import time
import logging
import traceback

from trytond.transaction import Transaction
from trytond.application import app
from trytond.pool import Pool

from trytond.protocols.wrappers import with_pool, with_transaction

from .wfs import WfsRequest

logger = logging.getLogger(__name__)

@app.route('/<string:database_name>/wfs', methods=['GET', 'POST'])
@with_pool
@with_transaction(readonly=False)
def wfs(request, database_name):
    print("###########ARGS REQUEST", database_name, request.args)
    begin = time.time()
    try:
        transaction = Transaction()
        req = WfsRequest()
        print("###########1")
    except Exception:
        print("########### exc")
        traceback.print_exc()
        return None

    #User = pool.get('res.user')
    #user = User(Transaction().user)
    try:
        ret = req.handle(**request.args)
    except Exception:
        logger.exception('Wfs request failure')
        ret = req.format_exc()
    logger.debug('WFS request handled in %0.1fs', (time.time() - begin))
    return ret

