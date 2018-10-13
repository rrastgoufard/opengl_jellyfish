#version 120 
uniform float etime;
uniform float power;
varying vec3 c;
void main() {
  gl_FragColor = vec4( c, 1.0 );
} 
