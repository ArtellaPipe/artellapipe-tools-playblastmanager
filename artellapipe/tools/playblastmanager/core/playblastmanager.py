#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to capture playblasts
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import inspect
import logging

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import path as path_utils, python
from tpQtLib.widgets import accordion, stack

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe
from artellapipe.widgets import dialog
from artellapipe.utils import resource
from artellapipe.tools.playblastmanager.core import plugin
from artellapipe.tools.playblastmanager.widgets import presets, preview


LOGGER = logging.getLogger()


class DefaultPlayblastOptions(plugin.PlayblastPlugin, object):

    def get_outputs(self):
        outputs = dict()
        scene = artellapipe.PlayblastsMgr().parse_current_scene()
        outputs['sound'] = scene['sound']
        outputs['show_ornaments'] = True
        outputs['camera_options'] = dict()
        outputs['camera_options']['overscan'] = 1.0
        outputs['camera_options']['displayFieldChart'] = False
        outputs['camera_options']['displayFilmGate'] = False
        outputs['camera_options']['displayFilmOrigin'] = False
        outputs['camera_options']['displayFilmPivot'] = False
        outputs['camera_options']['displayGateMask'] = False
        outputs['camera_options']['displayResolution'] = False
        outputs['camera_options']['displaySafeAction'] = False
        outputs['camera_options']['displaySafeTitle'] = False

        return outputs


