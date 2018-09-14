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

from trytond.transaction import Transaction
from trytond.application import app

from trytond.protocols.wrappers import with_pool, with_transaction, \
        user_application

from .wfs import WfsRequest

logger = logging.getLogger(__name__)

wfs_application = user_application('wfs')

@app.route('/<database_name>/wfs', methods=['GET', 'POST'])
@with_pool
@with_transaction()
@wfs_application
def wfs(request, pool):
    print("ARGS REQUEST", request.args)
    begin = time.time()
    req = WfsRequest()
    User = pool.get('res.user')
    user = User(Transaction().user)
    try:
        ret = req.handle(**request.args)
    except Exception:
        logger.exception('Wfs request failure')
        ret = req.format_exc()
    logger.debug('WFS request handled in %0.1fs', (time.time() - begin))
    return ret

