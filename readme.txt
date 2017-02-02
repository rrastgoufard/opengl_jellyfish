
Hello there!

This is my first attempt at pyopengl.  All
calculations are on the gpu, but all equations
are a simple function of time, not of any
previous state.  (I learned a way to do
state in my next attempt -- opengl_flower.)

This generates lots and lots of translucent
triangles that are on a spectrum between two
colors.  Colors can be specified or chosen
randomly.  (Random by default.  See the __main__
of jellyfish.py for more detail).  When multiple
triangles stack, they add luminosity instead
of blending together, so they appear very 
bright!  Some colors look garish together,
but others are really pleasing.

This needs python 2, pyopengl, numpy, and
pillow.  

You need a mouse and keyboard if you want to
interact with it.  There are two states,
zoom and rotate, that can be toggled by the
'r' key.  By default, you start in the zoom
state where dragging with the mouse zooms
in and out.  In the rotate state, dragging
with the mouse rotates the entire structure
around its center.  In either state, the
spacebar key resets back to default values.  
Note that entering the rotate state disables
the autorotation.  The only other notable
key is 0 for taking a screenshot.

There are no comments in the code.  I never
inteded for anyone to see this, but I decided
to make it public in case someone maybe gets
some enjoyment from it.  

