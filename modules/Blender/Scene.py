import bpy
import numpy as np

def setup(args):
    # Set render engine
    try:
        bpy.context.scene.render.engine = args.render_engine.upper()
    except:
        bpy.context.scene.render.engine = "BLENDER_RENDER"

    scene = bpy.context.scene
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.alpha_mode = 'TRANSPARENT'
    return scene

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
