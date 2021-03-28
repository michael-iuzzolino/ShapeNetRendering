import os
import sys
import glob
import json
import numpy as np
import modules.utils
from torch.utils.data import Dataset

class Dataset(Dataset):
    def __init__(self, root, background_handler=None, 
                 background_active=True, mode_key='generate', 
                 transforms=None, debug=False):
        super().__init__()
        self.root = root
        self.background_handler = background_handler
        self.mode_key = mode_key
        self.background_active = background_active
        self.transforms = transforms
        self.debug = debug
        
        self._setup_paths()
    
    def _get_path_info(self, path):
        class_id = path.split(os.path.sep)[-3]
        if 'synset' in class_id.lower():
            class_id = int(class_id.split("_")[1])
        instance_id = path.split(os.path.sep)[-2]
        return class_id, instance_id
    
    def _setup_paths(self):
        print(f"Building shapenet data filepaths from {self.root}...")
        self.filepaths = glob.glob(f'{self.root}/{self.mode_key}/BLENDER_RENDER/*/*/*_target.png')
        print("Path setup complete.")
        
    def __len__(self):
        return len(self.filepaths)

    def _load_img(self, path):
        img = imageio.imread(path)
        return img
    
    def __getitem__(self, idx):
        # Get path
        path_i = self.filepaths[idx]
        
        # Image
        img, mask = modules.utils.read_image(path_i, parse_mask=True)
        
        if self.background_active:
            # Sample background image
            background_img = self.background_handler.sample(img.shape)

            # Add background image
            img = modules.utils.add_background(img, mask, background_img)
        
        # Labels
        class_id, instance_id = self._get_path_info(path_i)
        
        if self.debug:
            img = self.background_handler.sample(img.shape)
            
            
        if self.transforms:
            img = self.transforms(img)
            
        return img, class_id, instance_id
    
class Handler(object):
    def __init__(self, root):
        self.root = root
        
        self._load_taxonomy()
        self._setup_folders()
        
    def align_with_shapenet(self, imagenet_idx_to_labels, verbose=False):
        for label_idx, imagenet_label in enumerate(imagenet_idx_to_labels):
            if verbose:
                sys.stdout.write(f'\rLabel idx {label_idx} : {imagenet_label}')
                sys.stdout.flush()
                
            for synset_id, synset_vals in self.synset_to_name_lookup.items():
                namelist = synset_vals['names']
                imagenet_label_parts = imagenet_label.split("_")
                for imagenet_label_part in imagenet_label_parts:
                    if imagenet_label_part in namelist:
                        if verbose:
                            print("\nFound: ", imagenet_label_part)
                        self.synset_to_name_lookup[synset_id]['imagenet_idx'] = label_idx
                        break

    def _load_taxonomy(self):
        self.taxonomy_filepath = os.path.join(self.root, 'taxonomy.json')
        print(f"Loading taxonomy from {self.taxonomy_filepath}...")
        with open(self.taxonomy_filepath, 'r') as infile:
            self.taxonomy = json.load(infile)
        
        print("Building synset to name lookup.")
        self.synset_to_name_lookup = {ele['synsetId'] : {"names" : ele['name'], "imagenet_idx" : None} for ele in self.taxonomy}
    
    def _setup_folders(self):
        print("Setting up model folders")
        self.model_folders = [ele for ele in glob.glob(f'{self.root}/*') if 'json' not in ele]
        
        self.objs_paths = {}
        for i, model_folder in enumerate(self.model_folders):
            sys.stdout.write(f'\rLoading folder {model_folder} [{i+1}/{len(self.model_folders)}]...')
            sys.stdout.flush()
            synsetID = os.path.basename(model_folder)
            model_name = self.synset_to_name_lookup[synsetID]["names"]
            obj_paths = glob.glob(f'{model_folder}/*/models/*.obj')
            self.objs_paths[synsetID] = obj_paths
        print("\n")
        
    def lookup_name(self, synset_id):
        try:
            synset_id = int(synset_id)
            # Synset ID has 8 digits, left-zero padded
            synset_id = f"{synset_id:08d}"
            model_name = self.synset_to_name_lookup[synset_id]["names"]
            imagenet_id = self.synset_to_name_lookup[synset_id]["imagenet_idx"]
        except:
            print("Excepts int or string-int representation!")
            model_name = None
            imagenet_id = None
        return model_name, imagenet_id
    
    def print_categories(self):
        for syn_id, syn_vals in self.synset_to_name_lookup.items():
            name = syn_vals["names"]
            print(f"SynsetID: {syn_id} -- Name: {name}") 
    
    def sample_obj(self, category_name=''):
        synsetIDs = [ele for ele in list(self.objs_paths.keys()) if category_name in self.synset_to_name_lookup[ele]["names"]]
        rand_synsetID = np.random.choice(synsetIDs)
        rand_name = self.synset_to_name_lookup[rand_synsetID]["names"]
        synsetID_objs = self.objs_paths[rand_synsetID]
        rand_obj_path = np.random.choice(synsetID_objs)
        instance_id = rand_obj_path.split(os.path.sep)[-3]

        return rand_obj_path, rand_synsetID, instance_id, rand_name