class PlayblastManager(artellapipe.Tool, object):

    optionsChanged = Signal(dict)
    playblastStart = Signal(dict)
    playblastFinished = Signal(dict)
    viewerStart = Signal(dict)

    def __init__(self, project, config):
        self.playblast_widgets = list()
        self.config_dialog = None
        self._plugins = list()

        super(PlayblastManager, self).__init__(project=project, config=config)

        tokens = self.config.get('tokens', dict())
        if tokens:
            for token in tokens:
                for token_name, token_info in token.items():
                    if 'rule' in token_info:
                        artellapipe.PlayblastsMgr().register_token(
                            token_name, lambda attrs_dict: artellapipe.PlayblastsMgr().get_project_rule_token(
                                token_info['rule']), label=token_info['label']
                        )
                    else:
                        if 'fn' not in token_info:
                            LOGGER.warning(
                                'Impossible to register token "{}" because its function is not defined!'.format(
                                    token_name))
                            continue
                        if not hasattr(artellapipe.PlayblastsMgr(), token_info['fn']):
                            LOGGER.warning(
                                'Impossible to register token "{}" because PlayblastMgr does not implements '
                                'its function: "{}"'.format(token_name, token_info['fn']))
                        artellapipe.PlayblastsMgr().register_token(
                            token_name, lambda attrs_dict: getattr(
                                artellapipe.PlayblastsMgr(), token_info['fn'])(), label=token_info['label']
                        )

        registered_plugins = self._get_registered_plugins() or list()
        for plugin_class in registered_plugins:
            plugin_inst = plugin_class(project=self._project)
            self._main_widget.add_item(plugin_inst.id, plugin_inst)
            self._plugins.append(plugin_inst)

        if self._plugins:
            self._stack.slide_in_index(1)
            self.capture_btn.setVisible(True)

    def ui(self):
        super(PlayblastManager, self).ui()

        self._stack = stack.SlidingStackedWidget()

        no_items_widget = QFrame()
        no_items_widget.setFrameShape(QFrame.StyledPanel)
        no_items_widget.setFrameShadow(QFrame.Sunken)
        no_items_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        no_items_layout = QVBoxLayout()
        no_items_layout.setContentsMargins(0, 0, 0, 0)
        no_items_layout.setSpacing(0)
        no_items_widget.setLayout(no_items_layout)
        no_items_lbl = QLabel()
        no_items_pixmap = resource.ResourceManager().pixmap('no_plugins_available')
        no_items_lbl.setPixmap(no_items_pixmap)
        no_items_lbl.setAlignment(Qt.AlignCenter)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))
        no_items_layout.addWidget(no_items_lbl)
        no_items_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Preferred, QSizePolicy.Expanding))

        self._main_widget = accordion.AccordionWidget(parent=self)
        self._main_widget.rollout_style = accordion.AccordionStyle.MAYA

        self.preset_widget = presets.PlayblastPreset(
            project=self._project, inputs_getter=self.get_inputs, config=self.config, parent=self)
        self._main_widget.add_item('Presets', self.preset_widget, collapsed=False)

        self.preview_widget = preview.PlayblastPreview(options=self.get_outputs, validator=self.validate, parent=self)
        self._main_widget.add_item('Preview', self.preview_widget, collapsed=False)

        self.capture_btn = QPushButton('C A P T U R E')
        self.capture_btn.setVisible(False)

        self._stack.addWidget(no_items_widget)
        self._stack.addWidget(self._main_widget)

        self.main_layout.addWidget(self._stack)
        self.main_layout.addWidget(self.capture_btn)

        # self.default_options = DefaultPlayblastOptions(project=self._project)
        # self.playblast_widgets.append(self.default_options)
        #
        # self.time_range = timerange.TimeRangeWidget(project=self._project)
        # self.cameras = cameras.CamerasWidget(project=self._project)
        # self.resolution = resolution.ResolutionWidget(project=self._project)
        # self.stamp = stamp.StampWidget(project=self._project)
        # self.save = save.SaveWidget(project=self._project)
        #
        # for widget in [self.cameras, self.resolution, self.time_range, self.stamp, self.save]:
        #     widget.initialize()
        #     widget.optionsChanged.connect(self._on_update_settings)
        #     self.playblastFinished.connect(widget.on_playblast_finished)
        #
        #     if widget == self.save:
        #         item = self._main_widget.add_item(widget.id, widget, collapsed=False)
        #     else:
        #         item = self._main_widget.add_item(widget.id, widget, collapsed=True)
        #     self.playblast_widgets.append(widget)
        #     if item is not None:
        #         widget.labelChanged.connect(item.setTitle)
        #
        # # We force the reload of the camera plugin title
        # self.cameras._on_update_label()
        # self.resolution._on_resolution_changed()

    # def setup_signals(self):
    #     self.capture_btn.clicked.connect(self._on_capture)
    #     self.preset_widget.configOpened.connect(self.show_config)
    #     self.preset_widget.presetLoaded.connect(self.apply_inputs)

    def post_attacher_set(self):
        self.apply_inputs(inputs=self._read_configuration())

    def get_plugins_paths(self):
        """
        Returns paths where plugins are located
        :return: list(str)
        """

        plugins_path = path_utils.clean_path(
            os.path.join(os.path.dirname(os.path.os.path.dirname(os.path.abspath(__file__))), 'plugins'))
        return [plugins_path]

    def validate(self):
        """
        Will ensure that widget outputs are valid and will raise proper errors if necessary
        :return: list<str>
        """

        errors = list()
        for widget in self.playblast_widgets:
            if hasattr(widget, 'validate'):
                widget_errors = widget.validate()
                if widget_errors:
                    errors.extend(widget_errors)

        if errors:
            message_title = '{} Validation Error(s)'.format(len(errors))
            message = '\n'.join(errors)
            QMessageBox.critical(self, message_title, message, QMessageBox.Ok)
            return False

        return True

    def get_inputs(self, as_preset=False):
        """
        Returns a dict with proper input variables as keys of the dictionary
        :param as_preset: bool
        :return: dict
        """

        inputs = dict()
        config_widgets = self.playblast_widgets
        config_widgets.append(self.preset_widget)
        for widget in config_widgets:
            widget_inputs = widget.get_inputs(as_preset=as_preset)
            if not isinstance(widget_inputs, dict):
                LOGGER.warning(
                    'Widget inputs are not a valid dictionary "{0}" : "{1}"'.format(widget.id, widget_inputs))
                return
            if not widget_inputs:
                continue
            inputs[widget.id] = widget_inputs

        return inputs

    def get_outputs(self):
        """
          Returns the outputs variables of the Playblast widget as dict
          :return: dict
          """

        outputs = dict()
        for widget in self.playblast_widgets:
            if hasattr(widget, 'get_outputs'):
                widget_outputs = widget.get_outputs()
                if not widget_outputs:
                    continue
                for key, value in widget_outputs.items():
                    if isinstance(value, dict) and key in outputs:
                        outputs[key].update(value)
                    else:
                        outputs[key] = value

        return outputs

    def apply_inputs(self, inputs):
        """
        Applies the given dict of attributes to the widget
        :param inputs: dict
        """

        if not inputs:
            return

        # widgets = self.playblast_widgets
        # widgets.append(self.preset_widget)
        # for widget in widgets:
        #     widget_inputs = inputs.get(widget.id, None)
        #     if not widget_inputs:
        #         widget_inputs = dict()
        #     # if not widget_inputs:
        #     #     continue
        #     # if widget_inputs:
        #     widget.apply_inputs(widget_inputs)

    def show_config(self):
        """
        Shows advanced configuration dialog
        """

        self._build_configuration_dialog()

        geometry = self.geometry()
        self.config_dialog.move(QPoint(geometry.x() + 30, geometry.y()))
        self.config_dialog.exec_()

    def _get_plugins(self):
        """
        Returns a list with all available plugins
        :return: list
        """

        plugins_paths = self.get_plugins_paths()
        if not plugins_paths:
            LOGGER.warning('No Plugins path to search plugins from!')
            return

        plugins_found = dict()

        for plugin_path in plugins_paths:
            if not plugin_path or not os.path.isdir(plugin_path):
                LOGGER.warning('Plugin Path "{}" does not exist!'.format(plugin_path))
                continue

            for sub_module in loader.walk_packages([plugin_path]):
                importer, sub_module_name, _ = sub_module
                mod = importer.find_module(sub_module_name).load_module(sub_module_name)
                for cname, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, plugin.PlayblastPlugin):
                        if cname in plugins_found:
                            LOGGER.warning(
                                'Playblast Plugin with name "{}" is already registered! Overriding ...'.format(cname))
                        plugins_found[cname] = obj

        return plugins_found

    def _get_registered_plugins(self):
        """
        Returns plugins that are registered in Playblast Manager configuration file
        :return: list
        """

        all_plugins = self._get_plugins()
        if not all_plugins:
            LOGGER.warning('No plugins available!')
            return None

        plugins_to_register = self.config.get('plugins', list())
        if not plugins_to_register:
            LOGGER.warning('No plugins to register defined in Playblast Manager configuration file!')
            return None

        registered_plugins = dict()

        for plugin_name, plugin_class in all_plugins.items():
            if plugin_name not in plugins_to_register:
                continue
            if plugin_name in registered_plugins:
                LOGGER.warning('Plugin "{}" already registered. Skipping ...'.format(plugin_name))
                continue

            registered_plugins[plugin_name] = plugin_class

        return registered_plugins.values()

    def _build_configuration_dialog(self):
        """
        Build configuration dialog to store configuration widgets in
        """

        self.config_dialog = PlayblastTemplateConfigurationDialog(project=self._project)

    def _read_configuration(self):
        inputs = dict()
        settings_file = self.settings()
        if not settings_file:
            LOGGER.warning('Impossible to read configuration because settings file does not exists!')
            return

        path = settings_file.fileName()
        if not os.path.isfile(path) or os.stat(path).st_size == 0:
            return inputs

        for section in self.settings().groups:
            if section == self.objectName().lower():
                continue
            inputs[section] = dict()
            settings_file.beginGroup(section)
            items = settings_file.childKeys() or list()
            for item in items:
                inputs[section][str(item)] = settings_file.value(item)

        return inputs

    def _store_configuration(self):
        pass
        # inputs = self.get_inputs(as_preset=False)
        # for widget_id, attrs_dict in inputs.items():
        #     if not self.settings.has_section(widget_id):
        #         self.settings.add_section(widget_id)
        #     for attr_name, attr_value in attrs_dict.items():
        #         self.settings.set(widget_id, attr_name, attr_value)
        # self.settings.update()

    def _on_update_settings(self):
        """
        Internal callback function that is called when options are updated
        """

        self.optionsChanged.emit(self.get_outputs)
        self.preset_widget.presets.setCurrentIndex(0)

    def _on_capture(self):
        valid = self.validate()
        if not valid:
            return

        options = self.get_outputs()
        filename = options.get('filename', None)

        print('CAPTURIGIGIGIGIG')
        print(options)

        # self.playblastStart.emit(options)
        #
        # if filename is not None:
        #     print('Creating capture')
        #
        # options['filename'] = filename
        # options['filename'] = artellapipe.PlayblastsMgr().capture_scene(options=options)
        #
        # self.playblastFinished.emit(options)
        #
        # filename = options['filename']
        #
        # viewer = options.get('viewer', False)
        # if viewer:
        #     if filename and os.path.exists(filename):
        #         self.viewerStart.emit(options)
        #         osplatform.open_file(file_path=filename)
        #     else:
        #         raise RuntimeError('Cannot open playblast because file "{}" does not exists!'.format(filename))
        #
        # return filename


