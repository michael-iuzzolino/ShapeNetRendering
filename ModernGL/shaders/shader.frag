#version 330

uniform vec3 LightPos;
uniform vec4 Color;
uniform float AmbientLight;
uniform bool NormColoring = false;
uniform bool UseTexture = false;
uniform sampler2D Texture;

in vec3 v_vert;
in vec3 v_norm;
in vec3 v_text;

out vec4 f_color;

void main() {

    if (NormColoring)
    {
        f_color = vec4(normalize(v_norm)*0.5 + 0.5, 1.0);
    }
    else
    {
        if (UseTexture)
        {
            float lum = dot(normalize(v_norm), normalize(v_vert - LightPos));
            lum = acos(lum) / 3.14159265;
            lum = lum * (1 - AmbientLight) + AmbientLight;  // apply ambient lighting
            lum = clamp(lum, 0.0, 1.0);

            vec3 color = texture(Texture, v_text.xy).rgb;
            color = color * (1.0 - Color.a) + Color.rgb * Color.a;
            f_color = vec4(color * lum, 1.0);
        }
        else
        {
            float lum = abs(1.0 - acos(dot(normalize(LightPos - v_vert), normalize(v_norm))) * 2.0 / 3.14159265);
            f_color = vec4(Color.rgb * sqrt(lum), 1.0);
        }
    }
}
