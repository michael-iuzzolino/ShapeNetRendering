# A simple script that uses blender to render views of a single object by rotation the camera around it.
# Also produces depth map at the same time.
#
# Source: https://github.com/panmari/stanford-shapenet-renderer
#
# Example:
# blender --background --python mytest.py -- --views 10 /path/to/my.obj
#
import bpy

class Camera:
    def __init__(self, scene, mode='oscillation'):
        self.mode = mode

        # Grab camera from scene
        cam = scene.objects['Camera']

        # Init location
        cam.location = (0.0, 0.0, 0.0)

        # Setup constraints
        cam_constraint = cam.constraints.new(type='TRACK_TO')
        cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        cam_constraint.up_axis = 'UP_Y'

        # Setup target object on constraint (Currently not used)
        self.b_empty = self._create_parent_obj_to_camera(cam)
        cam_constraint.target = self.b_empty

    def _create_parent_obj_to_camera(self, cam):
        origin = (0, 0, 0)
        b_empty = bpy.data.objects.new("Empty", None)
        b_empty.location = origin
        cam.parent = b_empty  # setup parenting

        scn = bpy.context.scene
        scn.objects.link(b_empty)
        scn.objects.active = b_empty
        return b_empty

    def _look_at_origin(self):
        loc_camera = self.camera.matrix_world.to_translation()

        direction = -loc_camera
        # point the cameras '-Z' and use its 'Y' as up
        rot_quat = direction.to_track_quat('-Z', 'Y')

        # assume we're using euler rotation
        self.camera.rotation_euler = rot_quat.to_euler()

    def set_position(self, camera_points):
        # Reload camera -- maybe not necessary
        self.camera = bpy.data.objects['Camera']
        self._look_at_origin()
        self.camera.location = camera_points
        self._look_at_origin()

    def update_target(self, azimuth_update):
        self.b_empty.rotation_euler[2] += azimuth_update
