#version 120 
#extension GL_ARB_explicit_attrib_location : require

uniform float etime;
uniform float power;
uniform float inverted;
varying vec3 c;

layout( location = 0 ) varying out vec3 color;

void main() {
  color = vec3( 
    pow( c.r/20, power ),
    pow( c.g/20, power ),
    pow( c.b/20, power ) );
//   if( inverted >= 0.5 ) {
//     color.r = clamp( color.r, 0, 1 );
//     color.g = clamp( color.g, 0, 1 );
//     color.b = clamp( color.b, 0, 1 );
//     color = 1 - color;
// 
//     color.r = pow( color.r, 50 );
//     color.g = pow( color.g, 50 );
//     color.b = pow( color.b, 50 );
//   }
}