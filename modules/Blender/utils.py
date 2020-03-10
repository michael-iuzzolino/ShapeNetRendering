import os
import math
import numpy as np

_CMAP = [[0.83106498, 0.23844675, 0.30880431],
         [0.94732795, 0.412995  , 0.26643599],
         [0.97070358, 0.52741253, 0.3088812 ],
         [0.98869666, 0.65736255, 0.36885813],
         [0.99361784, 0.75540177, 0.44175317],
         [0.99546328, 0.84767397, 0.51926182],
         [0.99730873, 0.91657055, 0.60907343],
         [0.99915417, 0.97377932, 0.70503652],
         [0.97500961, 0.99000384, 0.7100346 ],
         [0.92887351, 0.9715494 , 0.63806228],
         [0.85659362, 0.94232987, 0.60530565],
         [0.73863899, 0.89434833, 0.62929642],
         [0.62283737, 0.84798155, 0.6438293 ],
         [0.49550173, 0.79815456, 0.64567474],
         [0.37600923, 0.73402537, 0.65813149],
         [0.28004614, 0.62698962, 0.70242215],
         [0.20622837, 0.52018454, 0.7349481 ],
         [0.28742791, 0.41499423, 0.68512111],
         [0.36862745, 0.30980392, 0.63529412]]

def setup_angles(args):
    # Azimuth
    azimuth_stepsize = 360.0 / args.views

    # Elevations
    # --------------------------------------------------------
    ele_step = 45.0/args.views
    quarter = int(math.ceil(args.views/4))
    elevations = []
    for i in range(quarter):
        direction = 1 if i % 2 == 0 else -1
        x_i = [direction*ele_step for _ in range(quarter)]

        elevations += x_i
    # --------------------------------------------------------
    return azimuth_stepsize, elevations

def setup_filepaths(scene, sensor_outputs, args):
    model_identifier = os.path.split(os.path.split(args.obj)[0])[1]
    filepath = os.path.join(args.output_folder, model_identifier)
    scene.render.image_settings.file_format = 'PNG'  # set output format to .png

    for sensor_key, sensor_output in sensor_outputs.items():
        sensor_output.base_path = ''

    return filepath

def modulate_cam_distance(azimuth_i, cam_amp=0.25, cam_shift=1.5, cam_phase=0.25):
    cam_dist = cam_amp*math.sin(math.radians(azimuth_i)/float(cam_phase)) + cam_shift
    return cam_dist

def euler_to_xyz(azimuth_i, normalize=True, z_phase=0.5, z_amp=0.5, z_shift=0.0):
    A = math.radians(azimuth_i)
    E = math.radians(azimuth_i)

    x = math.sin(A)
    y = math.cos(A)
    z = z_amp*math.sin(E/float(z_phase)) + z_shift
    if normalize:
        d = math.sqrt(x**2 + y**2 + z**2)
        x /= d
        y /= d
        z /= d
    return np.array([x, y, z])
