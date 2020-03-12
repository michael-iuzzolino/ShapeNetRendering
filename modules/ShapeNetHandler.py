import os
import sys
import glob
import json
import numpy as np

class ShapeNetHandler(object):
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
        with open(self.taxonomy_filepath, 'r') as infile:
            self.taxonomy = json.load(infile)
            
        self.synset_to_name_lookup = {ele['synsetId'] : {"names" : ele['name'], "imagenet_idx" : None} for ele in self.taxonomy}
    
    def _setup_folders(self):
        self.model_folders = [ele for ele in glob.glob(f'{self.root}/*') if 'json' not in ele]
        
        self.objs_paths = {}
        for model_folder in self.model_folders:
            synsetID = os.path.basename(model_folder)
            model_name = self.synset_to_name_lookup[synsetID]["names"]
            obj_paths = glob.glob(f'{model_folder}/*/models/*.obj')
            self.objs_paths[synsetID] = obj_paths
     
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