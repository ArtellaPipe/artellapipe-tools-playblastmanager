#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Stamp Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtWidgets import *

from artellapipe.tools.playblastmanager.core import plugin


class StampWidget(plugin.PlayblastPlugin, object):

    id = 'Stamp'

    def __init__(self, project, parent=None):
        super(StampWidget, self).__init__(project=project, parent=parent)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(StampWidget, self).ui()

        self.enable_cbx = QCheckBox('Enable')

        self.main_layout.addWidget(self.enable_cbx)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        return {
            'enable_stamp': self.enable_cbx.isChecked()
        }

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        return {
            'enable_stamp': self.enable_cbx.isChecked()
        }

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin apply_inputs function
        Applies the given dict of attributes to the widget
        :param attrs_dict: dict
        """

        enable = attrs_dict.get('enable_stamp', True)

        self.enable_cbx.setChecked(enable)
