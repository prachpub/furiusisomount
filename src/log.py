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

import time
import StringIO

def write(log, message):
    try:
        now = time.asctime(time.localtime())
        log_entry = StringIO.StringIO()
        log_entry.write(' %s\n' %(now))
        log_entry.write('    :\n')
        log_entry.write('    :%s\n' %(message))
        log_entry.write('-------------------------------\n')
        try:
            log_object = open(log, 'a')
            log_object.write(log_entry.getvalue())
        finally:
            log_object.close( )
    finally:
        log_entry.close( )