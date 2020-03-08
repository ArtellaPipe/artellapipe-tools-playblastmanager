#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to generate cutomized playblasts
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import artellapipe

# Defines ID of the tool
TOOL_ID = 'artellapipe-tools-playblastmanager'

# We skip the reloading of this module when launching the tool
no_reload = True


class PlayblastManagerTool(artellapipe.Tool, object):
    def __init__(self, *args, **kwargs):
        super(PlayblastManagerTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = artellapipe.Tool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Playblast Manager',
            'id': 'artellapipe-tools-playblastmanager',
            'logo': 'playblastmanager_logo',
            'icon': 'video',
            'tooltip': 'Tool to generate customized playblasts',
            'tags': ['manager', 'playblast'],
            'sentry_id': 'https://d1f243de035d40bf98d492e80469b71b@sentry.io/1764692',
            'is_checkable': False,
            'is_checked': False,
            'menu_ui': {'label': 'Playblast Manager', 'load_on_startup': False, 'color': '', 'background_color': ''},
            'menu': [
                {'label': 'Layout',
                 'type': 'menu', 'children': [{'id': 'artellapipe-tools-playblastmanager', 'type': 'tool'}]},
                {'label': 'Animation',
                 'type': 'menu', 'children': [{'id': 'artellapipe-tools-playblastmanager', 'type': 'tool'}]}
            ],
            'shelf': [
                {'name': 'Layout',
                 'children': [{'id': 'artellapipe-tools-playblastmanager', 'display_label': False, 'type': 'tool'}]},
                {'name': 'Animation',
                 'children': [{'id': 'artellapipe-tools-playblastmanager', 'display_label': False, 'type': 'tool'}]}
            ]
        }
        base_tool_config.update(tool_config)

        return base_tool_config


class PlayblastManagerToolset(artellapipe.Toolset, object):
    ID = TOOL_ID

    def __init__(self, *args, **kwargs):
        super(PlayblastManagerToolset, self).__init__(*args, **kwargs)

    def contents(self):

        from artellapipe.tools.playblastmanager.widgets import playblastmanager

        playblast_manager = playblastmanager.PlayblastManager(
            project=self._project, config=self._config, settings=self._settings, parent=self)
        return [playblast_manager]
