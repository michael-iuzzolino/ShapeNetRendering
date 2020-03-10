import bpy

_LAMP_2_ENERGY = 0.05 # 0.015

def setup(args):
    scene = bpy.context.scene
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.alpha_mode = 'TRANSPARENT'
    return scene

class Lights:
    def __init__(self):
        self.lamps = {}
        self._setup_point_lamp()
        self._setup_hemi_lamp()
        self._setup_backlight()

    def _setup_point_lamp(self):
        self.point_lamp_location = (0, 0, 2)
        bpy.ops.object.lamp_add(type='POINT', radius=1, view_align=False, location=self.point_lamp_location)
        point_lamp = bpy.data.lamps['Lamp']
        point_lamp.type = 'SUN'
        point_lamp.shadow_method = 'NOSHADOW'
        point_lamp.use_specular = False
        self.lamps['point'] = point_lamp

    def _setup_backlight(self):
        # Add another light source so stuff facing away from light is not completely dark
        bpy.ops.object.lamp_add(type='SUN')
        backlight_lamp = bpy.data.lamps['Sun']
        backlight_lamp.shadow_method = 'NOSHADOW'
        backlight_lamp.use_specular = False
        backlight_lamp.energy = _LAMP_2_ENERGY
        bpy.data.objects['Sun'].rotation_euler = bpy.data.objects['Point'].rotation_euler
        bpy.data.objects['Sun'].rotation_euler[0] += 180

        self.lamps['backlight'] = backlight_lamp

    def _setup_hemi_lamp(self):
        bpy.ops.object.lamp_add(type='POINT', radius=1, view_align=False, location=(0, 0, 2))
        hemi_lamp = bpy.data.lamps['Lamp']
        hemi_lamp.type = 'HEMI'
        hemi_lamp.shadow_method = 'NOSHADOW'
        hemi_lamp.use_specular = False
        self.lamps['hemi'] = hemi_lamp

    def move(self, new_position):
        lamp = bpy.data.objects['Point']
        lamp.location = new_position

class Sensors:
    def __init__(self, args):
        # Set up rendering of depth map.
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        links = tree.links

        # Add passes for additionally dumping albedo and normals.
        if args.depth or args.normal or args.albedo:
            bpy.context.scene.render.layers["RenderLayer"].use_pass_normal = True
            bpy.context.scene.render.layers["RenderLayer"].use_pass_color = True
            bpy.context.scene.render.image_settings.file_format = args.format
            bpy.context.scene.render.image_settings.color_depth = args.color_depth

        # Clear default nodes
        for n in tree.nodes:
            tree.nodes.remove(n)

        # Create input render layer node.
        render_layers = tree.nodes.new('CompositorNodeRLayers')

        outputs = {}
        if args.depth:
            depth_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
            depth_file_output.label = 'Depth Output'
            if args.format == 'OPEN_EXR':
                links.new(render_layers.outputs['Depth'], depth_file_output.inputs[0])
            else:
                # Remap as other types can not represent the full range of depth.
                map = tree.nodes.new(type="CompositorNodeMapValue")
                # Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
                map.offset = [-0.7]
                map.size = [args.depth_scale]
                map.use_min = True
                map.min = [0]
                links.new(render_layers.outputs['Depth'], map.inputs[0])
                links.new(map.outputs[0], depth_file_output.inputs[0])

            outputs['depth'] = depth_file_output

        if args.normal:
            scale_normal = tree.nodes.new(type="CompositorNodeMixRGB")
            scale_normal.blend_type = 'MULTIPLY'
            # scale_normal.use_alpha = True
            scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
            links.new(render_layers.outputs['Normal'], scale_normal.inputs[1])

            bias_normal = tree.nodes.new(type="CompositorNodeMixRGB")
            bias_normal.blend_type = 'ADD'
            # bias_normal.use_alpha = True
            bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
            links.new(scale_normal.outputs[0], bias_normal.inputs[1])

            normal_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
            normal_file_output.label = 'Normal Output'
            links.new(bias_normal.outputs[0], normal_file_output.inputs[0])

            outputs['normal'] = normal_file_output

        if args.albedo:
            albedo_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
            albedo_file_output.label = 'Albedo Output'
            links.new(render_layers.outputs['Color'], albedo_file_output.inputs[0])

            outputs['albedo'] = albedo_file_output

        self.outputs = outputs
