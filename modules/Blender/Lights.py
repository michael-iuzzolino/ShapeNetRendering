import bpy
import numpy as np

_LAMP_2_ENERGY = 0.05 # 0.015

class Lights:
    def __init__(self, mode, lamp_radius=5.0):
        self.mode = mode
        self.lamp_radius = lamp_radius
        self._setup_lamps()

    def _setup_lamps(self):
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

    def _move(self, new_position):
        lamp = bpy.data.objects['Point']
        lamp.location = new_position

    def update(self, cam_position):
        if self.mode == 'follow_camera':
            new_lamp_position = self.lamp_radius * np.array(cam_position)
            self._move(new_lamp_position)
        elif self.mode == 'random':
            # Randomly select new radius and position
            rand_lamp_radius = np.random.uniform(1.5, 10.5)
            rand_pos = np.random.uniform(0, 1, size=3)
            # Normalize
            rand_pos /= float(np.sqrt(np.sum(rand_pos**2)))
            random_position = rand_lamp_radius * rand_pos
            self._move(random_position)
        elif self.mode == 'stationary':
            pass
