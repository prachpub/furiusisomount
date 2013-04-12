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

import os
import sys
import globals
import log
import subprocess
from ConfigParser import ConfigParser
from gettext import gettext as _

def mount(image_file, image_storage, history_storage, history_array, is_fuse):
    image_name = os.path.basename(image_file)
    
    #Get the mount root point
    config = ConfigParser()
    try:
        config.read(globals.settings_file)
        mount_root = config.get("mount_options", "mount_point")
    except:
        log.write(globals.mount_log, _('Error mounting image.\nUnexpected error: %s' % (sys.exc_info()[0])))
        log.write(globals.mount_log, _('Defaulting to home directory for mounting.'))
        mount_root = globals.home_directory
    #Replace any characters that could screw us up.
    mount_location = os.path.join(mount_root, image_name.replace(' ', '_'))
    mount_location = mount_location.replace('.', '_')

    try:
        # If an image is already mounted this will throw an IOError
        if os.path.exists(mount_location):
            os.rmdir(mount_location)
        os.mkdir(mount_location)
        if is_fuse:
            #Mount the image, writing the executed command to the log
            mount_command = "fuseiso '%s' '%s'" % (image_file, mount_location)
            log.write(globals.mount_log, mount_command)
            try:
                mount_process = subprocess.Popen(mount_command, shell=True)
                #Write an entry with instructions on how to remove manually if needed
                log.write(globals.mount_log,
                          _('%s successfully mounted @ %s. If required, run the following commands to remove:\n  :fusermount -u %s\n  :rmdir %s'
                            %(image_file, mount_location, mount_location, mount_location)))
            except:
                log.write(globals.mount_log, _('Error mounting image.\nUnexpected error: %s' % (sys.exc_info()[0])))
                raise
        else: #loop back
            mount_command = "gksu -u root \"mount -t auto -o loop '%s' '%s'\"" % (image_file, mount_location)
            log.write(globals.mount_log, mount_command)
            try:
                mount_process = subprocess.Popen(mount_command, shell=True)
                log.write(globals.mount_log,
                          _('%s successfully mounted @ %s. If required, run the following commands to remove:\n  :gksu -u root umount %s\n  :rmdir %s'
                            %(image_file, mount_location, mount_location, mount_location)))
            except:
                log.write(globals.mount_log, _('Error mounting image.\nUnexpected error: %s' % (sys.exc_info()[0])))
                raise
        # Add mount point and image to image_storage
        image_storage.append([mount_location, image_file, str(is_fuse)])
        # Add the image to the history_storage
        add_item_to_history(image_file, history_storage, history_array)
    except IOError, (errno, strerror):
        log.write(globals.mount_log, _('Error mounting image.\nOS error(%s): %s' % (errno, strerror)))
        raise
    except:
        log.write(globals.mount_log, _('Error mounting image.\nUnexpected error: %s' % (sys.exc_info()[0])))
        raise


def add_item_to_history(image_file, history_storage, history_array):
    #Clear the history_storage
    history_storage.clear()
    # If the image already exists in the list, remove it. We'll be adding it
    # to the top of the list.
    for string in history_array:
        if string == image_file:
            history_array.remove(string)
    # Add the image to the top
    history_array.insert(0, image_file)
    # If we've hit our history length max drop the last entry
    if len(history_array) > 10:
        history_array.remove(history_array[10])
    # Rebuild the storage
    try:
        history_file = open(globals.history_list, 'w')
        for string in history_array:
            history_storage.append([string])
            history_file.write('%s\n' %(string))
    except IOError, (errno, strerror):
        log.write(globals.mount_log, _('Error saving history to file.\nOS error(%s): %s' % (errno, strerror)))
        raise
    except:
        log.write(globals.mount_log, _('Error saving history to file\nUnexpected error: %s' % (sys.exc_info()[0])))
        raise
    finally:
        history_file.close( )

def unmount(mount_location, is_mounted_image_fuse, image_storage, iter, is_shutdown = False):
    # If the directory doesn't exist, it may have been
    # unmounted externally so just remove the TreeIter
    # from the TreeStore
    try:
        if os.path.exists(mount_location):
            if is_mounted_image_fuse == 'True':
                unmount_command = "fusermount -u '%s'" % (mount_location)
            else:
                unmount_command = "gksu -u root \"umount '%s'\"" % (mount_location)
            log.write(globals.mount_log, unmount_command)
            unmount_process = subprocess.Popen(unmount_command, shell=True)
            unmount_process.wait()
            os.rmdir(mount_location)
        # The iter should not be removed on shutdown or it will screw up the gtk.TreeModel.foreach function
        if not is_shutdown:
            image_storage.remove(iter)
        log.write(globals.mount_log, _('%s successfully unmounted.'%(mount_location)))
    except:
        log.write(globals.mount_log, _('Error unmounting image.\nUnexpected error: %s' % (sys.exc_info()[0])))
        raise

def burn(image_file, is_brasero = True):
    try:
        if is_brasero:
            burn_command = "brasero --image '%s'" % (image_file)
        else:
            burn_command = "nautilus-cd-burner --source-iso='%s'" % (image_file)
        subprocess.Popen(burn_command, shell=True)
        log.write(globals.mount_log, burn_command)
    except:
        log.write(globals.mount_log, _('Error burning image.\nUnexpected error: %s' % (sys.exc_info()[0])))
        raise

def browse(mount_location):
    browse_command = "nautilus --browser '%s'" % (mount_location)
    try:
        if os.path.exists(mount_location):
            subprocess.Popen(browse_command, shell=True)
            log.write(globals.mount_log, browse_command)
    except:
        log.write(globals.mount_log, _('Error launching nautilus.\nUnexpected error: %s' % (sys.exc_info()[0])))
        raise


