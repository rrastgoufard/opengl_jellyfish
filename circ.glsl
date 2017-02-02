 
#version 130 
#extension GL_ARB_explicit_attrib_location : require

in vec3 st;
uniform mat2 sincos2;
uniform float box;
uniform sampler2D tex;
uniform float inverted;
uniform float vignette;
uniform vec2 dims;

out vec4 color;

void main() {
  
//   float pi = 3.1415926535897932384626433832795;
  float pi = 3.14159;
  
//   float off = 0.0;  // set to 0.5 to center
//   float off = 0.5;
//   vec2 pull = (st+1) / 2;
//   vec2 pull = st.xy - off;

  vec2 pull = (st.xy + 1) / 2.0;
//   vec2 pull = st.xy;

  float a = 1.0;
  color = texture2D( tex, pull );
  color = vec4(
    pow( color.r, a ),
    pow( color.g, a ),
    pow( color.b, a ),
    1.0 );

  int N = 4;
  vec2 dx = vec2( 1, 0 );
  vec2 dy = vec2( 0, 1 );

// // Try strange offset replication!
//   a = 0.5*(1-cos(st.z*2*3.14/10));
//   color += texture2D( tex, pull + a*dx ) / N;
//   color += texture2D( tex, pull + a*dy ) / N;
//   color += texture2D( tex, pull - a*dx ) / N;
//   color += texture2D( tex, pull - a*dy ) / N;

// Try blurring!
  float den = (N)*(N);
//   if( inverted < 0.5 )
//     den = (N+2)*(N+2);
  vec4 color2 = texture2D(tex, pull)*4/den;
//   vec4 color2 = vec4(0.0);
  vec2 dw = vec2( 8.0/1920, 8.0/1080 );
  for( int i = 1; i <= N; i++ ) {
    for( int j = 1; j <= N; j++ ) {
      color2 += texture2D( tex, 
        pull + i*dw.x*dx + j*dw.y*dy )/den;
      color2 += texture2D( tex, 
        pull - i*dw.x*dx + j*dw.y*dy )/den;
      color2 += texture2D( tex, 
        pull + i*dw.x*dx - j*dw.y*dy )/den;
      color2 += texture2D( tex, 
        pull - i*dw.x*dx - j*dw.y*dy )/den;
    }
  }

  // I can invert the colors because I'm reading
  // from a texture now.  :D
  if( inverted > 0.5 ) {
    color = 1 - color;
    color2 = 1 - color2;
  }

  float r = length(st.xy);
  float e = 1.0 / (1 + exp((r-1.0)*5));

//   float bint = 0;
//   float bflo = modf( st.z, bint );
//   float aint = 0;
//   float aflo = modf( st.z/8, aint );

  // // If you want to have the grid rotate 
  // // continuously, use this.
//   float alpha = st.z/8*pi/4;
//   float fade = 1;

  // // If you want to have the grid rotate on
  // // clock ticks, then use this version.
//   float alpha = (mod(aint,8)+pow(aflo,32))*pi/4;
  float fade = 1;

  // // If you want the grid rotations to fade
  // // in and out on transition, use this.
//   float alpha = mod(aint,8)*pi/4;
//   float fade = 1-pow(abs(cos(pow(aflo,1)*pi)),32);

  // // box controls the number of pixels that 
  // // the grid cells cover.  
//   float box = 100*(-cos((bint+pow(bflo,1))*2*pi/120)+2);
//   float box = 10*(-cos((bint+pow(bflo,1))*2*pi/360)+3);

  // // Center the grid.
  vec2 glxy = gl_FragCoord.xy - dims/2;

  // // This distorts the grid so that it is 
  // // no longer square.  (Think of sine waves
  // // intersecting and coloring the regions.)
//   glxy = glxy + vec2( 50*cos(glxy.y/50), 50*sin(glxy.x/50) );

  // // This allows the grid to rotate to an
  // // arbitrary angle alpha.
//   mat2 A = mat2(cos(alpha),-sin(alpha),sin(alpha),cos(alpha));
  vec2 tt = sincos2 * glxy;
  float tx = mod( tt.x, box ) / box;
  float ty = mod( tt.y, box ) / box;
  float t = pow(tx * ty, 1.0) * fade;
  
//   t = max(t,(1-pow(e,-(vignette*vignette))));
  if(vignette > 0.1){
//     t = max(t,0.7);
    t = 1;
  }

  color = t*color + (1-t)*color2;
  color = color*pow(e,vignette);
} 
