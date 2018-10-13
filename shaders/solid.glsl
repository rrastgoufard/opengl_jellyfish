#version 120
#extension GL_ARB_explicit_attrib_location : require

layout (location = 0) in vec3 v;
varying vec3 c;
uniform mat4 P;

void main() { 
  c = v;
  gl_Position = vec4(v.xy, -v.z, 1.0);
  gl_Position = P*gl_Position;
}