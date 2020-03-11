class RenderHandlerHelpers(object):
    def AET_to_ROT(self, azimuth, elevation, theta):
        """Converts Azimuth, Elevation, Theta tuple into corresponding 4x4 Rotation Matrix
            
        """
        
        # Generate rotation matrices for each angle
        Tz_ROT = Matrix44.from_z_rotation(theta)
        Ex_ROT = Matrix44.from_x_rotation(elevation)
        Ay_ROT = Matrix44.from_y_rotation(azimuth)    
        
        # Apply transforms to obtain final 4x4 rotation matrix. 
        # NOTE: Order matters! Do not switch.
        rotation_matrix44 = Ay_ROT.dot(Ex_ROT).dot(Tz_ROT) 

        return rotation_matrix44

    def ROT_to_AET(self, R):
        """Recovers Azimuth, Elevation, and Theta angles from rotation matrix.
        NOTE: Currently DOES NOT work properly. Do not use.
        
        References
        ----------
            MATLAB source code: 
            https://github.com/robotology/mex-wholebodymodel/blob/master/mex-wholebodymodel/matlab/utilities/%2BWBM/%2Butilities/rotm2eul.m

            sequence = 'ZYX';
        """
        euler_return = np.zeros(3)

        R = R.astype(np.float32)

        if R[2,0] < 1:
            if R[2,0] > -1:
                euler_return[0] = np.arctan2(R[1,0], R[0,0])
                euler_return[1] = np.arcsin(-R[2,0])
                euler_return[2] = np.arctan2(R[2,1], R[2,2])
            else:
                euler_return[0] = -np.arctan2(-R[1,2], R[1,1])
                euler_return[1] = np.pi/2.0
                euler_return[2] = 0
        else:
            euler_return[0] = np.arctan2(-R[1,2], R[1,1])
            euler_return[1] = -np.pi/2.0
            euler_return[2] = 0

        # Euler return -> Z, Y, X
        # AET -> Y, X, Z
        # Therefore, roll -1
        euler_return = np.roll(euler_return, -1)

        return euler_return
    
    def __sample_from_textures(self, base_texture_dir, sample_textures_dir="dtd/images"):
        categories = glob2.glob("{}/{}/*".format(base_texture_dir, sample_textures_dir))
        sampled_category_dir = np.random.choice(categories)
        category_img_paths = glob2.glob("{}/*".format(sampled_category_dir))
        sampled_texture = np.random.choice(category_img_paths)
        return sampled_texture
    
