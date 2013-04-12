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

import sys
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import pango
    import gtk
    import gtk.glade
except:
    sys.exit(1)

import globals
import filehash
import time
import thread
import messagebox
import aboutbox
import locale
import log
import os
import subprocess
import imageaction
import gettext
from gettext import gettext as _


class main_window:
    drop_targets = [('text/plain', 0, 3), ]
    def __init__(self, parameter):
        
        # Localization
        locale.setlocale(locale.LC_ALL, '')
        gettext.textdomain(globals.assembly_name)
        gettext.bindtextdomain(globals.assembly_name, globals.locale_directory)

        #Set the Glade file
        self.interface = gtk.glade.XML(globals.application_interface, 'main_window')
        self.create_settings_directory()
        self.create_settings_file()
        log.write(globals.mount_log, _('Application started...'))
        self.set_storage_lists()
        self.set_history_entry()
        self.set_mounted_image_treeview()
        self.set_icons_and_text()
        self.load_mount_history()
        self.load_previously_mounted_images()

        HANDLERS_AND_METHODS = {
            'button_checksum_clicked': self.button_checksum_clicked,
            'button_browse_clicked': self.button_browse_clicked,
            'button_about_clicked': self.button_about_clicked,
            'button_view_log_clicked': self.button_view_log_clicked,
            'button_delete_log_clicked': self.button_delete_log_clicked,
            'button_mount_clicked': self.button_mount_clicked,
            'comboentry_image_key_release': self.comboentry_image_key_release,
            'comboentry_image_changed': self.comboentry_image_changed,
            'treeview_mounted_images_cursor_changed': self.treeview_mounted_images_cursor_changed,
            'button_unmount_clicked': self.button_unmount_clicked,
            'button_burn_clicked': self.button_burn_clicked,
            'treeview_mounted_images_drag_data_recieved': self.treeview_mounted_images_drag_data_recieved,
            'treeview_mounted_images_row_activated': self.treeview_mounted_images_row_activated,
            'destroy': self.destroy}
        self.interface.signal_autoconnect(HANDLERS_AND_METHODS)
        if (parameter != ''):
            try:
                imageaction.mount(parameter, self.image_storage, self.history_storage, self.history_array, self.interface.get_widget('radiobutton_fuse').get_active())
            except OSError, (errno, strerror):
                messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nOS error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
            except IOError, (errno, strerror):
                messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nIO error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
            except:
                messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nUnexpected error: %s' % (sys.exc_info()[0])), gtk.MESSAGE_ERROR)
        
    def load_previously_mounted_images(self):
        if os.path.exists(globals.mount_list):
            try:
                file_previous_images = open(globals.mount_list, 'rU')
                previous_image_history = file_previous_images.readlines()
                for line in previous_image_history:
                    previous_image = line.strip().split(',')
                    self.image_storage.append([previous_image[0], previous_image[1], previous_image[2]])
                os.remove(globals.mount_list)
            except IOError, (errno, strerror):
                log.write(globals.mount_log, _('Error loading history.\nOS error(%s): %s' % (errno, strerror)))
            except:
                log.write(globals.mount_log, _('Error loading history.\nUnexpected error: %s' % (sys.exc_info()[0])))
            finally:
                file_previous_images.close()

    def load_mount_history(self):
        self.history_array = []
        #Load the history
        if os.path.exists(globals.history_list):
            try:
                file_history = open(globals.history_list, 'rU')
                self.mount_history = file_history.readlines()
                for line in self.mount_history:
                    self.history_storage.append([line.strip()])
                    self.history_array.append(line.strip())
            except IOError, (errno, strerror):
                log.write(globals.mount_log, _('Error loading history.\nOS error(%s): %s' % (errno, strerror)))
            except:
                log.write(globals.mount_log, _('Error loading history.\nUnexpected error: %s' % (sys.exc_info()[0])))
            finally:
                file_history.close()

    def create_settings_directory(self):

        #Create settings directory if not present
        if not os.path.exists(globals.settings_directory):
            try:
                os.mkdir(globals.settings_directory)
            except OSError, (errno, strerror):
                messagebox.show(self.interface.get_widget('main_window'), _('Error creating settings directory.\nOS error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
            except IOError, (errno, strerror):
                messagebox.show(self.interface.get_widget('main_window'), _('Error creating settings directory.\nIO error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
            except:
                messagebox.show(self.interface.get_widget('main_window'), _('Error creating settings directory.\nUnexpected error: %s' % (sys.exc_info()[0])), gtk.MESSAGE_ERROR)

    def create_settings_file(self):
        
        #Create the setting file if it doesn't exist
        if not os.path.exists(globals.settings_file):
            try:
                settings_object = open(globals.settings_file, 'w')
                mount_point_setting = '[mount_options]\nmount_point: %s' % globals.home_directory
                settings_object.write(mount_point_setting);
                log.write(globals.mount_log, _('New settings file created at %s' % globals.settings_file))
            except OSError, (errno, strerror):
                messagebox.show(self.interface.get_widget('main_window'), _('Error creating settings file.\nOS error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
            except IOError, (errno, strerror):
                messagebox.show(self.interface.get_widget('main_window'), _('Error creating settings file.\nIO error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
            except:
                messagebox.show(self.interface.get_widget('main_window'), _('Error creating settings file.\nUnexpected error: %s' % (sys.exc_info()[0])), gtk.MESSAGE_ERROR)
            finally:
                settings_object.close( )
    
    def set_icons_and_text(self):

        #Set the Icons and Text
        self.interface.get_widget('main_window').set_title('%s %s' % (globals.assembly_title, globals.assembly_version))
        #Allowbutton imagestobe shown
        gtk_settings = self.interface.get_widget('main_window').get_settings()
        gtk_settings.set_property("gtk-button-images", True)
        self.browse_button_image = gtk.Image()
        self.browse_button_image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU)
        self.interface.get_widget('button_browse').set_image(self.browse_button_image)
        self.interface.get_widget('button_browse').set_label(_('_Browse...'))
        self.button_mount_image = gtk.Image()
        self.button_mount_image.set_from_stock("gtk-harddisk", gtk.ICON_SIZE_MENU)
        self.interface.get_widget('button_mount').set_image(self.button_mount_image)
        self.interface.get_widget('button_mount').set_label(_('_Mount'))
        self.button_checksum_image = gtk.Image()
        self.button_checksum_image.set_from_file(globals.image_checksum_button)
        self.interface.get_widget('button_checksum').set_image(self.button_checksum_image)
        self.interface.get_widget('button_checksum').set_label(_('_Checksum'))
        self.button_burn_image = gtk.Image()
        self.button_burn_image.set_from_file(globals.image_burn_button)
        self.interface.get_widget('button_burn').set_image(self.button_burn_image)
        self.interface.get_widget('button_burn').set_label(_('Bur_n'))
        self.button_unmount_image = gtk.Image()
        self.button_unmount_image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        self.interface.get_widget('button_unmount').set_image(self.button_unmount_image)
        self.interface.get_widget('button_unmount').set_label(_('_Unmount'))
        self.interface.get_widget('button_view_log').set_label(_('View Log'))
        self.interface.get_widget('button_delete_log').set_label(_('Delete Log'))
        self.interface.get_widget('label_select_image').set_label(_('Select Image'))
        self.interface.get_widget('label_selected_image').set_label(_('No Image Selected'))
        self.interface.get_widget('label_selected_image').modify_font(pango.FontDescription('8'))
        self.interface.get_widget('progressbar_hash').set_text(_('No Checksum Generated'))
        self.interface.get_widget('progressbar_hash').modify_font(pango.FontDescription('8'))
        self.interface.get_widget('label_selected_mount_point').set_label(_('No Mount Point Selected'))
        self.interface.get_widget('label_selected_mount_point').modify_font(pango.FontDescription('8'))
        self.interface.get_widget('frame_mounted_images').set_label(_('Mounted Images:'))
        self.interface.get_widget('label_drag_prompt').set_label(_('Drag image files into above window to quickly mount'))
        self.interface.get_widget('label_drag_prompt').modify_font(pango.FontDescription('8'))

    def set_mounted_image_treeview(self):

        #Set treeview for images
        self.treeview = self.interface.get_widget('treeview_mounted_images')
        self.treeview.modify_font(pango.FontDescription('sans 8'))
        self.treeview.set_model(self.image_storage)
        #Create columns
        self.column_mount_point = gtk.TreeViewColumn(_('Mount Point'), gtk.CellRendererText(), text=0)
        self.column_image_file = gtk.TreeViewColumn(_('Image File'), gtk.CellRendererText(), text=1)
        self.column_fuse = gtk.TreeViewColumn('Fuse', gtk.CellRendererText(), text=2)
        #Add sorting
        self.column_mount_point.set_sort_column_id(0)
        self.column_image_file.set_sort_column_id(1)
        #Append columns
        self.treeview.append_column(self.column_mount_point)
        self.treeview.append_column(self.column_image_file)
        self.treeview.append_column(self.column_fuse)
        #Set Drag n Drop
        self.treeview.drag_dest_set(gtk.DEST_DEFAULT_ALL, self.drop_targets, gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY)

    def set_history_entry(self):
        #set entry for history
        self.interface.get_widget('comboentry_image').set_model(self.history_storage)
        self.interface.get_widget('comboentry_image').set_text_column(0)

    def set_storage_lists(self):
        #Set storage
        self.image_storage = gtk.ListStore(str, str, str) #Mounted image storage
        self.history_storage = gtk.ListStore(str)

    def comboentry_image_key_release(self, data, event):
        key = gtk.gdk.keyval_name (event.keyval)
        if key == 'Return':
            self.verify_image()

    def comboentry_image_changed(self, data):
        if self.interface.get_widget('comboentry_image').get_active() != -1:
            self.verify_image()

    def button_browse_clicked(self, data):
        self.select_and_verify_image()

    def button_checksum_clicked(self, data):
        # Compute the checksum on an independent thread
        self.abort = False
        if self.interface.get_widget('button_checksum').get_label() == _('_Checksum'):
            selected_image = self.interface.get_widget('label_selected_image').get_label()
            self.interface.get_widget('button_checksum').set_label(_('_Cancel'))

            gtk_iteration()
            checksum = filehash.checksum()
            log.write(globals.mount_log, _('Checksum generation started...'))
            if self.interface.get_widget('radiobutton_md5').get_active():
                thread.start_new_thread(checksum.computemd5, (selected_image,))
            else:
                thread.start_new_thread(checksum.computesha1, (selected_image,))

            while checksum.hash == _('Calculating, please wait...'):
                if self.abort:
                    self.interface.get_widget('progressbar_hash').set_text(_('No Checksum Generated'))
                    self.interface.get_widget('progressbar_hash').set_fraction(0)
                    break
                gtk_iteration()
                time.sleep(0.1)
                self.interface.get_widget('progressbar_hash').set_fraction(checksum.progress)
                self.interface.get_widget('progressbar_hash').set_text(checksum.hash)
            if not self.abort:
                log.write(globals.mount_log, _('%s:%s' % (selected_image, checksum.hash)))
        else: # Cancel
            self.abort = True
            log.write(globals.mount_log, _('Checksum generation aborted!'))
        self.interface.get_widget('button_checksum').set_label(_('_Checksum'))

    def select_and_verify_image(self):
        if self.select_image():
            self.verify_image()

    def select_image(self):
        is_file_selected = False
        dialog = gtk.FileChooserDialog(_('Open Image..'),
                       None,
                       gtk.FILE_CHOOSER_ACTION_OPEN,
                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.interface.get_widget('comboentry_image').child.set_text(dialog.get_filename())
            is_file_selected = True
        dialog.destroy()
        return is_file_selected

    def verify_image(self, image=''):
        if image == '':
            selected_file = self.interface.get_widget('comboentry_image').get_active_text()
        else:
            selected_file = image
        # First, ensure that the file exists
        if not os.path.exists(selected_file):
            messagebox.show(self.interface.get_widget('main_window'), _('File not found. \nPlease check source exists.'), gtk.MESSAGE_ERROR)
            self.interface.get_widget('label_selected_image').set_label(_('No Image Selected'))
            self.interface.get_widget('button_mount').set_sensitive(False)
            self.interface.get_widget('button_checksum').set_sensitive(False)
            self.interface.get_widget('button_burn').set_sensitive(False)
            return False
        # Next, ensure it's a supported image
        if selected_file.lower().endswith('.iso') | selected_file.lower().endswith('.img') | selected_file.lower().endswith('.bin') | selected_file.lower().endswith('.mdf') | selected_file.lower().endswith('.nrg'):
            self.interface.get_widget('label_selected_image').set_label(selected_file)
            self.interface.get_widget('button_mount').set_sensitive(True)
            self.interface.get_widget('button_checksum').set_sensitive(True)
            self.interface.get_widget('button_burn').set_sensitive(True)
            # Loop method only supports ISO and IMG, so...
            if selected_file.lower().endswith('.iso') | selected_file.lower().endswith('.img'):
                self.interface.get_widget('radiobutton_loop').set_sensitive(True)
            else:
                self.interface.get_widget('radiobutton_loop').set_sensitive(False)
                self.interface.get_widget('radiobutton_fuse').set_active(True)
            return True
        messagebox.show(self.interface.get_widget('main_window'), _('File does not appear to be a compatible Image. \nPlease check source.'), gtk.MESSAGE_ERROR)
        self.interface.get_widget('label_selected_image').set_label(_('No Image Selected'))
        self.interface.get_widget('button_mount').set_sensitive(False)
        self.interface.get_widget('button_checksum').set_sensitive(False)
        self.interface.get_widget('button_burn').set_sensitive(False)
        return False

    def button_view_log_clicked(self, data):
        if os.path.exists(globals.mount_log):
            subprocess.Popen(['gnome-text-editor', globals.mount_log])
        else:
            messagebox.show(self.interface.get_widget('main_window'), _('%s not found.' % (globals.mount_log)))

    def button_delete_log_clicked(self, data):
        if os.path.exists(globals.mount_log):
            if messagebox.show(self.interface.get_widget('main_window'), _('Are you sure you wish to delete the log?'), gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO) == gtk.RESPONSE_YES:
                try:
                    os.remove(globals.mount_log)
                except IOError, (errno, strerror):
                    log.write(globals.mount_log, _('Error deleting log.\nOS error(%s): %s' % (errno, strerror)))
                except OSError, (errno, strerror):
                    log.write(globals.mount_log, _('Error deleting log.\nOS error(%s): %s' % (errno, strerror)))
                except:
                    log.write(globals.mount_log, _('Error deleting log.\nUnexpected error: %s' % (sys.exc_info()[0])))

    def button_mount_clicked(self, data):
        try:
            imageaction.mount(self.interface.get_widget('label_selected_image').get_label(), self.image_storage, self.history_storage, self.history_array, self.interface.get_widget('radiobutton_fuse').get_active())
        except OSError, (errno, strerror):
            messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nOS error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
        except IOError, (errno, strerror):
            messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nIO error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
        except:
            messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nUnexpected error: %s' % (sys.exc_info()[0])), gtk.MESSAGE_ERROR)

    def treeview_mounted_images_cursor_changed(self, data):
        #First get the tree view selection
        self.mounted_image_selection = self.treeview.get_selection()
        #Get the TreeModel and TreeIter of our selection
        (self.model, self.iter) = self.mounted_image_selection.get_selected()
        self.interface.get_widget('label_selected_mount_point').set_label(self.model.get_value(self.iter, 0))
        self.is_mounted_image_fuse = self.model.get_value(self.iter, 2)
        #Allow user to unmount
        self.interface.get_widget('button_unmount').set_sensitive(True)

    def button_unmount_clicked(self, data):
        try:
            imageaction.unmount(self.interface.get_widget('label_selected_mount_point').get_label(), self.is_mounted_image_fuse, self.image_storage, self.iter)
            self.interface.get_widget('label_selected_mount_point').set_label(_('No Mount Point Selected'))
            self.interface.get_widget('button_unmount').set_sensitive(False)
        except:
            messagebox.show(self.interface.get_widget('main_window'), _('Error unmounting image.\nUnexpected error: %s' % (sys.exc_info()[0])), gtk.MESSAGE_ERROR)

    def button_burn_clicked(self, data):
        try:
            imageaction.burn(self.interface.get_widget('label_selected_image').get_label(), self.interface.get_widget('radiobutton_brasero').get_active())
        except:
            messagebox.show(self.interface.get_widget('main_window'), _('Error burning image.\nUnexpected error: %s' % (sys.exc_info()[0])), gtk.MESSAGE_ERROR)

    def button_about_clicked(self, data):
        aboutbox.show(self.interface.get_widget('main_window'))

    def treeview_mounted_images_drag_data_recieved(self, widget, context, x, y, sel, ttype, time):
        files = sel.data.split('\n')
        for file in files:
            if not file:
                continue

            file = file.strip()
            file = file.replace('%20', ' ')
            if file.startswith('file:///') and os.path.isfile(file[7:]):
                if self.verify_image(file[7:]):
                    try:
                        imageaction.mount(self.interface.get_widget('label_selected_image').get_label(), self.image_storage, self.history_storage, self.history_array, self.interface.get_widget('radiobutton_fuse').get_active())
                    except OSError, (errno, strerror):
                        messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nOS error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
                    except IOError, (errno, strerror):
                        messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nIO error(%s): %s' % (errno, strerror)), gtk.MESSAGE_ERROR)
                    except:
                        messagebox.show(self.interface.get_widget('main_window'), _('Error mounting image.\nUnexpected error: %s' % (sys.exc_info()[0])), gtk.MESSAGE_ERROR)

    def treeview_mounted_images_row_activated(self, path, view_column, user_param1):
        imageaction.browse(self.interface.get_widget('label_selected_mount_point').get_label())

    def destroy(self, data):
        self.image_storage.foreach(self.clean_up)
        log.write(globals.mount_log, _('Application closed!'))
        gtk.main_quit()

    def clean_up(self, model, path, iter):
        if messagebox.show(self.interface.get_widget('main_window'), _('%s is still mounted.\nDo you wish to unmount it before exiting?' % (model.get_value(iter, 1))), gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO) == gtk.RESPONSE_YES:
            try:
                imageaction.unmount(model.get_value(iter, 0), model.get_value(iter, 2), self.image_storage, iter, True)
            except:
                log.write(globals.mount_log, _('Error unmounting image.\nUnexpected error: %s' % (sys.exc_info()[0])))
        else: #write the history to file for loading later
            try:
                mount_file = open(globals.mount_list, 'a')
                string = '%s,%s,%s' % (model.get_value(iter, 0), model.get_value(iter, 1), model.get_value(iter, 2))
                mount_file.write('%s\n' % (string))
            except IOError, (errno, strerror):
                log.write(globals.mount_log, _('Error saving unmounted images to file.\nOS error(%s): %s' % (errno, strerror)))
            except:
                log.write(globals.mount_log, _('Error saving unmounted images to file\nUnexpected error: %s' % (sys.exc_info()[0])))
            finally:
                mount_file.close()
        return False

def gtk_iteration():
    while gtk.events_pending():
        gtk.main_iteration(False)

if __name__ == '__main__':
    parameter = ''
    if len(sys.argv) > 1:
        parameter = sys.argv[1]
    app = main_window(parameter)
    gtk.main()
