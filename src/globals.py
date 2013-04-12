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

import os.path
from gettext import gettext as _

#Assembly information
assembly_title = _('Furius ISO Mount Tool')
assembly_description = _('''Simple Gtk+ Interface to Mount ISO, IMG, BIN, MDF and NRG Image files without burning to disk.''')
assembly_website = 'https://launchpad.net/furiusisomount/'
assembly_version = '0.11.3.1'
assembly_name = 'furiusisomount'

# Directories
home_directory = os.path.expanduser('~')
settings_directory = os.path.join(home_directory, '.furiusisomount')
source_directory = os.path.join(os.path.dirname(__file__))
resource_directory = os.path.join(source_directory, '..', 'res')
image_directory = os.path.join(source_directory, '..', 'pix')
document_directory = os.path.join(source_directory, '..', 'doc')
locale_directory = os.path.join(source_directory, '..', 'locale')
if not os.path.isdir(locale_directory) :
    locale_directory = os.path.join(source_directory, '..', '..', 'locale')

#files
application_interface = os.path.join(resource_directory, 'main_window.glade')
about_image = os.path.join(image_directory, 'furiusisomount.png')
glp_license = os.path.join(document_directory, 'gpl.txt')
mount_log = os.path.join(settings_directory, 'FuriusMountLog.txt')
mount_list = os.path.join(settings_directory, 'FuriusMountList.csv')
history_list = os.path.join(settings_directory, 'FuriusMountHistory.txt')
image_burn_button = os.path.join(image_directory, 'imageburn.png')
image_checksum_button = os.path.join(image_directory, 'imagechecksum.png')
settings_file = os.path.join(settings_directory, 'settings.cfg')