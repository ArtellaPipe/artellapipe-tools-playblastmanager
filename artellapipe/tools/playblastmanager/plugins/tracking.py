#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Tracking Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging
import traceback

from Qt.QtWidgets import *

import tpDcc as tp

import artellapipe
from artellapipe.tools.playblastmanager.core import plugin

LOGGER = logging.getLogger()


class TrackerPlugin(plugin.PlayblastPlugin, object):

    id = 'Tracker'
    label = 'Production Tracker'

    def __init__(self, project, config, parent=None):
        super(TrackerPlugin, self).__init__(project=project, config=config, parent=parent)

        self.label = artellapipe.Tracker().get_name()

        if not artellapipe.Tracker().is_logged():
            artellapipe.Tracker().login()

        if artellapipe.Tracker().is_logged():
            self.refresh()

    @staticmethod
    def can_be_registered():
        return artellapipe.Tracker().is_tracking_available()

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(TrackerPlugin, self).ui()

        self._upload_playblast_cbx = QCheckBox('Upload Playblast to Production Tracker?')
        self._upload_playblast_cbx.setChecked(True)
        self.main_layout.addWidget(self._upload_playblast_cbx)

        combos_layout = QHBoxLayout()
        combos_layout.setContentsMargins(2, 2, 2, 2)
        combos_layout.setSpacing(2)
        self.main_layout.addLayout(combos_layout)

        self._sequences_combo = QComboBox()
        self._sequences_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._shots_combo = QComboBox()
        self._shots_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._tasks_combo = QComboBox()
        self._tasks_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        combos_layout.addWidget(self._sequences_combo)
        combos_layout.addWidget(QLabel("<span style='color:#E2AC2C'> &#9656; </span>"))
        combos_layout.addWidget(self._shots_combo)
        combos_layout.addWidget(QLabel("<span style='color:#E2AC2C'> &#9656; </span>"))
        combos_layout.addWidget(self._tasks_combo)

        stamp_version_lbl = QHBoxLayout()
        stamp_version_lbl.setContentsMargins(2, 2, 2, 2)
        stamp_version_lbl.setSpacing(2)
        stamp_templates_lbl = QLabel('Task Comment: ')
        self._task_comment_line = QLineEdit()
        self._task_comment_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        stamp_version_lbl.addWidget(stamp_templates_lbl)
        stamp_version_lbl.addWidget(self._task_comment_line)
        self.main_layout.addLayout(stamp_version_lbl)

    def setup_signals(self):
        self._sequences_combo.currentIndexChanged.connect(self._on_sequence_selected)
        self._shots_combo.currentIndexChanged.connect(self._on_shot_selected)

    def get_inputs(self, as_preset=False):
        """
        Overrides base ArtellaPlayblastPlugin get_inputs function
        Returns a dict with proper input variables as keys of the dictionary
        :return: dict
        """

        return {
            'tracker_enable': self._upload_playblast_cbx.isChecked(),
            'sequence_name': self._sequences_combo.currentText(),
            'shot_name': self._shots_combo.currentText(),
            'task_name': self._tasks_combo.currentText(),
            'task_comment': self._task_comment_line.text()
        }

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        sequence_name = None
        shot_name = None
        task_name = None

        sequence_index = self._sequences_combo.currentIndex()
        if sequence_index > 0:
            sequence_name = self._sequences_combo.currentText()
        shot_index = self._shots_combo.currentIndex()
        if shot_index >= 0:
            shot_name = self._shots_combo.currentText()
        task_index = self._tasks_combo.currentIndex()
        if task_index >= 0:
            task_name = self._tasks_combo.currentText()

        return {
            'tracker_enable': self._upload_playblast_cbx.isChecked(),
            'sequence_name': sequence_name,
            'shot_name': shot_name,
            'task_name': task_name,
            'task_comment': self._task_comment_line.text()
        }

    def apply_inputs(self, attrs_dict):
        tracker_enable = attrs_dict.get('tracker_enable', False)
        stamp_template = attrs_dict.get('stamp_comment', '')
        self._upload_playblast_cbx.setChecked(bool(tracker_enable))
        self._task_comment_line.setText(str(stamp_template))

    def refresh(self):
        self._fill_sequences_combo()
        self._shots_combo.clear()
        self._tasks_combo.clear()
        self._shots_combo.setEnabled(False)
        self._tasks_combo.setEnabled(False)
        self._fill_info_from_scene()

    def _fill_sequences_combo(self):
        self._sequences_combo.blockSignals(True)
        try:
            self._sequences_combo.clear()
            self._sequences_combo.addItem('< Select Sequence >')
            all_sequences = artellapipe.SequencesMgr().get_sequence_names() or list()
            for sequence_name in all_sequences:
                self._sequences_combo.addItem(sequence_name)
        except Exception as exc:
            LOGGER.error('Error while retrieving sequences: {} | {}'.format(exc, traceback.format_exc()))
        finally:
            self._sequences_combo.blockSignals(False)

    def _fill_info_from_scene(self):
        scene_file = tp.Dcc.scene_name()
        if not scene_file:
            return
        parsed_path = artellapipe.FilesMgr().parse_path(scene_file)
        if not parsed_path:
            return

        sequence_name = parsed_path.get('sequence_name', None)
        if not sequence_name:
            return
        sequence_index = self._sequences_combo.findText(sequence_name)
        if sequence_index <= -1:
            return
        current_sequence_index = self._sequences_combo.currentIndex()
        self._sequences_combo.setCurrentIndex(sequence_index)
        if current_sequence_index == sequence_index:
            self._on_sequence_selected(current_sequence_index)

        shot_name = parsed_path.get('shot_name', None)
        if not shot_name:
            return
        shot_index = self._shots_combo.findText(shot_name)
        if shot_index <= -1:
            return
        current_shot_index = self._shots_combo.currentIndex()
        self._shots_combo.setCurrentIndex(shot_index)
        if current_shot_index == shot_index:
            self._on_shot_selected(current_shot_index)

    def _disable_combos(self, clear=True):
        if clear:
            self._shots_combo.clear()
            self._tasks_combo.clear()
        self._shots_combo.setEnabled(False)
        self._tasks_combo.setEnabled(False)

    def _on_sequence_selected(self, index):
        self._disable_combos()
        if index == 0:
            return

        sequence_name = self._sequences_combo.itemText(index)
        if not sequence_name:
            return

        sequence_shots = artellapipe.ShotsMgr().get_shots_from_sequence(sequence_name)
        if not sequence_shots:
            self._disable_combos()
        self._shots_combo.setEnabled(True)
        for shot in sequence_shots:
            self._shots_combo.addItem(shot.get_name())

    def _on_shot_selected(self, index):
        self._tasks_combo.clear()
        self._tasks_combo.setEnabled(False)

        shot_name = self._shots_combo.itemText(index)
        if not shot_name:
            return

        shot_tasks = artellapipe.TasksMgr().get_task_names_for_shot(shot_name)
        if not shot_tasks:
            return
        self._tasks_combo.setEnabled(True)
        self._tasks_combo.addItems(shot_tasks)