class RenderHandler(RenderHandlerHelpers):
    """Wrapper over ModernGL for rendering Reference and Query images
    
    """
    def __init__(self, shader_dir, background_dir, viewport_width, viewport_height, backgroundHandler=None):
        
        super(RenderHandler, self).__init__()
        
        # Set background dir for background obj
        self._background_dir = background_dir
        self._backgroundHandler = backgroundHandler
        
        # Create the standalone context
        self.context = moderngl.create_standalone_context()

        # Enable depth test - this enables the depth buffer to detect depth
        self.context.enable(moderngl.DEPTH_TEST)
        
        # Load shaders
        with open(os.path.join(shader_dir, "shader.vert")) as infile:
            vertex_shader_source = infile.read()

        with open(os.path.join(shader_dir, "shader.frag")) as infile:
            fragment_shader_source = infile.read()
        
        # Create the program
        self.program = self.context.program(vertex_shader=vertex_shader_source, fragment_shader=fragment_shader_source)
        
        # Set the viewport and FBO
        self.set_viewport(viewport_width, viewport_height)
        
        self.previous_background_options = None
            
    def __get_img_from_fbo(self):
        """ Retrieves np Image from FBO """
        pixels = self.fbo.read(components=3, alignment=1)
        img = np.array(Image.frombytes('RGB', self.fbo.size, pixels).transpose(Image.FLIP_TOP_BOTTOM))
        return img
    
    def __render_background(self, options={}):
        """Renders the background of Query items
        
        Background may be texture (backgroundHandler used here)
        or may be randomly generated RGB color.
        """
        
        # Background Transform (DO NOT CHANGE)
        # -----------------------------------------------------------------------
        translate_vec = [0, 0, 0, 1]         # Set location of background object
        scale = 1.0                          # Set scale of background object
        background_transform = np.identity(4) * scale
        background_transform[:,3] = translate_vec
        # -----------------------------------------------------------------------

        # Randomly select background texture or random RGB coloring
        use_previous_background_opts = options.get('use_previous', False)
        if use_previous_background_opts: 
            options = self.previous_background_options
            texture_background = options["texture_background"]
        else:
            texture_prob = options.get("texture_prob", 0.5)
            texture_background = True if np.random.uniform() <= texture_prob else False
            options["texture_background"] = texture_background

        # Send uniforms to program
        # --------------------------------------------------------
        self.program['Transform'].write(background_transform.astype('float32').tobytes())
        self.program["AmbientLight"].value = options.get("ambient_light", 0.2)
        self.program['UseTexture'].value = texture_background
        self.program['NormColoring'].value = False
        # --------------------------------------------------------

        # Vertex buffer object
        obj_location = options.get("render_obj_dir", self._background_dir)
        background_model = ObjLoader.Obj.open('{}/model/background_plane.obj'.format(obj_location))
        packed_background = background_model.pack('vx vy vz nx ny nz tx ty tz')
        background_VBO = self.context.buffer(packed_background)

        # Vertex array object
        background_VAO = self.context.simple_vertex_array(self.program, background_VBO, 'in_vert', 'in_norm', 'in_text')

        # Apply texture or coloring
        if texture_background and self._backgroundHandler is not None:
            # Randomly sample a background texture
            dataset_key = options.get("dataset_key", "training")
            background_obj = options.get("backgroundHandler", self._backgroundHandler)
            random_preloaded_background = background_obj.sample(dataset_key)
            
            if use_previous_background_opts:
                random_preloaded_background = options["previous_background"]
            else:
                options["previous_background"] = random_preloaded_background

            # Get texture info, create render context texture and build mipmaps
            texture_image, texture_size, texture_bytes = random_preloaded_background
            background_texture = self.context.texture(size=texture_size, components=3, data=texture_bytes)
            background_texture.build_mipmaps()

            # Use the texture
            background_texture.use()

        # Randomly select RGB coloring if not texture
        else:
            if use_previous_background_opts:
                random_background_color = options["previous_background"]
            else:
                random_background_color = tuple([np.random.uniform() if i < 3 else 1.0 for i in range(4)])
                options["previous_background"] = random_background_color
                
            self.program['Color'].value = random_background_color

        # Render vertex array object
        background_VAO.render()

        # Release objects (otherwise memory leak issues)
        background_VAO.release()
        background_VBO.release()

        if texture_background:
            background_texture.release()
            
        if not use_previous_background_opts: 
            self.previous_background_options = options 
    
    def __render_CAD_model(self, packed_model, render_matrix44, options={}):
        base_texture_dir = options.get("textures_dir", None)
        apply_model_textures = options.get("apply_textures", False)
        model_textures = options.get("textures", []) 
        ambient_light = options.get("ambient_light", 0.2)
        model_color = options.get("color", (1.0, 1.0, 1.0, 0.5))
        apply_norm_color = options.get("norm_coloring", not apply_model_textures)

        # Send uniforms to self._program
        # --------------------------------------------------------
        self.program['Transform'].write(render_matrix44.astype('float32').tobytes())
        self.program["AmbientLight"].value = ambient_light
        self.program['Color'].value = model_color
        self.program['UseTexture'].value = apply_model_textures
        self.program['NormColoring'].value = apply_norm_color
        # --------------------------------------------------------

        # Setup textures
        # ----------------------------------------------------------------------------------
        if apply_model_textures:
            object_textures = []
            if model_textures is not None and len(model_textures) == 1:
                for model_texture in model_textures:
                    texture_image, texture_size, texture_bytes = model_texture
                    try:
                        object_texture = self.context.texture(texture_size, 3, texture_bytes)
                        object_texture.build_mipmaps()
                        object_textures.append(object_texture)
                    except:
                        continue
            else:
                texture_path = self.__sample_from_textures(base_texture_dir)
                with Image.open(texture_path) as im:
                    texture_image = im
                    texture_size = im.size
                    texture_bytes = im.tobytes()

                texture = self.context.texture(texture_size, 3, texture_bytes)
                texture.build_mipmaps()
                object_textures.append(texture)
        # ----------------------------------------------------------------------------------

        # Vertex buffer object
        object_VBO = self.context.buffer(packed_model)

        # Vertex array object
        object_VAO = self.context.simple_vertex_array(self.program, object_VBO, 'in_vert', 'in_norm', 'in_text')

        # Use the texture
        if apply_model_textures:
            for object_texture in object_textures:
                object_texture.use()

        # Render vertex array object
