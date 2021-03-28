import torchvision

class UnNormalize(object):
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, tensor):
        """
        Args:
            tensor (Tensor): Tensor image of size (C, H, W) to be normalized.
        Returns:
            Tensor: Normalized image.
        """
        for t, m, s in zip(tensor, self.mean, self.std):
            t.mul_(s).add_(m)
            # The normalize code -> t.sub_(m).div_(s)
        return tensor
    
def load_imagenet_transformations():
    # Source: https://pytorch.org/docs/stable/torchvision/models.html
    # All pre-trained models expect input images normalized in the same way, 
    # i.e. mini-batches of 3-channel RGB images of shape (3 x H x W), 
    # where H and W are expected to be at least 224. 
    # The images have to be loaded in to a range of [0, 1] and 
    # then normalized using mean = [0.485, 0.456, 0.406] and std = [0.229, 0.224, 0.225]. 
    # You can use the following transform to normalize:
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    fixed_normalize_transform = torchvision.transforms.Normalize(mean=mean, std=std)
    fixed_denormalize_transform = UnNormalize(mean=mean, std=std)
    
    return {"normalize" : fixed_normalize_transform, "denormalize" : fixed_denormalize_transform}