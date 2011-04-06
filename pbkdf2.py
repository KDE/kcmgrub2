#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python pbkdf2 generator
#
# Copyright 2011 Alberto Mattea <alberto@mattea.info>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from math import ceil
from functools import partial
from hashlib import sha512
from hmac import new as hmac
from random import randrange
from binascii import hexlify, unhexlify

def pbkdf2(password, salt=None, dk_length=64, iterations=10000, hashfunc=sha512):
    if salt==None: salt="".join(chr(randrange(0, 256)) for i in xrange(64))
    else: salt=unhexlify(salt)
    digest_size = hashfunc().digest_size
    prf = partial(hmac, digestmod=hashfunc)
    assert dk_length < 2**32 - 1, 'derived key too long'

    l = int(ceil(float(dk_length)/digest_size))

    def xor(a, b):
        return ''.join([chr(ord(x)^ord(y)) for (x, y) in zip(a, b)])

    def i2b(i):
        i = hex(i)[2:]
        i = '0'*(8-len(i)) + i
        return i.decode('hex')

    dk = ''

    for b in xrange(1, l+1):
        u = prf(password, salt + i2b(b)).digest()
        r = u
        for _ in xrange(iterations-1):
            u = prf(password, u).digest()
            r = xor(r, u)
        dk += r

    return hexlify(salt), hexlify(dk[:dk_length])
