#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for presets widget
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import tempfile

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.python import decorators

import tpDcc as tp
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import label

import artellapipe

if tp.is_maya():
    from tpDcc.dccs.maya.core import decorators as maya_decorators
    no_undo_decorator = maya_decorators.SkipUndo
else:
    no_undo_decorator = decorators.empty_decorator_context

LOGGER = logging.getLogger()


class PlayblastPreview(base.BaseWidget, object):
    """
    Playblast image preview
    """

    __DEFAULT_WIDTH__ = 320
    __DEFAULT_HEIGHT__ = 180

    def __init__(self, options, validator, parent=None):

        self.options = options
        self.validator = validator

        super(PlayblastPreview, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignHCenter)

        return main_layout

    def ui(self):
        super(PlayblastPreview, self).ui()

        self.preview = label.ClickLabel()
        # self.preview.setFixedWidth(self.__DEFAULT_WIDTH__)
        # self.preview.setFixedHeight(self.__DEFAULT_HEIGHT__)
        self.main_layout.addWidget(self.preview)

        sync_icon = tp.ResourcesMgr().icon('sync')
        self.sync_preview_btn = QPushButton()
        self.sync_preview_btn.setIcon(sync_icon)
        self.sync_preview_btn.setFixedWidth(25)
        self.sync_preview_btn.setFixedHeight(25)
        self.sync_preview_btn.setIconSize(QSize(25, 25))
        self.sync_preview_btn.setToolTip('Sync Preview')
        self.sync_preview_btn.setStatusTip('Sync Preview')
        self.sync_preview_btn.setParent(self.preview)
        self.sync_preview_btn.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0); border: 0px solid rgba(255,255,255,0);")
        self.sync_preview_btn.move(5, 5)

        self.sync_preview_btn.clicked.connect(self.refresh)

    def showEvent(self, event):
        self.refresh()
        event.accept()

    def refresh(self):
        """
        Refresh playblast preview
        """

        frame = tp.Dcc.get_current_frame()

        # When play blasting outside of an undo queue next undo will trigger a reset to frame 0
        # To solve this and ensure undo works properly, we update undo queue with current time
        tp.Dcc.set_current_frame(frame)

        valid = self.validator()
        if not valid:
            return

        with no_undo_decorator():
            options = self.options()
            tempdir = tempfile.mkdtemp()

            # Override settings that are constants for the preview
            options = options.copy()
            options['filename'] = None
            options['complete_filename'] = os.path.join(tempdir, 'temp.jpg')
            options['width'] = self.__DEFAULT_WIDTH__
            options['height'] = self.__DEFAULT_HEIGHT__
            options['viewer'] = False
            options['frame'] = frame
            options['off_screen'] = True
            options['format'] = 'image'
            options['compression'] = 'jpg'
            options['sound'] = None

            frame_name = artellapipe.PlayblastsMgr().capture_scene(**options)
            if not frame_name:
                LOGGER.warning('Preview failed!')
                return

            image = QPixmap(frame_name)
            self.preview.setPixmap(image)
            os.remove(frame_name)
