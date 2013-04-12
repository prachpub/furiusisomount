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

import gtk
import os.path
import globals
from gettext import gettext as _


def show(parent) :
    """
        Show an about dialog box
    """
    dlg = gtk.AboutDialog()
    dlg.set_transient_for(parent)

    # Set credit information
    dlg.set_name(globals.assembly_title)
    dlg.set_version(globals.assembly_version)
    dlg.set_website(globals.assembly_website)
    dlg.set_translator_credits(_('''translator-credits
        Bulgarian (bg): Svetoslav Stefanov
        Chinese (Simplified) (zh_CN): XsLiDian
        Dutch (nl): Dirk Roos
        French (f): bouchard renaud, peterl
        German (de): Klaus Riesterer
        Hunsrik (hrx): Adriano Steffler
        Italian (it): Christos Spyroglou
        Greek (el):  Christos Spyroglou
        Italian (it): Christos Spyroglou
        Japanese (ja): YAMAKAGE Hideo
        Polish (pl): It's Easy
        Portuguese (pt): Celso Henriques
        Russian (ru): Alexey Ivanes
        Spanish (es): Adrián García
        Swedish (sv): Anders Pamdal
        Turkish (tr): Emre AYTAÇ'''))
    dlg.set_comments(globals.assembly_description)
    

    dlg.set_authors([
        _('Developer:'),
        'Dean Harris <marcus_furius@hotmail.com>',
    ])

    # Set logo
    if os.path.exists(globals.about_image) :
        dlg.set_logo(gtk.gdk.pixbuf_new_from_file(globals.about_image))

    # Load the licence from the disk if possible
    if os.path.exists(globals.glp_license) :
        dlg.set_license(open(globals.glp_license).read())
        dlg.set_wrap_license(True)

    dlg.run()
    dlg.destroy()