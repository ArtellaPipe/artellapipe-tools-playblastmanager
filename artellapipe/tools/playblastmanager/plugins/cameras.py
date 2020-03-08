#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Playblast Time Range Plugin
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import traceback
import logging.config

from Qt.QtWidgets import *

from tpDcc.libs.python import python

import tpDcc as tp

from artellapipe.tools.playblastmanager.core import plugin

if tp.is_maya():
    import tpDcc.dccs.maya as maya

LOGGER = logging.getLogger()


class CamerasWidget(plugin.PlayblastPlugin, object):
    """
    Allows user to select the camera to generate playblast from
    """

    id = 'Camera'
    collapsed = True

    def __init__(self, project, config, parent=None):
        super(CamerasWidget, self).__init__(project=project, config=config, parent=parent)

        self._on_set_active_camera()
        self._on_update_label()

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 0, 5, 0)

        return main_layout

    def ui(self):
        super(CamerasWidget, self).ui()

        self.cameras = QComboBox()
        self.cameras.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cameras.setMinimumWidth(200)

        self.get_active = QPushButton('Get Active')
        self.get_active.setToolTip('Set camera from currently active view')
        refresh_icon = tp.ResourcesMgr().icon('refresh')
        self.refresh = QPushButton()
        self.refresh.setMaximumWidth(25)
        self.refresh.setIcon(refresh_icon)
        self.refresh.setToolTip('Refresh the list of cameras')
        self.refresh.setStatusTip('Refresh the list of cameras')

        for widget in [self.refresh, self.cameras, self.get_active]:
            self.main_layout.addWidget(widget)

    def setup_signals(self):
        self.get_active.clicked.connect(self._on_set_active_camera)
        self.refresh.clicked.connect(self._on_refresh)
        self.cameras.currentIndexChanged.connect(self._on_update_label)

    def validate(self):
        """
        Overrides base ArtellaPlayblastPlugin validate function
        Will ensure that widget outputs are valid and will raise proper errors if necessary
        :return: list<str>
        """

        errors = list()
        camera = self.cameras.currentText()
        if not tp.Dcc.object_exists(camera):
            errors.append('{0} : Selected Camera "{1}" does not exists!'.format(self.id, camera))
            self.cameras.setStyleSheet('border 1px solid red;')
        else:
            self.cameras.setStyleSheet('')

        return errors

    def get_outputs(self):
        """
        Overrides base ArtellaPlayblastPlugin get_outputs function
        Returns the outputs variables of the Playblast widget as dict
        :return: dict
        """

        camera_id = self.cameras.currentIndex()
        camera = str(self.cameras.itemText(camera_id)) if camera_id != -1 else None

        return {'camera': camera}

    def select_camera(self, camera):
        """
        Selects the given camera node
        :param camera: str
        """

        if camera:
            cameras = tp.Dcc.node_long_name(node=camera)
            if not cameras:
                return
            cameras = python.force_list(cameras)
            camera = cameras[0]
            for i in range(self.cameras.count()):
                value = str(self.cameras.itemText(i))
                if value == camera:
                    self.cameras.setCurrentIndex(i)
                    return

    def _get_camera(self):
        """
        Internal function that returns current camera
        :return: str
        """

        if tp.is_maya():
            panel = maya.cmds.getPanel(withFocus=True)
            if maya.cmds.getPanel(typeOf=panel) == 'modelPanel':
                cam = maya.cmds.modelEditor(panel, query=True, camera=True)
                if cam:
                    if maya.cmds.nodeType(cam) == 'transform':
                        return cam
                    elif maya.cmds.objectType(cam, isAType='shape'):
                        parent = maya.cmds.listRelatives(cam, parent=True, fullPath=True)
                        if parent:
                            return parent[0]

            cam_shapes = maya.cmds.ls(sl=True, type='camera')
            if cam_shapes:
                return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=True)[0]

            transforms = maya.cmds.ls(sl=True, type='transform')
            if transforms:
                cam_shapes = maya.cmds.listRelatives(transforms, shapes=True, type='camera')
                if cam_shapes:
                    return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=True)[0]
        else:
            return None

    def _on_set_active_camera(self):
        """
        Internal callback function that is called when a camera is set
        """

        camera = self._get_camera()
        self._on_refresh(camera=camera)
        if tp.is_maya():
            maya.cmds.optionVar(sv=['{}_playblast_camera'.format(self._project.name.lower()), camera])
        # if tp.Dcc.object_exists(camera):
        #     cmds.select(camera)

    def _on_update_label(self):
        """
        Internal callback function that updates the text of the camera label
        """

        camera = self.cameras.currentText()
        camera = camera.split('|', 1)[-1]
        self.label = 'Camera ({})'.format(camera)
        self.labelChanged.emit(self.label)

        self.validate()

    def _on_refresh(self, camera=None):
        """
        Internal callback function that refreshes of current cameras in the scene and emit proper signal if necessary
        :param camera: str, if camera nave is given, it will try to select this camera after refresh
        """

        cam = self.get_outputs()['camera']
        if camera is None:
            index = self.cameras.currentIndex()
            if index != -1:
                camera = self.cameras.currentData()

        self.cameras.blockSignals(True)
        try:
            self.cameras.clear()
            camera_shapes = tp.Dcc.list_nodes(node_type='camera')
            camera_transforms = tp.Dcc.shape_transform(camera_shapes)
            camera_shorts = [tp.Dcc.node_short_name(camera_xform) for camera_xform in camera_transforms]
            for full_path, short_name in zip(camera_transforms, camera_shorts):
                self.cameras.addItem(short_name, userData=full_path)
            self.select_camera(camera)
            self.cameras.blockSignals(False)
        except Exception as e:
            self.cameras.blockSignals(False)
            LOGGER.error('{} | {}'.format(e, traceback.format_exc()))

        if cam != self.get_outputs()['camera']:
            camera_index = self.cameras.currentIndex()
            self.cameras.currentIndexChanged.emit(camera_index)
            # self.cameras.setCurrentIndex(camera_index)
