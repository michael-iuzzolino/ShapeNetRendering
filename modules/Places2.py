import os
import sys
import glob
import json
import numpy as np
import modules.utils
from torch.utils.data import Dataset

class Dataset(Dataset):
    def __init__(self, root, resize=True, dim=256, transforms=None):
        super().__init__()
        self.root = root
        self.resize = resize
        self.dim = dim
        self.transforms = transforms
        
        self._setup_paths()
    
    def _get_path_info(self, path):
        class_id = path.split(os.path.sep)[-3]
        if 'synset' in class_id.lower():
            class_id = int(class_id.split("_")[1])
        instance_id = path.split(os.path.sep)[-2]
        return class_id, instance_id
    
    def _setup_paths(self):
        print(f"Building image filepaths from {self.root}...")        
        self.filepaths = glob.glob(f'{self.root}/*/*')
        print("Path setup complete.")
        
    def __len__(self):
        return len(self.filepaths)

    def _load_img(self, path):
        img = imageio.imread(path)
        if self.resize:
            img = cv2.resize(img, (self.dim, self.dim))
        return img
    
    def __getitem__(self, idx):
        # Get path
        path_i = self.filepaths[idx]
        
        # Image
        img = modules.utils.read_image(path_i, parse_mask=False)
        
        if self.transforms:
            img = self.transforms(img)
            
        return img, path_i