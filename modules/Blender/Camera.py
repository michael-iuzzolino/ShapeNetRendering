import bpy
import numpy as np
import modules.Blender.utils

class Camera:
    def __init__(self, scene, mode='oscillation', cam_dist=1.25, modulate_distance=False):
        self.mode = mode
        self.cam_dist = cam_dist
        self.modulate_distance = modulate_distance

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

    def update(self, azimuth_i):
        if self.mode == 'oscillation':
            self.cam_pos = modules.Blender.utils.euler_to_xyz(azimuth_i, normalize=True)
            if self.modulate_distance:
                cam_dist = modules.Blender.utils.modulate_cam_distance(azimuth_i)
            else:
                cam_dist = self.cam_dist

            self.set_position(cam_dist * self.cam_pos)
        elif self.mode == 'random':
            # Randomly select new radius and position
            rand_cam_dist = np.random.uniform(1.5, 7.5)
            self.cam_pos = np.random.uniform(0, 1, size=3)
            # Normalize
            self.cam_pos /= float(np.sqrt(np.sum(self.cam_pos**2)))
            random_position = rand_cam_dist * self.cam_pos
            self.set_position(random_position)
