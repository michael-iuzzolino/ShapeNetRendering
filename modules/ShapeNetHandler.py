import os
import glob
import json
import numpy as np

class ShapeNetHandler(object):
    def __init__(self, root):
        self.root = root
        
        self._load_taxonomy()
        self._setup_folders()

    def _load_taxonomy(self):
        self.taxonomy_filepath = os.path.join(self.root, 'taxonomy.json')
        with open(self.taxonomy_filepath, 'r') as infile:
            self.taxonomy = json.load(infile)
            
        self.synset_to_name_lookup = {ele['synsetId'] : ele['name'] for ele in self.taxonomy}
    
    def _setup_folders(self):
        self.model_folders = [ele for ele in glob.glob(f'{self.root}/*') if 'json' not in ele]
        
        self.objs_paths = {}
        for model_folder in self.model_folders:
            synsetID = os.path.basename(model_folder)
            model_name = self.synset_to_name_lookup[synsetID]
            obj_paths = glob.glob(f'{model_folder}/*/models/*.obj')
            self.objs_paths[synsetID] = obj_paths
            
    def print_categories(self):
        for syn_id, name in self.synset_to_name_lookup.items():
            print(f"SynsetID: {syn_id} -- Name: {name}") 
    
    def sample_obj(self, category_name='', verbose=True):
        synsetIDs = [ele for ele in list(self.objs_paths.keys()) if category_name in self.synset_to_name_lookup[ele]]
        rand_synsetID = np.random.choice(synsetIDs)
        rand_name = self.synset_to_name_lookup[rand_synsetID]
        synsetID_objs = self.objs_paths[rand_synsetID]
        rand_obj_path = np.random.choice(synsetID_objs)
        instance_id = rand_obj_path.split(os.path.sep)[-3]
        if verbose:
            print(f"SynsetID: {rand_synsetID} -- InstanceID: {instance_id} -- Name: {rand_name}")
            
        return rand_obj_path, rand_synsetID, instance_id