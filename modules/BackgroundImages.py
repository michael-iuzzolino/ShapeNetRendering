import os
import json
import glob
import imageio
import cv2
import numpy as np

class BackgroundHandler:
    def __init__(self, root, labels_root, eval_model='resnet', mode='include', classes_specified=[]):
        self.root = root
        self.labels_root = labels_root
        self.eval_model = eval_model
        self.mode = mode
        self.classes_specified = classes_specified
        
        self._setup()
        
    def _setup(self):
        print("Building image paths...")
        self.img_paths = glob.glob(f'{self.root}/*/*')
        
        if len(self.classes_specified) > 0:
            self._filter_img_paths_by_class()
    
    def _filter_img_paths_by_class(self):
        print("Loading labeled path lookup...")
        labels_path = os.path.join(self.labels_root, f'{self.eval_model}.json')
        with open(labels_path, 'r') as infile:
            load_data = json.load(infile)
        self.path_to_labels = {ele[2] : {"idx" : ele[0], "name" : ele[1]} for ele in load_data}
        
        num_missing_labels = 0
        # Filter Image Paths
        filtered_img_paths = []
        for img_path in self.img_paths:
            if img_path not in self.path_to_labels:
                num_missing_labels += 1
                filtered_img_paths.append(img_path)
                continue

            img_info = self.path_to_labels[img_path]
            img_in_classes_specified = False
            for class_to_exclude in self.classes_specified:
                if class_to_exclude in img_info['name']:
                    img_in_classes_specified = True
                    break
            
            if self.mode == 'include':
                if img_in_classes_specified:
                    filtered_img_paths.append(img_path)
            elif self.mode == 'exclude':
                if not img_in_classes_specified:
                    filtered_img_paths.append(img_path)
        
        diff = len(self.img_paths) - len(filtered_img_paths)
        
        print(f"Original: {len(self.img_paths):,} -- Final: {len(filtered_img_paths):,} -- Num Filtered: {diff:,}")
        if num_missing_labels:
            print(f"Evaluations incomplete. Missing {num_missing_labels:,} image labels.")
            
        self.img_paths = filtered_img_paths
            
        print("Finished setup.")
        
    def sample(self, img_shape=None):
        # Randomly sample background image
        background_path_i = np.random.choice(self.img_paths)
        
        # Load image
        background_img = imageio.imread(background_path_i)
        
        # Check for reshape
        if img_shape:
            background_img = cv2.resize(background_img, img_shape[:2][::-1])
            
        return background_img