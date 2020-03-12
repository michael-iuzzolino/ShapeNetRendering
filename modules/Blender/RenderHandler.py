# import os
# import sys
import bpy
import math

# dir = os.path.dirname(bpy.data.filepath)
# if dir not in sys.path:
#     sys.path.append(dir)

from modules.Blender.Camera import Camera
import modules.Blender.Occlusion
import modules.Blender.Model
import modules.Blender.Scene
import modules.Blender.Lights
import modules.Blender.utils

_SEMANTIC_RGB_COLOR = [1.0, 1.0, 1.0]

class BlenderRender:
    def __init__(self, args):
        self.args = args
        self._setup()

    def _setup(self):
        # Delete default cube
        for default_obj in ['Cube', 'Lamp']:
            bpy.data.objects[default_obj].select = True
            bpy.ops.object.delete()

        # Setup depth, normal, albedo sensors
        self.sensors = modules.Blender.Scene.Sensors(self.args)

        # Setup light
        self.lights = modules.Blender.Lights.Lights(self.args.lamp_mode)

        # Import model obj and cleanup
        self.target_model = modules.Blender.Model.ModelHandler(self.args, target=True, semantic_rgb_color=_SEMANTIC_RGB_COLOR)
        self.occlusions = modules.Blender.Occlusion.OcclusionHandler(self.args.n_occlusions)

        # Log colors
        if self.occlusions.active:
            modules.Blender.utils.log_color_mapping(self.target_model, self.occlusions, self.args.output_folder)

        # Setup scene
        self.scene = modules.Blender.Scene.setup(self.args)

        # Setup camera
        self.camera = Camera(self.scene, mode=self.args.camera_mode)

        # File output paths
        self.filepath = modules.Blender.utils.setup_filepaths(self.scene, self.sensors.outputs, self.args)

        # Init RGB model visibility
        self.target_model.show("RGB_model")
        self.occlusions.show()

    def run(self):
        if self.args.render_mode == 'demo':
            self._demo_rendering()

    def _demo_rendering(self):
        # Setup angles
        azimuth_stepsize, elevations = modules.Blender.utils.setup_angles(self.args)

        # Generate renders
        for i in range(self.args.views):
            azimuth_i = azimuth_stepsize * i

            # Stdout put
            print("Rotation {} DEG, {} RAD".format(azimuth_i, math.radians(azimuth_i)))

            # Set camera position
            self.camera.update(azimuth_i)

            # Update light
            self.lights.update(self.camera.cam_pos)

            self.target_model.translate()

            # Write sensor
            for sensor_key, sensor_output in self.sensors.outputs.items():
                sensor_output.file_slots[0].path = "{}_{}.png".format(self.scene.render.filepath, sensor_key)

            # Render RGBA without occlusion
            self.occlusions.hide()
            self.target_model.show("RGB_model")
            self.scene.render.filepath = "{}_r_{:03d}_RGBA_target".format(self.filepath, int(azimuth_i))
            bpy.ops.render.render(write_still=True)  # render still
            self.occlusions.show()

            # Check for active occlusions
            if self.occlusions.active:
                self.occlusions.colorize_materials()
                self.scene.render.filepath = "{}_r_{:03d}_RGBA_occluded".format(self.filepath, int(azimuth_i))
                bpy.ops.render.render(write_still=True)  # render still

                if self.args.render_semseg:
                    self.target_model.show("emission_model")
                    self.occlusions.emission_materials()
                    self.scene.render.filepath = "{}_r_{:03d}_RGBA_semseg".format(self.filepath, int(azimuth_i))
                    bpy.ops.render.render(write_still=True)  # render still
                    self.target_model.show("RGB_model")
