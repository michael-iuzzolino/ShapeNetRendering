import imageio
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import animation
from IPython.display import HTML

matplotlib.rcParams['animation.embed_limit'] = 2**32

import torch
from torchvision.utils import make_grid

def stack_all_imgs(all_imgs, nrow=2):
    all_imgs_np = np.array([np.array(ele) for ele in all_imgs])
    all_imgs_pt = torch.tensor(all_imgs_np).permute(1,0,4,2,3)
    stacked_imgs = []
    for img_t in all_imgs_pt:
        padding = int(img_t.shape[2]*0.01)
        row_im = make_grid(img_t, nrow=nrow, pad_value=255, padding=padding).permute(1,2,0).numpy()
        stacked_imgs.append(row_im)
    return stacked_imgs

def combine_imgs(imgs):
    combined_imgs = []
    for img_i, (rgb, seg) in enumerate(imgs):
        rgb_pt = torch.tensor(rgb).permute(2,0,1)
        seg_pt = torch.tensor(seg).permute(2,0,1)
        padding = int(rgb_pt.shape[1]*0.01)
        row_img = make_grid(torch.stack([rgb_pt, seg_pt], axis=0), pad_value=255, padding=padding)
        row_img = row_img.permute(1,2,0).numpy()
        combined_imgs.append(row_img)
    return combined_imgs

def read_image(path, same_size=True):
    image = imageio.imread(path)
    img_RGB = image[:,:,:3]
    img_segmentation = image[:,:,3]
    if same_size:
        img_segmentation = np.repeat(img_segmentation[..., np.newaxis], img_RGB.shape[-1], axis=2)
    return img_RGB, img_segmentation

def toAnimation(imgs, *args, **kwargs):
    animator = FrameAnimator(imgs, *args, **kwargs)
    
    animation_obj = animator()
    if kwargs.get("savepath", False):
        save_path = kwargs['savepath']
        print(f"Saving to {save_path}...")
        animator.save(save_path, kwargs.get('fps', 15))
    
    print("Fin.")
    return animation_obj
    
class FrameAnimator(object):
    def __init__(self, imgs, interval=100, blit=True, text=None, figsize=(6,6), mode='jsHTML', **kwargs):
        self.mode = mode
        
        # Compute cmap
        # ----------------------------------------------------
        if len(imgs[0].shape) == 2 or imgs[0].shape[-1] == 1:
            cmap = 'gray'
        else:
            cmap = None
        # ----------------------------------------------------
        
        # Setup figure
        fig, ax = plt.subplots(1, figsize=figsize)
        
        # Init image 0
        img_0 = imgs[0]
        if img_0.shape[-1] == 1:
            img_0 = np.repeat(img_0, 3, axis=2)
            
        video_img = ax.imshow(img_0, cmap=cmap)
        ax.axis('off')

        def init():
            img_0 = imgs[0]
            if img_0.shape[-1] == 1:
                img_0 = np.repeat(img_0, 3, axis=2)
            video_img.set_array(np.zeros_like(img_0))
            return (video_img,)

        def animate(i):
            img_i= imgs[i]
            if img_i.shape[-1] == 1:
                img_i = np.repeat(img_i, 3, axis=2)
            
            video_img.set_array(img_i)
            
            text_str = f' -- {text[i]}' if text is not None else ""
            ax.set_title(f"Frame {i+1}/{len(imgs)} {text_str}")
            
            return (video_img,)
        
        plt.tight_layout()
        plt.close() # prevent fig from showing
        
        print("Building animator...")
        self.anim = animation.FuncAnimation(fig, animate, 
                                       init_func=init, 
                                       frames=len(imgs),
                                       interval=interval, # delay between frames in ms (25FPS=25 f/s * 1 s/1000ms = 0.025 f/ms)
                                       blit=blit)
        
    def __call__(self):
        print("Generating animation object...")
        if self.mode == 'HTML':
            anim_obj = HTML(self.anim.to_html5_video())
        elif self.mode == 'jsHTML':
            anim_obj = HTML(self.anim.to_jshtml())
        return anim_obj
    
    def _init_mp4_writer(self, fps):
        Writer = animation.writers['ffmpeg']
        self.writer = Writer(fps=fps, metadata=dict(artist='Me'), bitrate=1800)
        
    def save(self, save_path, fps=15): 
        if save_path.endswith('gif'):
            self.anim.save(save_path, writer='imagemagick', fps=fps)
        else:
            self._init_mp4_writer(fps)
            self.anim.save(save_path, writer=self.writer)