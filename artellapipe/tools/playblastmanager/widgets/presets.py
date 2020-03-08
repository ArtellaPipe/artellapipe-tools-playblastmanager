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
import glob
import json
import logging.config

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc
from tpDcc.libs.python import jsonio, fileio, folder as folder_utils
from tpDcc.libs.qt.core import base

import artellapipe

LOGGER = logging.getLogger()


class PlayblastPreset(base.BaseWidget, object):

    presetLoaded = Signal(dict)

    id = 'Presets'
    label = 'Presets'

    registered_paths = list()

    def __init__(self, project, inputs_getter, config, parent=None):

        self._project = project
        self._config = config
        self._inputs_getter = inputs_getter

        super(PlayblastPreset, self).__init__(parent=parent)
        presets_folders = artellapipe.PlayblastsMgr().get_presets_paths()
        if not presets_folders:
            LOGGER.warning('No Presets folders found!')
            return

        for preset_folder in presets_folders:
            self.register_preset_path(preset_folder)

        self._process_presets()

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignCenter)

        return main_layout

    def ui(self):
        super(PlayblastPreset, self).ui()

        self._presets = QComboBox()
        self._presets.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        save_icon = tpDcc.ResourcesMgr().icon('save')
        self._save_btn = QPushButton()
        self._save_btn.setIcon(save_icon)
        self._save_btn.setFixedWidth(30)
        self._save_btn.setToolTip('Save Preset')
        self._save_btn.setStatusTip('Save Preset')

        load_icon = tpDcc.ResourcesMgr().icon('open')
        self._load_btn = QPushButton()
        self._load_btn.setIcon(load_icon)
        self._load_btn.setFixedWidth(30)
        self._load_btn.setToolTip('Load Preset')
        self._load_btn.setStatusTip('Load Preset')

        preset_sync_icon = tpDcc.ResourcesMgr().icon('sync')
        self._preset_sync = QPushButton()
        self._preset_sync.setIcon(preset_sync_icon)
        self._preset_sync.setFixedWidth(30)
        self._preset_sync.setToolTip('Sync Prests from Artella')
        self._preset_sync.setStatusTip('Sync Presets from ASrtella')

        vertical_separator = QFrame()
        vertical_separator.setFrameShape(QFrame.VLine)
        vertical_separator.setFrameShadow(QFrame.Sunken)

        open_templates_folder_icon = tpDcc.ResourcesMgr().icon('search')
        self._open_templates_folder_btn = QPushButton()
        self._open_templates_folder_btn.setIcon(open_templates_folder_icon)
        self._open_templates_folder_btn.setFixedWidth(30)
        self._open_templates_folder_btn.setToolTip('Open Templates Folder')
        self._open_templates_folder_btn.setStatusTip('Open Templates Folder')

        for widget in [
            self._presets,
            self._save_btn,
            self._load_btn,
            self._preset_sync,
            vertical_separator,
            self._open_templates_folder_btn
        ]:
            self.main_layout.addWidget(widget)

    def setup_signals(self):
        self._save_btn.clicked.connect(self._on_save_preset)
        self._load_btn.clicked.connect(self.import_preset)
        self._preset_sync.clicked.connect(self._on_sync_presets)
        self._presets.currentIndexChanged.connect(self.load_active_preset)
        self._open_templates_folder_btn.clicked.connect(self.open_templates_folder)

    @property
    def presets(self):
        return self._presets

    def get_inputs(self, as_preset=False):
        if as_preset:
            return {}
        else:
            current_index = self._presets.currentIndex()
            selected = self._presets.itemData(current_index)
            return {'selected': selected}

    def apply_inputs(self, settings):
        path = settings.get('selected', None)
        if not path:
            return
        index = self._presets.findData(path)
        if index == -1:
            if os.path.exists(path):
                LOGGER.info('Adding previously selected preset explicitilly: {}'.format(path))
                self.add_preset(path)
            else:
                LOGGER.warning('Previously selected preset is not available: {}'.format(path))
                index = 0

        self._presets.blockSignals(True)
        try:
            self._presets.setCurrentIndex(index)
        finally:
            self._presets.blockSignals(False)

    @classmethod
    def get_preset_paths(cls):
        """
        Returns existing registered preset paths
        :return: list<str>, list of full paths
        """

        paths = list()
        for path in cls.registered_paths:
            if path in paths:
                continue
            if not os.path.exists(path):
                continue
            paths.append(path)

        return paths

    @classmethod
    def register_preset_path(cls, path):
        """
        Add file path to registered presets
        :param path: str, path of the preset file
        """

        if path in cls.registered_paths:
            LOGGER.warning('Preset path already registered: "{}"'.format(path))
            return
        cls.registered_paths.append(path)

        return path

    @classmethod
    def discover_presets(cls, paths=None):
        """
        Get the full list of files found in the registered preset folders
        :param paths: list<str>, directories which stores preset files
        :return: list<str>, valid JSON preset file paths
        """

        presets = list()
        for path in paths or cls.get_preset_paths():
            path = os.path.normpath(path)
            if not os.path.isdir(path):
                continue

            glob_query = os.path.abspath(os.path.join(path, '*.json'))
            file_names = glob.glob(glob_query)
            for file_name in file_names:
                if file_name.startswith('_'):
                    continue
                if not fileio.file_has_info(file_name):
                    LOGGER.warning('File size is smaller than 1 byte for preset file: "{}"'.format(file_name))
                    continue
                if file_name not in presets:
                    presets.append(file_name)

        return presets

    def get_presets(self):
        """
        Returns all currently listed presets
        :return: list<str>
        """

        presets_list = [self._presets.itemText(i) for i in range(self._presets.count())]
        return presets_list

    def add_preset(self, filename):
        """
        Add the filename to the presets list
        :param filename: str
        """

        filename = os.path.normpath(filename)
        if not os.path.exists(filename):
            LOGGER.warning('Preset file does not exists: "{}"'.format(filename))
            return

        label = os.path.splitext(os.path.basename(filename))[0]
        item_count = self._presets.count()

        paths = [self._presets.itemData(i) for i in range(item_count)]
        if filename in paths:
            LOGGER.info('Preset is already in the presets list: "{}"'.format(filename))
            item_index = paths.index(filename)
        else:
            self._presets.addItem(label, userData=filename)
            item_index = item_count

        self._presets.blockSignals(True)
        self._presets.setCurrentIndex(item_index)
        self._presets.blockSignals(False)

        return item_index

    def import_preset(self):
        """
        Load preset file sto override output values
        """

        path = self._default_browse_path()
        filters = 'Text file (*.json)'
        dialog = QFileDialog()
        filename, _ = dialog.getOpenFileName(self, 'Open Playblast Preset File', path, filters)
        if not filename:
            return

        self.add_preset(filename)

        return self.load_active_preset()

    def save_preset(self, inputs):
        """
        Save Playblast template on a file
        :param inputs: dict
        """

        path = self._default_browse_path()
        filters = 'Text file (*.json)'
        filename, _ = QFileDialog.getSaveFileName(self, 'Save Playblast Preset File', path, filters)
        if not filename:
            return

        with open(filename, 'w') as f:
            json.dump(inputs, f, sort_keys=True, indent=4, separators=(',', ': '))

        self.add_preset(filename)

        return filename

    def load_active_preset(self):
        """
        Loads the active preset
        :return: dict, preset inputs
        """

        current_index = self._presets.currentIndex()
        filename = self._presets.itemData(current_index)
        if not filename:
            return {}

        preset = jsonio.read_file(filename)
        self.presetLoaded.emit(preset)

        self._presets.blockSignals(True)
        self._presets.setCurrentIndex(current_index)
        self._presets.blockSignals(False)

        return preset

    def open_templates_folder(self):
        """
        Opens folder where templates are stored
        :return:
        """

        folder_utils.open_folder(self._default_browse_path())

    def _process_presets(self):
        """
        Adds all preset files from preset paths
        """

        for preset_file in self.discover_presets():
            self.add_preset(preset_file)

        if self._presets.count() <= 0:
            self.presets.addItem('*')
        self._presets.setCurrentIndex(0)

    def _default_browse_path(self):
        """
        Returns the current browse path for save/load preset
        If a preset is currently loaded it will use that specific path otherwise it will
        go to the last registered preset path
        :return: str, path to use as default browse location
        """

        current_index = self._presets.currentIndex()
        path = self._presets.itemData(current_index)
        if not path:
            paths = self.get_preset_paths()
            if paths:
                path = paths[-1]

        return path

    def _on_save_preset(self):
        """
        Internal function that saves playblast template to a file
        """

        inputs = self._inputs_getter(as_preset=True)
        self.save_preset(inputs)

    def _on_sync_presets(self):
        """
        Internal function that syncronizes presets from Artella
        """

        presets_paths = self.get_preset_paths()
        if presets_paths:
            artellapipe.FilesMgr().sync_paths(presets_paths, recursive=True)
            self._presets.blockSignals(True)
            self._presets.clear()
            self._presets.blockSignals(True)
            self._process_presets()
            self.load_active_preset()
