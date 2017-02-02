from __future__ import print_function

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import sys
import os
import time
import errno

from PIL import Image

from OpenGL.arrays import vbo
from OpenGL.GL import shaders
import numpy as np

# Following http://pyopengl.sourceforge.net/
#             context/tutorials/shader_1.xhtml
# I had to adapt it already because a built-in
# model view matrix is not provided any more in
# GLSL.  

# MODERN OPENGL TUTORIAL...
# http://www.arcsynthesis.org/gltut/
#   Basics/Tut02%20Vertex%20Attributes.html

# Use this stackoverflow response for
# glsl 330 to 130 conversion.
# http://stackoverflow.com/questions/
#   20161057/opengl-3-glsl-compatibility-mess

# Follow these tutorials.
# http://www.opengl-tutorial.org/

def chain( As ):
  Aout = As.pop()
  for A in As[::-1]:
    Aout = np.dot( A, Aout )
  return Aout

class Context():

  WW, HH = (1920, 1080)
  W, H = (750, 750)

  # we want to make posters of size 24x18.  There
  # is one inch of padding, so the printable
  # area is 23x17.
  # We want about 3500 pixels in width.  The
  # GPU cannot make an image of higher resolution.
  PW = 23
  PH = 17
  dpi = 150
  WW, HH = (PW*dpi, PH*dpi)

  asp = 1.0*W / H  

  fullscreen = True
  #fullscreen = False
  inverted = True
  points = True
  lines = False
  
  usetexture = True
  
  Nx, Ny = 1080, 120
  
  fstring = "{:>12.2f} frames per second. {}."
  
  last_fps = 0   # last fps time
  nframes = 1
  tscale = 8.0   # loop magnitude
  tloop = 180.0  # total loop duration
  
  def get_time(self):
    return np.float64(time.time()) - self.tstart
  
  fps = 60.0
  fpsr = 60.0
  renderstart = 0.0
  renderend = 0.0
  renderdelta = 0.0
  
  #thetax0 = np.pi/8
  #thetay0 = -np.pi/4
  thetax0 = 0
  thetay0 = 0
  thetax, dtx = thetax0, 0.05
  thetay, dty = thetay0, 0.25
  thetaz, dtz = 0.0, 0.15
  #a = 0.5
  mousethetax = 0
  mousethetay = 0
  thickscale = 0.0

  autorotate = True
  #autorotate = False
  
  def init_selfies( self ):
    #self.thickness = 0.5
    if self.autorotate:
      #if self.points:
        #self.a = 4.0
      #if self.lines:
        #self.a = 5*0.5
      self.a = 1.25
    else:
      self.thetax = self.thetax0
      self.thetay = self.thetay0
      #self.thetax = 0.0
      #self.thetay = 0.0
      self.thetaz = 0.0
      self.mousethetax = 0.0
      self.mousethetay = 0.0

  def __init__(self, 
               name="",
               W=None,
               H=None,
               c1=[0.2375,0.125,0.0125],
               c2=[0.35,0.5,0.35],
               usetexture=True,
               vignette=0,
               snaptimes=[],
               ):
    glutInit()
    self.tstart = time.time()
    self.t = self.get_time()
    
    self.name = name
    
    if snaptimes:
      if W and H:
        self.WW = W
        self.HH = H
    
    self.c1=c1
    self.c2=c2
    print("The two colors are:\n{}\n{}\n".format(
      self.c1, self.c2))
    
    self.vignette=vignette
    
    self.usetexture = usetexture
  
    self.snaptimes = snaptimes
    if self.snaptimes:
      self.snaptimes = [0] + self.snaptimes
      self.fullscreen = False
      self.W, self.H = self.WW, self.HH
    self.last_window = self.W, self.H
    self.init_selfies()

    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)
    glutInitWindowSize(self.W, self.H)
    glutInitWindowPosition(0, 0)
    self.window = glutCreateWindow( "bubbles" )
    glutSetOption(
      GLUT_ACTION_ON_WINDOW_CLOSE,
      GLUT_ACTION_CONTINUE_EXECUTION)
    
    
    self.getGLData()
    
    if self.fullscreen:
      self.fullscreen = not self.fullscreen
      self.togglefullscreen()
      
    self.downs = {}
    
    self.loadShaders()
    self.loadUniforms()
    self.loadData()
    self.loadBuffers(self.WW, self.HH, new=True)
      
    glutDisplayFunc(self.Render)
    glutIdleFunc(self.Render)
    glutReshapeFunc(self.ResizeGL)
    
    glutKeyboardFunc( self.keyPressed )
    glutKeyboardUpFunc( self.keyReleased )
    glutMouseFunc( self.mouseFunc )
    glutMotionFunc( self.mouseMotion )
    glutPassiveMotionFunc( self.mousePassive )
    glutMainLoop()
    
  def getGLData( self ):
    print( "{}\n{}\nGL {}\nGLSL {}\n".format(
      glGetString( GL_VENDOR ),
      glGetString( GL_RENDERER ),
      glGetString( GL_VERSION ),
      glGetString(GL_SHADING_LANGUAGE_VERSION) ) )
    print( "max!", glGetIntegerv(
      GL_MAX_TEXTURE_SIZE ) )
    print()
    
  def loadData( self ):
    # Load the egg carton's grid into a
    # vertex buffer object.
    xr = np.linspace( 0, 2, self.Nx )
    yr = np.linspace( 0, 2, self.Ny )
    xx,yy = np.meshgrid( xr, yr )
    xx = np.reshape( xx, [-1, 1] )
    yy = np.reshape( yy, [-1, 1] )
    offs = np.random.random( xx.shape )
    poses = np.hstack( [xx, yy, offs] )
    poses = np.array( poses, 'f' )
    self.N = len(poses)
    print( "There are", self.N, "points.\n" )
    self.grid = vbo.VBO( poses )  
    
    # Load the three coordinate arrows.
    a = np.hstack( [np.zeros([3,3]),np.eye(3)] )
    self.arrows = vbo.VBO( np.array(a,"f") )
    
    # Draw a square!
    a = np.array( [
      [-1, -1],
      [ 1, -1],
      [-1,  1],
      [ 1,  1] ], "f" )
    self.quad = vbo.VBO( a )
    
  def loadShaders( self ):
    files = [
      "vertex", "frag", 
      "solid", "classic", 
      "quad", "circ",
      
      #add varying keyword for nvidia
      "frag_nv", "quad_nv", 
      ]
    glsls = {}
    for f in files:
      fname = "{}.glsl".format(f)
      with open( fname, "r" ) as fin:
        s = fin.read()
        if "vertex" in fname:
          c1, c2 = self.c1, self.c2
          s = template(s,
            c1r=c1[0],c1g=c1[1],c1b=c1[2],
            c2r=c2[0],c2g=c2[1],c2b=c2[2],
            )
        glsls[f] = s

    try:
      ss = [ 
        shaders.compileShader(
          glsls["vertex"], GL_VERTEX_SHADER), 
        shaders.compileShader(
          glsls["frag_nv"], GL_FRAGMENT_SHADER)
      ]
    except:
      ss = [ 
        shaders.compileShader(
          glsls["vertex"], GL_VERTEX_SHADER), 
        shaders.compileShader(
          glsls["frag"], GL_FRAGMENT_SHADER)
      ]
    self.carton = shaders.compileProgram( *ss )
    
    ss = [ 
      shaders.compileShader(
        glsls["solid"], GL_VERTEX_SHADER), 
      shaders.compileShader(
        glsls["classic"], GL_FRAGMENT_SHADER)
    ]
    self.arrow = shaders.compileProgram( *ss )
    
    try:
      ss = [ 
        shaders.compileShader(
          glsls["quad"], GL_VERTEX_SHADER), 
        shaders.compileShader(
          glsls["circ"], GL_FRAGMENT_SHADER)
      ]
    except:
      ss = [ 
        shaders.compileShader(
          glsls["quad_nv"], GL_VERTEX_SHADER), 
        shaders.compileShader(
          glsls["circ"], GL_FRAGMENT_SHADER)
      ]
    self.squad = shaders.compileProgram( *ss )
    
  def loadUniforms( self ):
    self.etimeU = glGetUniformLocation(
      self.carton, "etime")
    self.PU = glGetUniformLocation(
      self.carton, "P")
    self.upower = glGetUniformLocation(
      self.carton, "power" )
    self.udims = glGetUniformLocation(
      self.carton, "dims" )
    self.ci = glGetUniformLocation(
      self.carton, "inverted" )
    print( "Carton Uniforms" )
    print( "  etime", self.etimeU )
    print( "  dims", self.udims )
    print( "  P", self.PU )
    print( "  power", self.upower )
    print( "  inverted", self.ci )
      
    self.PUa = glGetUniformLocation(
      self.arrow, "P" )
    print( "Arrow Uniforms" )
    print( "  P", self.PUa )
      
    self.PUq = glGetUniformLocation( 
      self.squad, "P" )
    self.zu = glGetUniformLocation(
      self.squad, "z" )
    self.sqi = glGetUniformLocation(
      self.squad, "inverted" )
    self.vign = glGetUniformLocation(
      self.squad, "vignette" )    
    self.sincos = glGetUniformLocation(
      self.squad, "sincos2" )
    self.boxsize = glGetUniformLocation(
      self.squad, "box" )
    self.dims = glGetUniformLocation(
      self.squad, "dims" )
    print( "Squad Uniforms" )
    print( "  P", self.PUq )
    print( "  z", self.zu )
    print( "  inverted", self.sqi )
    print( "  vignette", self.vign )
    print( "  sincos", self.sincos )
    print( "  boxsize", self.boxsize )
    print( "  dims", self.dims )
    
  def specifyBuffer(self, tW, tH, 
                    fb,
                    tex,
                    depthbuffer,
                    attach,):
      
    glBindFramebuffer(GL_FRAMEBUFFER, fb)
    
    # Create a texture
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexImage2D( 
      GL_TEXTURE_2D,    # target
      0,                # level?
      GL_RGB,           # internal format
      tW,               # width
      tH,               # height
      0,                # border
      GL_RGB,           # format (not internal?)
      GL_UNSIGNED_BYTE, # type
      None)             # null pointer
    
    # Disable interpolation so that the pixels
    # look correct.  (Is that the reason?)
    interp = GL_NEAREST
    glTexParameteri( 
      GL_TEXTURE_2D, 
      GL_TEXTURE_MAG_FILTER, 
      interp )
    glTexParameteri( 
      GL_TEXTURE_2D, 
      GL_TEXTURE_MIN_FILTER, 
      interp )
    
    # Create a depth buffer
    glBindRenderbuffer( GL_RENDERBUFFER, 
      depthbuffer )
    glRenderbufferStorage( GL_RENDERBUFFER,
      GL_DEPTH_COMPONENT, tW, tH )
    glFramebufferRenderbuffer( GL_FRAMEBUFFER,
      GL_DEPTH_ATTACHMENT,
      GL_RENDERBUFFER,
      depthbuffer ) 
      
    # Configure the framebuffer
    glFramebufferTexture2D( 
      GL_FRAMEBUFFER,
      attach,
      GL_TEXTURE_2D,
      tex, 
      0 )
    glDrawBuffer(attach)
    print( "Configured!", tW, tH )
    
    
  def loadBuffers( self, tW, tH, new=False ):
    """
    This entire function is copypasta from
    opengl-tutorial.org's render to texture.
    """
    
    # Create a framebuffer
    if new:
      self.framebuffer = glGenFramebuffers(1)
      self.tex = glGenTextures(1)
      self.depthbuffer = glGenRenderbuffers(1)
      print("self.tex")
      print("  Framebuffer", self.framebuffer)
      print("  Texture", self.tex)
      print("  Depthbuffer", self.depthbuffer)
      
    self.specifyBuffer(
      tW, tH,
      self.framebuffer,
      self.tex,
      self.depthbuffer,
      GL_COLOR_ATTACHMENT0)
    
    if new:
      self.screenbuffer = glGenFramebuffers(1)
      self.screentex = glGenTextures(1)
      self.screendepthbuffer = glGenRenderbuffers(1)
      print("self.screentex")
      print("  Framebuffer", self.screenbuffer)
      print("  Texture", self.screentex)
      print("  Depthbuffer", self.screendepthbuffer)      
      
    self.specifyBuffer(
      tW, tH,
      self.screenbuffer,
      self.screentex,
      self.screendepthbuffer,
      GL_COLOR_ATTACHMENT1)
    
  def keyPressed( self, key, *args ):
    #print( "key pressed:", args )
    if key == '\x1b':
      #sys.exit(0)
      glutLeaveMainLoop()
    elif key == 'p':
      self.points = not self.points
      self.lines = not self.lines
    elif key == ' ':
      self.init_selfies()
    elif key == 'i':
      self.inverted = 1.0 - self.inverted
    elif key == 'f':
      self.togglefullscreen()
    elif key == 't':
      self.usetexture = not self.usetexture
    elif key == '0':
      self.writePNG()
    else:
      self.autorotate = not self.autorotate
      print( "autorotation", self.autorotate )
        
  def keyReleased( self, *args ):
    pass
    
  def mouseFunc( self, *args ):
    #print( "mouse func:", args, self.a )
    if len(args) == 4:
      self.downs[args[0]] = args[1]
      self.mousex, self.mousey = args[2:]
    
  def mouseMotion( self, x, y ):
    self.mouseFunc( "mouse motion:", x, y )
    # diff = 2 * (self.mousey - y > 0) - 1
    dx = x - self.mousex
    dy = y - self.mousey
    
    dx = np.clip( dx, -10, 10 )
    dy = np.clip( dy, -10, 10 )
    
    if self.autorotate:
      self.a += -dy/100.0*np.exp(self.a/5.0)
      self.a = np.clip( self.a, 0.25, 5 )
    
    if not self.autorotate:
      # n pixels should be d degrees.
      n = 10
      d = 5
      self.mousethetax += 1.0*dx/n*d*np.pi/180
      self.mousethetay += -1.0*dy/n*d*np.pi/180
      self.mousethetay = np.clip( 
        self.mousethetay, -np.pi/2, np.pi/2 )
        
    self.mousex, self.mousey = x, y
    
  def mousePassive( self, *args ):
    self.mouseFunc( "mouse passive:", *args )
    
  def reshapeFunc( self, *args ):
    print( "reshape:", args )
    self.Render( *args )
    
  def rotate( self, tx, ty, tz ):
    
    # XZ rotation (about the Y axis)
    theta = ty
    P1 = np.array( [
      [np.cos(theta), 0, -np.sin(theta), 0],
      [0, 1, 0, 0],
      [np.sin(theta), 0, np.cos(theta), 0],
      [0, 0, 0, 1] ] )
    
    # XY rotation (about the Z axis)
    theta = tz
    P2 = np.array( [
      [np.cos(theta), -np.sin(theta), 0, 0],
      [np.sin(theta), np.cos(theta), 0, 0],
      [0, 0, 1, 0],
      [0, 0, 0, 1] ] )
    
    # YZ rotation (about the X axis)
    theta = -tx
    P3 = np.array( [
      [1, 0, 0, 0],
      [0, np.cos(theta), -np.sin(theta), 0],
      [0, np.sin(theta), np.cos(theta), 0],
      [0, 0, 0, 1] ] )
    
    return chain( [P3, P2, P1] )
  
  def translate( self, x=[0.0,0.0,0.0] ):
    P = np.array( [
      [1,0,0,x[0]],
      [0,1,0,x[1]],
      [0,0,1,x[2]],
      [0,0,0,1] ], "f" )
    return P
  
  def scale( self ):
    a = self.a
    P = np.array( [
      [a,0,0,0],
      [0,a,0,0],
      [0,0,a,0],
      [0,0,0,1] ], "f" )
    return P
  
  def takeSnapshots( self ):
    if self.snaptimes:
      if (self.snaptimes[0]-self.t) <= 0:
        self.snaptimes.pop(0)
        if self.snaptimes:
          self.writePNG()
      
  def update( self ):
    self.told = self.t
    if not self.snaptimes:
      self.t = self.get_time()
    elif len(self.snaptimes) > 1:
      self.t = self.snaptimes[1]  
    elif len(self.snaptimes) == 1:
      #sys.exit(0)
      glutLeaveMainLoop()
    self.dt = (self.t - self.told)/self.tscale
    
    if self.t - self.last_fps > 1.0:
      at = (self.t - self.last_fps)/self.nframes
      self.nframes = 0
      self.last_fps = self.t
      if not self.snaptimes:
        print( self.fstring.format( 1.0/at, 
          display_time(self.t) ) )
      self.fps -= (1.0/at - self.fpsr)/2.0
    
    downed = 1.0
    left = 0 in self.downs and self.downs[0] == 0
    right = 2 in self.downs and self.downs[2] == 0
      
    self.thickness = self.a*self.thickscale
    
    if self.autorotate:
      self.thetax += self.dt*self.dtx*downed
      self.thetay += self.dt*self.dty*downed
      self.thetaz += self.dt*self.dtz*downed
      
      self.thetax = np.mod( self.thetax, 2*np.pi )
      self.thetay = np.mod( self.thetay, 2*np.pi )
      self.thetaz = np.mod( self.thetaz, 2*np.pi )
      
    R = self.rotate(
      self.thetax, 
      self.thetay, 
      self.thetaz )
    Rm = self.rotate( 
      -self.mousethetay,
      self.mousethetax,
      0 )
    T = self.translate()
    S = self.scale()
    self.P = chain( [T, Rm, S, R] )
    self.P = np.array( self.P, 'f' )
  
  def Render( self, *args ):
    
    self.renderend = self.get_time()
    self.renderdelta = self.renderend - self.renderstart
    #if not self.snaptimes:
      #time.sleep( np.abs(1.0/self.fps - self.renderdelta) )
    self.renderstart = self.get_time()
    
    if self.usetexture:
      # Draw everything to the texture first.
      # Set to self.framebuffer for texture draw.
      glBindFramebuffer( GL_FRAMEBUFFER, 
        self.framebuffer )
    else:
      if self.snaptimes:
        glBindFramebuffer(GL_FRAMEBUFFER,
                          self.screenbuffer)
      else:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glViewport(0, 0, self.W, self.H)
    
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear( GL_COLOR_BUFFER_BIT |
             GL_DEPTH_BUFFER_BIT )
    #glClear( GL_DEPTH_BUFFER_BIT )
    
    self.update()
    self.renderCarton()
    # self.renderArrows()
    
    if self.usetexture:
      # Draw the texture to the screen. (0)
      if self.snaptimes:
        glBindFramebuffer(GL_FRAMEBUFFER,
                  self.screenbuffer)
      else:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
      glViewport(0, 0, self.W, self.H)
      glClearColor(0.0, 0.0, 0.0, 1.0)
      glClear( GL_COLOR_BUFFER_BIT |
              GL_DEPTH_BUFFER_BIT )
      self.renderQuad()
    
    glutSwapBuffers()
    # glutPostRedisplay()
    self.takeSnapshots()
    self.nframes += 1
    
  def renderCarton( self ):
    shaders.glUseProgram( self.carton )
    glUniform1f( self.etimeU, 
      self.tscale*np.sin(
        2*np.pi*self.t/self.tloop ) )
    
    #if not self.usetexture:
    self.asp = 1.0*self.W/self.H
    #else:
    #self.asp = 1.0  
    glUniform2f( self.udims, 
      self.asp,          # send the aspect ratio 
      self.points )      # and whether we draw 
                         # points or lines.
                          
    glUniformMatrix4fv( 
      self.PU,   # Uniform location 
      1,         # 1 matrix (not matrix array)
      GL_TRUE,   # Transpose this (for np to gl)
      self.P )   # actual values of the matrix
    glUniform1f( self.ci, self.inverted )
      
    try:
      self.grid.bind()
      try:
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(
          0,         # start
          3,         # number of elements
          GL_FLOAT,  # type for each element
          GL_FALSE,  # ???
          3*4,       # stride
          self.grid )

        glEnable( GL_BLEND )
        glBlendFunc( GL_ONE, GL_ONE )
        glDisable( GL_DEPTH_TEST )
        
        glLineWidth(2.0*self.thickness)
        
        if self.points:
          glUniform2f( self.udims, 
            self.asp,          
            not self.points )                                 
          glUniform1f( self.upower, 0.5 )
          glPointSize(1.0*self.thickness)
          glDrawArrays( GL_TRIANGLES, 0, self.N )
        if self.lines:
          glUniform1f( self.upower, 0.5 )
          glDrawArrays( GL_LINES, 0, self.N )
          
        ## Always add points!  :D
        #glUniform2f( self.udims, 
          #self.asp,          # send the aspect ratio 
          #self.points )      # and whether we draw 
                             ## points or lines.        
        glUniform1f( self.upower, 0.5 )
        glPointSize(2.0*self.thickness)
        glDrawArrays( GL_POINTS, 0, self.N )          
          
        glDisable( GL_BLEND )
        glEnable( GL_DEPTH_TEST )

      finally:
        self.grid.unbind()
        glDisableVertexAttribArray(0)
    finally:
      shaders.glUseProgram( 0 )
  
  def clocktick( self ):
    aflo, aint = np.modf( self.t/8 )
    alpha = (np.mod(aint,8)+
             np.power(aflo,32))*np.pi/4;
    if self.snaptimes:
      alpha = np.pi/4*len(self.snaptimes)
    return self.rotate(0,0,-alpha)[:2,:2]
  
  def boxit( self ):
    bflo, bint = np.modf( self.t )
    return ( (self.WW/20)*(
      -np.cos((bint+np.power(bflo,1))
      *2*np.pi/120) +2) )
  
  def renderArrows( self ):
    shaders.glUseProgram( self.arrow )
    glUniformMatrix4fv( 
      self.PUa,  # Uniform location 
      1,         # 1 matrix (not matrix array)
      GL_TRUE,   # Transpose this (for np to gl)
      self.P )   # actual values of the matrix
      
    try:
      self.arrows.bind()
      try:
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(
          0,         # start
          3,         # number of elements
          GL_FLOAT,  # type for each element
          GL_FALSE,  # ???
          3*4,       # stride
          self.arrows )
        
        glLineWidth(10.0)
        glDrawArrays( GL_LINES, 0, 6 )

      finally:
        self.arrows.unbind()
        glDisableVertexAttribArray(0)
    finally:
      shaders.glUseProgram( 0 )      
      
  def renderQuad( self ):
    shaders.glUseProgram( self.squad )
    glUniformMatrix4fv( 
      self.PUq,  # Uniform location 
      1,         # 1 matrix (not matrix array)
      GL_TRUE,   # Transpose this (for np to gl)
      self.P )   # actual values of the matrix
    glUniform1f( self.zu, self.t )
    glUniform1f( self.sqi, self.inverted )
    glUniform1f( self.vign, self.vignette )
    glUniformMatrix2fv( 
      self.sincos, 
      1,
      GL_TRUE,
      self.clocktick() )
    glUniform1f( self.boxsize, self.boxit() )
    glUniform2f( self.dims, self.W, self.H )
      
    try:
      self.quad.bind()
      try:
        glEnableVertexAttribArray(0) # layout = 0
        glVertexAttribPointer(
          0,         # start
          2,         # number of elements
                     # (per vertex)
          GL_FLOAT,  # type for each element
          GL_FALSE,  # normalized (?)
          2*4,       # stride
          self.quad )
        
        glActiveTexture( GL_TEXTURE0 )
        glBindTexture( GL_TEXTURE_2D, self.tex )
        glUniform1i( glGetUniformLocation(
          self.squad, "tex" ), 
          0 )
        glDrawArrays( GL_TRIANGLE_STRIP, 0, 4 )

      finally:
        self.quad.unbind()
        glDisableVertexAttribArray(0)
    finally:
      shaders.glUseProgram( 0 )   

  def togglefullscreen( self ):
    if self.fullscreen:
      glutReshapeWindow( *self.last_window )
      self.fullscreen = False
    else:
      glutFullScreen()
      self.fullscreen = True
      
  def ResizeGL( self, *args ):
    print( "resize function:", args, self.fullscreen )
    print( "last:", *self.last_window )
    print( "curr:", self.W, self.H )

    self.W, self.H = args
    if self.snaptimes:
      self.W, self.H = self.WW, self.HH
    if not self.fullscreen:
      self.last_window = self.W, self.H
    print( "new :", self.W, self.H )
    self.loadBuffers( self.W, self.H )
    self.thickscale = self.computethick( 
      np.max([self.W,self.H]) )
    print()
    
  def computethick( self, w ):
    # We want the size of a point to be dependent
    # on the resolution.  Assume linear scaling.
    y = 0.75*np.array( [2.0, 1.0] )
    X = np.array( [[3840,1],[1920,1]] )
    B = np.linalg.solve( X, y )
    return np.dot( B, [w,1] )    
    
  # write a png file from GL framebuffer data
  def writePNG(self, name="screenie"):
    if not snaptimes:
      W, H = self.W, self.H
      data = glReadPixels( 0,0, W, H, 
        GL_RGBA, GL_UNSIGNED_BYTE)
      
    else:
      W, H = self.WW, self.HH
      glBindTexture(GL_TEXTURE_2D, self.screentex)
      data = glGetTexImage(
        GL_TEXTURE_2D, 
        0,
        GL_RGBA, 
        GL_UNSIGNED_BYTE)
    im = Image.frombuffer(
      "RGBA", (W,H), data, "raw", "RGBA", 0, 0)
    t = time.strftime( "_%Y_%m_%d_%H%M%S" )
    name = "{}_{:>07.2f}s{}.png".format(
      name, self.t, 
      "" if self.snaptimes else t,
      )
    if self.snaptimes:
      print("{}, {} remain{}".format(
        name, 
        len(self.snaptimes)-1,
        "s" if len(self.snaptimes)==2 else "",
        ))
    else:
      print( "Taking Screenshot " + name )
    outdir = os.path.join(
      os.path.expanduser("~"),
      "img_opengl_jellyfish",
      self.name,
      )
    mkdir(outdir)
    im.save(os.path.join(outdir,name))
    
