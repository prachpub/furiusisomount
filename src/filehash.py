#!/usr/bin/env python
# -*- coding: utf-8 -*-
#This file is part of PyFuriusIsoMount. Copyright 2008 Dean Harris (marcus_furius@hotmail.com)
#
#    PyFuriusIsoMount is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    PyFuriusIsoMount is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PyFuriusIsoMount.  If not, see <http://www.gnu.org/licenses/>.

import hashlib
import string
import os
from gettext import gettext as _

class checksum():
    def __init__(self):
        self.hash = _('Calculating, please wait...')
        self.progress = 0.0
    def hexstr(self, s):
        h = string.hexdigits
        r = ''
        for c in s:
            i = ord(c)
            r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
        return r

    def computemd5(self, file, CHUNK=2**16):
        self.hash = _('Calculating, please wait...')
        self.progress = 0.0
        try:
            file_stream = open(file, 'rb')
            hash = hashlib.md5()
            size = os.stat(file).st_size
            total = 0
            while True:
                chunk = file_stream.read(CHUNK)
                if not chunk:
                    break
                hash.update(chunk)
                total += CHUNK
                self.progress = float(total) / float(size)
        finally:
            file_stream.close( )
        self.progress = 1.0
        self.hash =  self.hexstr(hash.digest())

    def computesha1(self, file, CHUNK=2**16):
        self.hash = 'Calculating, please wait...'
        self.progress = 0.0
        try:
            file_stream = open(file, 'rb')
            hash = hashlib.sha1()
            size = os.stat(file).st_size
            total = 0
            while True:
                chunk = file_stream.read(CHUNK)
                if not chunk:
                    break
                hash.update(chunk)
                total += CHUNK
                self.progress = float(total) / float(size)
        finally:
            file_stream.close( )
        self.progress = 1.0
        self.hash = self.hexstr(hash.digest())
