#version 120
#extension GL_ARB_explicit_attrib_location : require

layout (location = 0) in vec3 v;
varying vec3 c;
uniform float etime;
uniform mat4 P;

uniform vec2 dims;
// dims.x stores the aspect ratio W / H
// dims.y stores whether we use points or lines

const float pi = 3.1415;

// // Blue Orange
// const vec3 c1 = vec3( 0.85, 0.37, 0.05 );
// const vec3 c2 = vec3( 0.01, 0.42, 0.90 );

// // Gray Orange Red
// const vec3 c1 = 0.25*vec3( 0.95, 0.5, 0.05 );
// const vec3 c2 = vec3( 0.35, 0.5, 0.35 );

const vec3 c1 = vec3([=[c1r]=], 
                     [=[c1g]=],
                     [=[c1b]=]);
const vec3 c2 = vec3([=[c2r]=], 
                     [=[c2g]=],
                     [=[c2b]=]);

// // Purple Gray
// const vec3 c1 = 0.25*vec3( 0.55, 0.05, 0.55 );
// const vec3 c2 = vec3( 0.35, 0.5, 0.35 );

// // Seafoam Green
// const vec3 c1 = 0.6*vec3( 0.25, 0.65, 0.65 );
// const vec3 c2 = 0.6*vec3( 0.25, 0.65, 0.25 );

// // Sprite (Inverted, #glBlendFunc())
// // Dark Sprite (Inverted, glBlendFunc())
// const vec3 c1 = 6.0*vec3( 0.45, 0.00, 0.95 );
// const vec3 c2 = 12.0*vec3( 0.95, 0.25, 0.95 );

void main() { 
  float x = v.x;
  float y = v.y;
  float fx = 1-cos(2*pi*etime/12);
  float fy = 1-cos(2*pi*etime/10);
  float z = sin(2*pi*x*fx) + cos(pi*y*fy+pi/16);
  float swig = 0.5*fx*sin(2*pi*etime*v.z*2);
  float cwig = 0.5*fy*cos(2*pi*etime*v.z);
  float spread = (swig*swig + cwig*cwig)/2;
  z = (z + 1) / 2;

//   // Make it stay in pure form, no spreading
//   cwig = 1;
//   swig = 1;
//   spread = -10;
//   fx = 0;
//   fy = 0;

  c  = (z*c2 + (1-z)*c1);
  c *= (1-spread)*0.15;
  c *= (2-0.8*fx);
  c *= (2-0.8*fy);
  z = z * (x + y);
  
  gl_Position = vec4(
    (x - 1) + 0.05*cwig*(1-dims.y),
    (y - 1) + 0.035*swig*(1-dims.y),
    -(z - 1.0)*0.15,
    1.0 );
  x = gl_Position.x;
  y = gl_Position.y;
  
  // wrap the grid into a weird circle/helix thing
  float rad = x + 
    0.1*sin(2*pi*x*4*
      (1-0.25*cos(etime*pi/4)));
  float the = y*pi*0.75*(1+0.05*cos(etime*pi));

  gl_Position.xy = vec2(rad*cos(the),rad*sin(the));
  gl_Position.z *= 2;
  gl_Position.z += 0.025*cwig;
  gl_Position = P*gl_Position;

  gl_Position.z = atan(gl_Position.z) / 1.57;
  gl_Position.y = gl_Position.y * dims.x;

//   if( dims.y > 0 ){
//     float maxx = 1.0;
//     float maxy = 1.0;
// //     if( dims.x > 1 ){  // if wider than tall,
// //       maxy = 1.0/dims.x; // maxy is smaller than 1.
// //     } else {
// //       maxy = 1.0/dims.x;
// //     }
//     if( gl_Position.x > maxx ) { 
//       gl_Position.x -= 2*maxx; }
//     if( gl_Position.y > maxy ) { 
//       gl_Position.y -= 2*maxy; }
//     if( gl_Position.x < -maxx ) { 
//       gl_Position.x += 2*maxx; }
//     if( gl_Position.y < -maxy ) { 
//       gl_Position.y += 2*maxy; }
//   }
}