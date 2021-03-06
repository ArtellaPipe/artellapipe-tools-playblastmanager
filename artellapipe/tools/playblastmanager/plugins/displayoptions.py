#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Display Options Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *

import tpDcc as tp

from tpDcc.libs.qt.widgets import layouts, color, label, checkbox, combobox

from artellapipe.tools.playblastmanager.core import plugin

if tp.is_maya():
    import tpDcc.dccs.maya as maya


class DisplayOptionsWidget(plugin.PlayblastPlugin, object):
    """
    Allows user to set playblast display settings
    """

    id = 'DisplayOptions'
    label = 'Display Options'
    collapsed = True

    BACKGROUND_DEFAULT = [0.6309999823570251, 0.6309999823570251, 0.6309999823570251]
    TOP_DEFAULT = [0.5350000262260437, 0.6169999837875366, 0.7020000219345093]
    BOTTOM_DEFAULT = [0.052000001072883606, 0.052000001072883606, 0.052000001072883606]
    COLORS = {"background": BACKGROUND_DEFAULT,
              "backgroundTop": TOP_DEFAULT,
              "backgroundBottom": BOTTOM_DEFAULT}
    LABELS = {"background": "Background",
              "backgroundTop": "Top",
              "backgroundBottom": "Bottom"}

    def __init__(self, project, config, parent=None):

        self._colors = dict()

        super(DisplayOptionsWidget, self).__init__(project=project, config=config, parent=parent)

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(DisplayOptionsWidget, self).ui()

        self.override = checkbox.BaseCheckBox('Override Display Options')

        self.display_type = combobox.BaseComboBox()
        self.display_type.addItems(['Solid', 'Gradient'])

        self._color_layout = layouts.HorizontalLayout()
        for lbl, default in self.COLORS.items():
            self._add_color_picker(self._color_layout, lbl, default)

        self.main_layout.addWidget(self.override)
        self.main_layout.addWidget(self.display_type)
        self.main_layout.addLayout(self._color_layout)

        self._on_toggle_override()

        self.override.toggled.connect(self._on_toggle_override)
        self.override.toggled.connect(self.optionsChanged)
        self.display_type.currentIndexChanged.connect(self.optionsChanged)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        inputs = {'override_display': self.override.isChecked()}
        for lbl, w in self._colors.items():
            inputs[lbl] = w.color

        return inputs

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        outputs = dict()

        if not tp.is_maya():
            return outputs

        if self.override.isChecked():
            outputs['displayGradient'] = self.display_gradient()
            for lbl, w in self._colors.items():
                outputs[lbl] = w.color
        else:
            outputs['displayGradient'] = maya.cmds.displayPref(query=True, displayGradient=True)
            for key in self.COLORS.keys():
                clr = maya.cmds.displayRGBColor(key, query=True)
                outputs[key] = clr

        return {'display_options': outputs}

    def apply_inputs(self, attrs_dict):
        """
        Overrides base ArtellaPlayblastPlugin apply_inputs function
        Applies the given dict of attributes to the widget
        :param attrs_dict: dict
        """

        for lbl, w in self._colors.items():
            default = self.COLORS.get(lbl, [0, 0, 0])
            value = attrs_dict.get(lbl, default)
            w.color = value

        override = attrs_dict.get('override_display', False)
        self.override.setChecked(override)

    def display_gradient(self):
        """
        Returns whether the background should be displayed as gradient
        If True, the colors will use the top and bottom colors to define
        the gradient otherwise the background color will be used as solid color
        :return: bool, True if background is gradient, False otherwise
        """

        return self.display_type.currentText() == 'Gradient'

    def _add_color_picker(self, layout, label_name, default):
        """
        Internal function that creates a picker with a label and a button to select a color
        :param layout: QLayout, layout to add color picker to
        :param label: str, system name for the color type (egp: backgorundTop)
        :param default: list, default color to start with
        :return: solstice_color.ColorPicker
        """

        color_layout = layouts.VerticalLayout()
        lbl = label.BaseLabel(self.LABELS[label_name])
        color_picker = color.ColorPicker()
        color_picker.color = default
        color_layout.addWidget(lbl)
        color_layout.addWidget(color_picker)
        color_layout.setAlignment(lbl, Qt.AlignCenter)
        layout.addLayout(color_layout)
        color_picker.colorChanged.connect(self.optionsChanged)
        self._colors[label_name] = color_picker

        return color_picker

    def _on_toggle_override(self):
        """
        Internal function that is called when override is toggled
        Enable or disabled the color pickers and background type widgets bases on the current state of the override
        checkbox
        """

        state = self.override.isChecked()
        self.display_type.setEnabled(state)
        for w in self._colors.values():
            w.setEnabled(state)
