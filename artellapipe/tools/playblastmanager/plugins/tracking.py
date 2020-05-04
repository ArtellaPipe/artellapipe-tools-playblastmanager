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

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs.qt.widgets import layouts, label, checkbox, combobox, lineedit

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
        main_layout = layouts.VerticalLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(TrackerPlugin, self).ui()

        self._upload_playblast_cbx = checkbox.BaseCheckBox('Upload Playblast to Production Tracker?')
        self._upload_playblast_cbx.setChecked(True)
        self.main_layout.addWidget(self._upload_playblast_cbx)

        combos_layout = layouts.HorizontalLayout()
        combos_layout.setContentsMargins(2, 2, 2, 2)
        combos_layout.setSpacing(2)
        self.main_layout.addLayout(combos_layout)

        self._sequences_combo = combobox.BaseComboBox()
        self._sequences_combo.set_placeholder('< Sequence >')
        self._shots_combo = combobox.BaseComboBox()
        self._shots_combo.set_placeholder('< Shot >')
        self._tasks_combo = combobox.BaseComboBox()
        self._tasks_combo.set_placeholder('< Task >')
        self._task_status_combo = combobox.BaseComboBox()
        self._task_status_combo.set_placeholder('< Status >')

        combos_layout.addWidget(self._sequences_combo)
        combos_layout.addWidget(label.BaseLabel("<span style='color:#E2AC2C'> &#9656; </span>"))
        combos_layout.addWidget(self._shots_combo)
        combos_layout.addWidget(label.BaseLabel("<span style='color:#E2AC2C'> &#9656; </span>"))
        combos_layout.addWidget(self._tasks_combo)
        combos_layout.addWidget(label.BaseLabel("<span style='color:#E2AC2C'> &#9656; </span>"))
        combos_layout.addWidget(self._task_status_combo)

        stamp_version_lbl = layouts.HorizontalLayout()
        stamp_version_lbl.setContentsMargins(2, 2, 2, 2)
        stamp_version_lbl.setSpacing(2)
        stamp_templates_lbl = label.BaseLabel('Task Comment: ')
        self._task_comment_line = lineedit.BaseLineEdit()
        stamp_version_lbl.addWidget(stamp_templates_lbl)
        stamp_version_lbl.addWidget(self._task_comment_line)
        self.main_layout.addLayout(stamp_version_lbl)

    def setup_signals(self):
        self._sequences_combo.currentIndexChanged.connect(self._on_sequence_selected)
        self._shots_combo.currentIndexChanged.connect(self._on_shot_selected)
        self._tasks_combo.currentIndexChanged.connect(self._on_task_selected)

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
            'task_comment': self._task_comment_line.text(),
            'task_status': self._task_status_combo.currentText()
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
        task_status = None

        sequence_index = self._sequences_combo.currentIndex()
        if sequence_index > 0:
            sequence_name = self._sequences_combo.currentText()
        shot_index = self._shots_combo.currentIndex()
        if shot_index >= 0:
            shot_name = self._shots_combo.currentText()
        task_index = self._tasks_combo.currentIndex()
        if task_index >= 0:
            task_name = self._tasks_combo.currentText()
        task_status_index = self._task_status_combo.currentIndex()
        if task_status_index > 0:
            task_status = self._task_status_combo.currentText()

        return {
            'tracker_enable': self._upload_playblast_cbx.isChecked(),
            'sequence_name': sequence_name,
            'shot_name': shot_name,
            'task_name': task_name,
            'task_status': task_status,
            'task_comment': self._task_comment_line.text(),
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
        self._task_status_combo.clear()
        self._shots_combo.setEnabled(False)
        self._tasks_combo.setEnabled(False)
        self._task_status_combo.setEnabled(False)
        self._fill_info_from_scene()

    def _fill_sequences_combo(self):
        self._sequences_combo.blockSignals(True)
        try:
            self._sequences_combo.clear()
            self._sequences_combo.addItem('< Sequence >')
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
            self._task_status_combo.clear()
        self._shots_combo.setEnabled(False)
        self._tasks_combo.setEnabled(False)
        self._task_status_combo.setEnabled(False)

    def _add_status_item(self, index, name, color):
        self._task_status_combo.addItem(name)
        size = self._task_status_combo.style().pixelMetric(QStyle.PM_SmallIconSize)
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(color))
        self._task_status_combo.setItemData(index, pixmap, Qt.DecorationRole)

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

    def _on_task_selected(self, index):
        self._task_status_combo.clear()
        self._task_status_combo.setEnabled(False)

        shot_name = self._shots_combo.itemText(index)
        if not shot_name:
            return

        task_name = self._tasks_combo.currentText()
        if not task_name:
            return

        task_statuses = artellapipe.TasksMgr().get_all_task_statuses()
        for i, task_status in enumerate(task_statuses):
            self._add_status_item(i, task_status.name, task_status.color)
        self._task_status_combo.setEnabled(True)

        shot_task_status = artellapipe.TasksMgr().get_task_status_for_shot(shot_name, task_name)
        if not shot_task_status:
            return
        status_name = shot_task_status.name
        status_index = self._task_status_combo.findText(status_name, Qt.MatchExactly)
        if status_index == -1:
            return
        self._task_status_combo.setCurrentIndex(status_index)