class PlayblastTemplateConfigurationDialog(dialog.ArtellaDialog, object):

    def __init__(self, project, parent=None, **kwargs):

        self.playblast_config_widgets = list()

        super(PlayblastTemplateConfigurationDialog, self).__init__(

            name='PlayblastTemplateConfigurationDialog',
            title='Artella - Playblast Template Configuration',
            parent=parent,
            project=project,
            **kwargs
        )

    def custom_ui(self):
        super(PlayblastTemplateConfigurationDialog, self).custom_ui()

        self.set_logo('solstice_playblast_logo')

        self.resize(400, 810)

        self.setMinimumHeight(810)
        self.setMaximumWidth(400)

        self.options_widget = accordion.AccordionWidget(parent=self)
        self.options_widget.rollout_style = accordion.AccordionStyle.MAYA
        self.main_layout.addWidget(self.options_widget)

        # self.codec = codec.CodecWidget(project=self._project)
        # self.renderer = renderer.RendererWidget(project=self._project)
        # self.display = displayoptions.DisplayOptionsWidget(project=self._project)
        # self.viewport = viewport.ViewportOptionsWidget(project=self._project)
        # self.options = options.PlayblastOptionsWidget(project=self._project)
        # self.panzoom = panzoom.PanZoomWidget(project=self._project)

        for widget in [self.codec, self.renderer, self.display, self.viewport, self.options, self.panzoom]:
            widget.initialize()
            # widget.optionsChanged.connect(self._on_update_settings)
            # self.playblastFinished.connect(widget.on_playblast_finished)
            item = self.options_widget.add_item(widget.id, widget)
            self.playblast_config_widgets.append(widget)
            if item is not None:
                widget.labelChanged.connect(item.setTitle)
