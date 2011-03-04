#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