#         object_VAO.render(moderngl.LINE_STRIP, 400)
        object_VAO.render()

        # Release objects
        object_VAO.release()
        object_VBO.release()

        # Release model textures, if they exist
        if apply_model_textures:
            for obj_texture in object_textures:
                obj_texture.release()

        # Get the rendered image from fbo
        img = self.__get_img_from_fbo()

        return img
    
    def __render(self, packed_model, render_matrix44, rot_matrix33, model_opts={}, background_opts={}, light_position=(100, 100, 0)):
        
        # Clear context
        bg_color = background_opts.get("color", np.array([0.0, 0.0, 0.0]))
        self.context.clear(*bg_color)

        # Required for both the background and object - DO NOT REMOVE!
        self.program['NormalTransform'].write(rot_matrix33.tobytes()) # 3x3
        self.program['LightPos'].value = light_position

        # Render background, if applicable
        if background_opts.get("apply_textures", False): self.__render_background(background_opts)

        # Render object and get image
        img = self.__render_CAD_model(packed_model, render_matrix44, model_opts)

        return img
    
    def apply_scale_and_shift(self, rotation, scale, translation):
        """ Apply scale and shift transforms to rotation matrix """
        # Check correct shapes
        if rotation.shape[0] == 3:
            rotation = Matrix44.from_matrix33(rotation)

        if np.array(translation).shape[0] == 2:
            translation = np.array([*list(translation), 0])

        # Define Translate, if applicable
        translation_matrix44 = Matrix44.from_translation(translation)

        # Define scale Scale
        scale_matrix44 = Matrix44.from_scale(np.ones(3) * scale)

        # Set transformation
        transform_matrix44 = rotation.dot(scale_matrix44).dot(translation_matrix44)

        return transform_matrix44.astype(np.float32)
        
    def render_with_AET(self, model_obj, azimuth, elevation, theta, scale=1, distance=1, pascal_axis=True, translation=np.zeros(3), model_options={}, background_options={}):
        """ Render with AET """
        # Calculate ROT from aet
        rot_matrix44 = self.AET_to_ROT(azimuth, elevation, theta)
        rot_matrix33 = Matrix33.from_matrix44(rot_matrix44).astype(np.float32)

        # Get scale and shifted transform
        render_matrix44 = self.apply_scale_and_shift(np.copy(rot_matrix44), scale, translation)

        # Render
        required_params = {
            "packed_model"     : model_obj, 
            "render_matrix44"  : render_matrix44, 
            "rot_matrix33"     : rot_matrix33
        }
        render_img = self.__render(**required_params, model_opts=model_options, background_opts=background_options)
        
        if pascal_axis:
            render_img = render_img[:,::-1,:]
        
        return render_img, rot_matrix33
    
    def render_with_ROT(self, model_obj, ROT44, scale=1, translation=np.zeros(3), pascal_axis=True, time_speed=False, model_options={}, background_options={}):
        """ Render with rotation matrix """
        if time_speed:
            t0 = time.time()
            
            
        if ROT44.shape[0] == 3:
            temp = np.copy(ROT44)
            ROT44 = np.eye(4)
            ROT44[:3,:3] = temp

        # Already have ROT. Get scale and shifted transform
        render_matrix44 = self.apply_scale_and_shift(ROT44, scale, translation)

        # Get 33 rot representation
        rot_matrix33 = ROT44[:3,:3].astype(np.float32)

        # Render
        required_params = {
            "packed_model"     : model_obj, 
            "render_matrix44"  : render_matrix44, 
            "rot_matrix33"     : rot_matrix33
        }
        
        render_img = self.__render(**required_params, model_opts=model_options, background_opts=background_options)
        
        if pascal_axis:
            render_img = render_img[:,::-1,:]
        
        if time_speed:
            render_time = time.time() - t0
            return render_img, render_time
            
        return render_img
    
    def render_reference_img(self, packed_model, ROT33, scale=1, render_i=0, verbose=False):
        """ Simple render function used for timing the render """
        t0 = time.time()

        ROT44 = np.eye(4)
        ROT44[:3,:3] = ROT33

        # Define scale Scale
        scale_matrix44 = Matrix44.from_scale(np.ones(3) * scale)

        # Set transformation
        render_matrix44 = (ROT44 @ scale_matrix44).astype(np.float32)

        # Clear context
        self.context.clear(0,0,0)

        # Required for both the background and object - DO NOT REMOVE!
        self.program['NormalTransform'].write(render_matrix44[:3,:3].tobytes()) # 3x3
        self.program['LightPos'].value = (100, 100, 0)

        # Send uniforms to self._program
        # --------------------------------------------------------
        self.program['Transform'].write(render_matrix44.tobytes())
        self.program["AmbientLight"].value = 0.2
        self.program['Color'].value = (1,1,1,0.5)
        self.program['UseTexture'].value = False
        self.program['NormColoring'].value = True
        # --------------------------------------------------------

        # Vertex buffer object
        object_VBO = self.context.buffer(packed_model)

        # Vertex array object
        object_VAO = self.context.simple_vertex_array(self.program, object_VBO, 'in_vert', 'in_norm', 'in_text')

        # Render vertex array object
        tt = time.time()
        object_VAO.render()
        if verbose: print("\t\tActual render time: {:0.9f}".format(time.time()-tt))
            
        # Release objects
        object_VAO.release()
        object_VBO.release()

        # Get the rendered image from fbo
        tt = time.time()
        render_img = self.__get_img_from_fbo()
        if verbose: print("\t\tGet img from buffer: {:0.9f}".format(time.time()-tt))

        # Flip Axis
        render_img = render_img[:,::-1,:]

        t_total = time.time() - t0
        if verbose: print("\tRender {:2d} time: {:0.7f}".format(render_i+1, t_total))
        return render_img
    
    def set_viewport(self, viewport_width, viewport_height):
        """ Reset the viewport height/width"""
        # Frame buffer object
        self.fbo = self.context.framebuffer(
            self.context.renderbuffer((viewport_width, viewport_height)),
            self.context.depth_renderbuffer((viewport_width, viewport_height), )
        )

        # Binds the frame buffer
        self.fbo.use()