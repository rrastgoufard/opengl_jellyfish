 
#version 120
#extension GL_ARB_explicit_attrib_location : require

layout (location = 0) in vec2 v;
uniform float z; // z is the elapsed time.
uniform mat4 P;

varying out vec3 st;
varying out mat2 sincos;

void main() { 
//   st = vec3( 1.0*(v.xy)*(2.0 + 1.0*sin(2*3.14*z/60)), z);
  st = vec3( v.xy, z );         // 1x
//   st = vec3( 2*v.xy, z );       // 2x centered
  gl_Position = vec4( v.x, v.y, 0.0, 1.0 );
}