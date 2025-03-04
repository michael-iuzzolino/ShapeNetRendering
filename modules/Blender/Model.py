import bpy
import glob
import mathutils
import numpy as np

class ModelHandler:
    def __init__(self, args, target, semantic_rgb_color=[1.0,1.0,1.0]):
        self.args = args
        self.target = target
        self.semantic_rgb_color = semantic_rgb_color

        # Load model - specify as RGB model
        RGB_model = self._import_model_obj(args, target=target)

        # Fix mesh
        self._modify_mesh(RGB_model, args)

        # Create emission model as copy with new mats from RGB model
        emission_model = self._make_emission_model()

        # Assign models to lookup
        self.model_objects = {"RGB_model" : RGB_model, "emission_model" : emission_model}
        self.prev_translation = None

    def _make_emission_model(self):
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'},
                                      TRANSFORM_OT_translate={"value":(0,0,0),
                                                              "constraint_axis":(False, False, False),
                                                              "constraint_orientation":'GLOBAL',
                                                              "mirror":False,
                                                              "proportional":'DISABLED',
                                                              "proportional_edit_falloff":'SMOOTH',
                                                              "proportional_size":1,
                                                              "snap":False,
                                                              "snap_target":'CLOSEST',
                                                              "snap_point":(0, 0, 0),
                                                              "snap_align":False,
                                                              "snap_normal":(0, 0, 0),
                                                              "gpencil_strokes":False,
                                                              "texture_space":False,
                                                              "remove_on_cancel":False,
                                                              "release_confirm":False,
                                                              "use_accurate":False})
        objects = []
        for object in bpy.context.selected_objects:
            object.name = 'emission_model__{}'.format(object.name)
            objects.append(object)

        emission_mat = self._make_emission_material()
        self._set_material(objects, emission_mat)

        """ Currently broken - just use blender_render for segmentation """
        # if self.args.render_mode == 'CYCLES':
        #     self._create_emission_nodes(objects)
        # else:
        #     emission_mat = self._make_emission_material()
        #     self._set_material(objects, emission_mat)

        return objects

    def _create_emission_nodes(self, objects):
        """
            # CURRENTLY BROKEN!
        """
        for object in objects:
            old_materials = object.data.materials
            old_materials.clear()

            # Create a new material
            material = bpy.data.materials.new(name="Plane Light Emission Shader")
            material.use_nodes = True

            # Remove default
            material.node_tree.nodes.remove(material.node_tree.nodes.get('Diffuse BSDF'))
            material_output = material.node_tree.nodes.get('Material Output')
            emission = material.node_tree.nodes.new('ShaderNodeEmission')
            emission.inputs['Strength'].default_value = 500.0

            # link emission shader to material
            material.node_tree.links.new(material_output.inputs[0], emission.outputs[0])

            # set activer material to your new material
            object.active_material = material

    def _set_material(self, objects, material):
        for object in objects:
            bpy.context.scene.objects.active = object
            if len(object.data.materials) == 1:
                object.data.materials[0] = material
            elif len(object.data.materials) > 1:
                for i in range(len(object.data.materials)):
                    object.data.materials[i] = material

    def _make_emission_material(self):
        emission_mat = bpy.data.materials.new(name="Material")
        emission_mat.diffuse_color = self.semantic_rgb_color
        emission_mat.diffuse_shader = 'LAMBERT'
        emission_mat.use_shadeless = True
        return emission_mat

    def _import_model_obj(self, args, target=False):
        if target:
            bpy.ops.import_scene.obj(filepath=args.obj)
        else:
            if args.occlusion_obj_root != '':
                obj_paths = glob.glob("{}/*/models/*.obj".format(args.occlusion_obj_root))
                occlused_object_path = np.random.choice(obj_paths)
            else:
                occlused_object_path = args.obj
            bpy.ops.import_scene.obj(filepath=occlused_object_path)

        # When object loaded, all parts are selected by default
        # Iterate over selected objects and rename
        # Accumulate Model objects
        objects = []
        for object in bpy.context.selected_objects:
            object.name = 'RGB_model__{}'.format(object.name)
            objects.append(object)

        return objects

    def _modify_mesh(self, objects, args):
        for object in objects:
            bpy.context.scene.objects.active = object
            if args.recompute_norms:
                bpy.ops.object.mode_set(mode='EDIT')

                # bpy.ops.mesh.select_all(action='SELECT')
                # bpy.ops.mesh.flip_normals()
                # bpy.ops.mesh.select_all(action='DESELECT')

                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.normals_make_consistent()
                bpy.ops.mesh.select_all(action='DESELECT')

                # bpy.ops.mesh.select_all(action='SELECT')
                # bpy.ops.mesh.normals_make_consistent()
                # bpy.ops.mesh.select_all(action='DESELECT')

                bpy.ops.object.mode_set(mode='OBJECT')
            if args.scale != 1:
                # bpy.ops.transform.resize(value=(1, 1, 1), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='ENABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
                bpy.ops.transform.resize(value=(args.scale,args.scale,args.scale))
                bpy.ops.object.transform_apply(scale=True)
            if args.remove_doubles:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.remove_doubles()
                bpy.ops.object.mode_set(mode='OBJECT')
            if args.edge_split:
                bpy.ops.object.modifier_add(type='EDGE_SPLIT')
                bpy.context.object.modifiers["EdgeSplit"].split_angle = 1.32645
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="EdgeSplit")

    def translate(self):
        rand_pos = lambda : np.random.uniform(-0.25, 0.25)
        translation_delta = mathutils.Vector((rand_pos(), rand_pos(), rand_pos()))

        if self.prev_translation is not None:
            for model_key, model_objects in self.model_objects.items():
                for object in model_objects:
                    object.location -= self.prev_translation

        for model_key, model_objects in self.model_objects.items():
            for object in model_objects:
                object.location += translation_delta

        self.prev_translation = translation_delta

    def hide(self, model_key):
        for obj in self.model_objects[model_key]:
            obj.hide_render = True

    def show(self, model_key):
        for obj in self.model_objects[model_key]:
            obj.hide_render = False

        # Hide other model
        other_key_idx = 1-list(self.model_objects.keys()).index(model_key)
        other_key = list(self.model_objects.keys())[other_key_idx]
        self.hide(other_key)
