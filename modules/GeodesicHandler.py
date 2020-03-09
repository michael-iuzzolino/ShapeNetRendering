import glob
import numpy as np
from itertools import combinations
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class GeodesicHandler(object):
    def __init__(self, geodesic_dir):
        self.geodesic_dir = geodesic_dir
        self._get_geodesic_options()
        
    def _get_geodesic_options(self):
        """
            Print the available geodesic obj files
        """
        geodesic_obj_paths = [ele for ele in glob.glob("{}/*.obj".format(self.geodesic_dir))]
        self.geodesic_options = {}
        print("Geodesic Objs")
        for geo_i, geodesic_obj in enumerate(geodesic_obj_paths, 1):
            with open(geodesic_obj, "r") as infile:
                geodesic_data = infile.readlines()

            # Parse out the vertex points in the obj file
            cartesian_points = np.array([list(map(np.float32, d.strip().split()[1:])) for d in geodesic_data if "v " in d])
            num_points = len(cartesian_points)
            self.geodesic_options[num_points] = {
                "dir"                        : geodesic_obj,
                "cartesian_points" : cartesian_points,
                "num_points"                 : num_points
            }
            print("{}. Num points: {:3d} -- Dir: {}".format(geo_i, num_points, geodesic_obj))
        print("Select with <obj>.set_geodesic(<num_geodesic_points>)")
        
    def set_geodesic(self, num_points):
        """
            Set the geodesic object and calculate
                1. Reference cartesian points
                2. Reference spherical points
        """
        selected_opt = self.geodesic_options[num_points]
        
        print("Selected {}-point Geodesic Obj at {}".format(selected_opt["num_points"], selected_opt["dir"]))
        
        # Extract reference cartesian points from selected option
        self.cartesian_points = selected_opt["cartesian_points"]
        
        # Calculate the speherical points
        self.calculate_spherical_points()
                
        # Set values
        self.num_geodesic_points = selected_opt["num_points"]
        
        # Generate AET points
        self.generate_AET_points()
        
    def __calculate_unit_vector(self, vector):
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector)
    
    def __calculate_angle_between(self, v1, v2):
        """ Returns the angle in radians between vectors 'v1' and 'v2':: """
        v1_u = self.__calculate_unit_vector(v1)
        v2_u = self.__calculate_unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
    
    def add_AET_noise(self, aet_point, point_noise):
        """ Adds noise to AET point """
        # calculate new azimuth, elevation, and thetas
        amp = (self.nearest_neighbor_angle / 2) * point_noise # radians
        random_point = aet_point - amp * (0.5 - np.random.random(aet_point.shape))

        return random_point
    
    def cart2sphere(self, x, y, z):
        """ Convert cartestian (x,y,z) to spherical (r, azimuth, theta) """
        r = np.sqrt(x**2 + y**2 + z**2)
        azimuth = np.arctan2(y, x)             # Phi
        elevation = np.arctan2(np.sqrt(x**2 + y**2), z) - np.pi/2
        
        return np.array([r, azimuth, elevation])
    
    def sphere2cart(self, r, azimuth, elevation):
        """ Convert spherical (r, azimuth, theta) to cartestian (x,y,z) """
        x = r * np.sin(elevation) * np.cos(azimuth)    
        y = r * np.sin(elevation) * np.sin(azimuth)    
        z = r * np.cos(elevation)
        
        return np.array([x, y, z])
    
    def __minimum_angle_separation(self):
        """ Calculate the minimum angle of separation between neighboring points """
        vec_combs = combinations(self.cartesian_points, 2)
        angles = [self.__calculate_angle_between(*vec_comb) for vec_comb in vec_combs]
        self.nearest_neighbor_angle = np.min(angles)
        
    def calculate_spherical_points(self):
        """ Convert all geodesic obj's cartesian points into spherical points """
        self.spherical_points = np.zeros_like(self.cartesian_points)
        for point_i, (x, y, z) in enumerate(self.cartesian_points):
            self.spherical_points[point_i] = self.cart2sphere(x, y, z)
        
        # Calculate minimum angle separation
        self.__minimum_angle_separation()
        
    def generate_AET_points(self):
        """ Generate all AET points """
        # Calculate number of AET points (AE * T)
        self.num_aet_points = self.spherical_points.shape[0] * self.num_thetas
                
        self.AET_points = np.zeros((self.num_aet_points, 3))
        render_i = 0
        for r, azimuth, elevation in self.spherical_points:
            for theta in self.theta_range:
                self.AET_points[render_i] = np.array([azimuth, elevation, theta])
                render_i += 1
    
    def set_thetas(self, num_thetas):
        """ Set the thetas """
        degree_increment = 360 / num_thetas
        init_theta_range = np.arange(0, 360, degree_increment)
        self.theta_range = np.array([np.radians(ele) for ele in init_theta_range])
        self.num_thetas = self.theta_range.shape[0]

    def sample_AET(self):
        return self.AET_points[np.random.randint(self.num_aet_points)]
    
    def find_nearest_geodesic_point_AET(self, AET_src, renderHandler):
        """ Find nearest geodesic AET to AET_src (used for Pascal3d AETs) """
        R_src = renderHandler.AET_to_ROT(*AET_src)[:3,:3]
        traces = []
        for point in self.AET_points:
            point_R = renderHandler.AET_to_ROT(*point)[:3,:3]
            R = np.dot(R_src, point_R.T)
            R_trace = np.matrix.trace(R)
            traces.append(R_trace)
        max_idx = np.argmax(traces)
        nearest_AET = self.AET_points[max_idx]
        return nearest_AET, max_idx
    
    def visualize_noise_factors(self, target_noise=None):
        """ Visualize the mean/max angle noise generated from different point_noise factors """
        point_noises = np.linspace(0, 10, 501)
        y = []
        for point_noise in point_noises:
            av_diffs = []
            max_diffs = []

            for aet in self.AET_points:
                noisy_aet = self.add_AET_noise(aet, point_noise=point_noise)
                diff = np.abs(noisy_aet - aet)
                av_diff = np.mean(diff)
                max_diff = np.max(diff)
                av_diffs.append(av_diff)
                max_diffs.append(max_diff)

            av_diffs = np.mean(av_diffs)
            max_diffs = np.max(max_diffs)

            if target_noise is not None and np.abs(target_noise - point_noise) < 1e-2:
                target_mean = np.degrees(av_diffs)
                target_max = np.degrees(max_diffs)

                print('Target Mean: {} -- Max: {}'.format(target_mean, target_max))

            y.append([np.degrees(av_diffs), np.degrees(max_diffs)])
        y = np.array(y)
        plt.plot(point_noises, y[:,0], label="Mean")
        plt.plot(point_noises, y[:,1], label="Max")
        if target_noise is not None:
            plt.plot([target_noise], [target_mean], 'ro')
            plt.plot([target_noise], [target_max], 'ro')
        plt.legend()
        plt.xlabel("Point Noise")
        plt.ylabel("Theta Noise")
        
    def visualize_points(self, test_recovery=False, target_point=None, target_size=150, highlight_aet=None, highlight_size=150):
        """ Visualize the geodesic sphere """
        X_self = self.cartesian_points[:,0]
        Y_self = self.cartesian_points[:,1]
        Z_self = self.cartesian_points[:,2]
        
        fig = plt.figure(figsize=(9, 9))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(X_self, Y_self, Z_self, 'b')
        ax.scatter([0], [0], [0], 'r', s=200)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_zlabel('Z axis')

        if highlight_aet is not None:
            highlight_point = self.sphere2cart(*highlight_aet)
            ax.scatter([highlight_point[0]], [highlight_point[1]], [highlight_point[2]], 'b', s=highlight_size, label="Nearest AET")
            
        if target_point is not None:
            ax.scatter([target_point[0]], [target_point[1]], [target_point[2]], 'r', s=target_size, label="Pascal AET")

        if test_recovery:
            tests_points = np.zeros_like(self.spherical_points)
            for point_i, sphere_point in enumerate(self.spherical_points):
                tests_points[point_i] = self.sphere2cart(*sphere_point)

            X_recover = tests_points[:,0]
            Y_recover = tests_points[:,1]
            Z_recover = tests_points[:,2]

            ax.scatter(X_recover, Y_recover, Z_recover, 'r')
        
        plt.legend(loc='upper left', numpoints=1, ncol=3, fontsize=8, bbox_to_anchor=(0, 0))
        