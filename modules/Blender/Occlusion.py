# A simple script that uses blender to render views of a single object by rotation the camera around it.
# Also produces depth map at the same time.
#
# Source: https://github.com/panmari/stanford-shapenet-renderer
#
# Example:
# blender --background --python mytest.py -- --views 10 /path/to/my.obj
#
import os
import sys
import argparse
import bpy
import math
import glob
import numpy as np
from modules.Blender.utils import _CMAP

class OcclusionHandler:
    def __init__(self, args):
        self.args = args
        self.active = args.occlude
        self.num_occlusions = args.n_occlusions
        self._generate_unique_rgb_colors()
        self._setup()

    def _generate_unique_rgb_colors(self):
        # Setup unique colors for semantic seg
        interval = math.floor(len(_CMAP)//self.num_occlusions)
        self.unique_rgb_colors = _CMAP[::interval]

    def _setup(self):
        if self.active:
            self.objs = [OccluderObj(i, self.unique_rgb_colors[i]) for i in range(self.num_occlusions)]
        else:
            self.objs = []

    def colorize_materials(self):
        """ Materials for RGB occlusion render """
        for obj in self.objs:
            obj.set_material('color')

    def emission_materials(self):
        """ Materials for instance segmentation render """
        for obj in self.objs:
            obj.set_material('emission')

    def hide(self):
        for obj in self.objs:
            obj.hide()

    def show(self):
        for obj in self.objs:
            obj.show()

    def get_colors(self):
        colors = {obj.id : obj.semantic_rgb_color for obj in self.objs}
        return colors

class OccluderObj:
    def __init__(self, id, rgb_color):
        self.id = 'Object_{}'.format(id)
        self.semantic_rgb_color = rgb_color

        self._create_object()
        self._generate_materials(rgb_color)
        self.set_material('transparent')

    def _create_object(self):
        # https://blender.stackexchange.com/questions/24133/modify-obj-after-import-using-python
        trans_mag = 0.2
        scale = np.clip(np.random.normal(0.085, 0.001), 0.01, 0.15) #, uniform(0.01, 0.15)
        random_translation = np.random.uniform(-trans_mag, trans_mag, size=3)
        if np.random.uniform() < 0.5:
            bpy.ops.mesh.primitive_cube_add(radius=1, view_align=False, enter_editmode=False, location=(0,0,0))
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(view_align=False, enter_editmode=False, location=(0,0,0))
        bpy.ops.transform.resize(value=(scale, scale, scale), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
        bpy.ops.transform.translate(value=random_translation, constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)

        object = bpy.context.selected_objects[0]
        self.object = object

    def _generate_materials(self, rgb_color):
        transparent_mat = bpy.data.materials.new(name="Material")
        transparent_mat.use_transparency = True
        transparent_mat.transparency_method = 'MASK'
        transparent_mat.alpha = 0

        # RGB occlusion render
        color_mat = bpy.data.materials.new(name="Material")
        color_mat.diffuse_color = rgb_color
        color_mat.diffuse_shader = 'LAMBERT'
        color_mat.diffuse_intensity = 0.5

        # Instance segmentation colors
        emission_mat = bpy.data.materials.new(name="Material")
        emission_mat.diffuse_color = rgb_color
        emission_mat.diffuse_shader = 'LAMBERT'
        emission_mat.use_shadeless = True

        self.materials = {"transparent" : transparent_mat, "color" : color_mat, "emission" : emission_mat}

    def set_material(self, material_key):
        material = self.materials[material_key]

        if len(self.object.data.materials):
            # assign to 1st material slot
            self.object.data.materials[0] = material
        # if there is no material append it
        else:
            self.object.data.materials.append(material)

    def hide(self):
        self.object.hide_render = True

    def show(self):
        self.object.hide_render = False