# borrowed from a stackoverflow post.
# http://stackoverflow.com/questions/4048651/
#   python-function-to-convert-seconds-
#   into-minutes-hours-and-days
def display_time(seconds):
  intervals = (
      ('w', 604800),
      ('d', 86400),
      ('hours', 3600),
      ('mins', 60),
      ('secs', 1),
      )
  result = []

  for name, count in intervals:
    value = seconds // count
    if value:
      seconds -= value * count
      if value == 1:
        name = name.rstrip('s')
      result.append("{} {}".format(value, name))
  return ', '.join(result)

def mkdir(location):
  try:
    os.makedirs(location)
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      raise
  
def template(x, **kwargs):
  y = x.replace("{","{{")
  y = y.replace("}","}}")
  y = y.replace("[=[","{")
  y = y.replace("]=]","}")
  return y.format(**kwargs)

def doit(name, c1, c2, t, v, snaptimes=[]):
  Context(
    #W=750,
    #H=750,
    name=name,
    c1=c1,
    c2=c2,
    usetexture=t,
    vignette=v,
    snaptimes=snaptimes,
    )
  
if __name__ == "__main__":
  
  
  params = [
    [
      "bluepurple_white",
      [0.2375,0.125,0.0125],
      [0.35,0.5,0.35],
      True, # usetex
      0,    # vignette
      ],
    
    #[
      #"graypurple_black",
      #[0.1375,0.0125,0.1375],
      #[0.35,0.5,0.35],
      #False, # usetex
      #0,     # vignette
      #],
      
    #[
      #"seafoamgreen_black",
      #[0.6*0.25, 0.6*0.65, 0.6*0.65],
      #[0.6*0.25, 0.6*0.65, 0.6*0.25],
      #False, # usetex
      #0,     # vignette
      #],
      
    [
      "bloodred_white",
      [0.6*0.25, 0.6*0.65, 0.6*0.65],
      [0.6*0.25, 0.6*0.65, 0.6*0.25],
      True, # usetex
      0,    # vignette
      ],
        
    #[
      #"blueorange_black",
      #[0.85, 0.37, 0.05],
      #[0.01, 0.42, 0.90],
      #False,
      #0,
      #],
    
    #[
      #"grayorangered_black",
      #[0.25*0.95, 0.25*0.5, 0.25*0.05],
      #[0.36, 0.5, 0.35],
      #False,
      #0,
      #],
      
    [
      "sprite_white",
      0.25*np.array([0.45, 0.00, 0.95]),
      0.5*np.array([0.95, 0.25, 0.95]),
      True,
      0,
      ],
    
    [
      "salmon_black",
      7.5*np.array([0.15, 0.0, 0.00]),
      50*np.array([0.06, 0.02, 0.02]),
      False,
      0,
      ],
    
    [
      "greenorange_black",
      [0.85, 0.37, 0.05],
      [0.01, 0.80, 0.30],
      False,
      0,
      ],  
    
    [
      "Random_Color",
      np.random.rand(3),
      np.random.rand(3),
      False,
      0,
      ],  
     
    ]
  
  snaptimes = []
  #snaptimes = np.arange(0.5,600,8.5).tolist()
  #snaptimes = [230.0, 238.5]
  doit(*params[-1],snaptimes=snaptimes)
