from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# ─────────────────────────────────────────────
#  Global State
# ─────────────────────────────────────────────
angle        = 0.0        # planet orbit angle
zoom         = 1.0        # zoom level (scroll wheel)
fog_on       = False      # toggle fog with 'f'
blend_on     = True       # toggle blending with 'b'
show_help    = True       # toggle help text with 'h'
paused       = False      # pause animation with SPACE
sun_x        = 0.0        # sun X position (drag with mouse)
sun_y        = 0.0        # sun Y position
dragging     = False      # mouse drag state
bg_color     = 0          # cycle background with 'c'

BG_COLORS = [
    (0.0,  0.0,  0.05),   # deep space black
    (0.05, 0.0,  0.1 ),   # dark purple nebula
    (0.0,  0.05, 0.1 ),   # midnight blue
]

# ─────────────────────────────────────────────
#  Drawing Helpers
# ─────────────────────────────────────────────

def draw_circle(cx, cy, r, slices=60):
    """Filled circle using GL_TRIANGLE_FAN."""
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(slices + 1):
        theta = 2.0 * math.pi * i / slices
        glVertex2f(cx + r * math.cos(theta),
                   cy + r * math.sin(theta))
    glEnd()


def draw_circle_outline(cx, cy, r, slices=60):
    """Circle outline (orbit ring)."""
    glBegin(GL_LINE_LOOP)
    for i in range(slices):
        theta = 2.0 * math.pi * i / slices
        glVertex2f(cx + r * math.cos(theta),
                   cy + r * math.sin(theta))
    glEnd()


def draw_glow(cx, cy, r, color, layers=6):
    """Soft glow via multiple translucent rings (needs blending ON)."""
    for i in range(layers, 0, -1):
        alpha  = 0.06 * i / layers
        radius = r + (layers - i + 1) * 0.018
        glColor4f(color[0], color[1], color[2], alpha)
        draw_circle(cx, cy, radius)


def draw_stars():
    """Static star field."""
    import random
    random.seed(42)
    glPointSize(1.5)
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_POINTS)
    for _ in range(200):
        x = random.uniform(-1.0, 1.0)
        y = random.uniform(-1.0, 1.0)
        glVertex2f(x, y)
    glEnd()


# ─────────────────────────────────────────────
#  Planet Data:  (orbit_radius, size, R, G, B, speed_mult, name)
# ─────────────────────────────────────────────
PLANETS = [
    (0.18, 0.025, 0.7,  0.7,  0.7,  4.7,  "Mercury"),
    (0.30, 0.040, 0.9,  0.7,  0.3,  1.8,  "Venus"),
    (0.42, 0.045, 0.2,  0.5,  1.0,  1.0,  "Earth"),
    (0.54, 0.035, 0.8,  0.3,  0.1,  0.5,  "Mars"),
    (0.70, 0.080, 0.8,  0.6,  0.4,  0.08, "Jupiter"),
    (0.85, 0.065, 0.9,  0.85, 0.5,  0.03, "Saturn"),
]


# ─────────────────────────────────────────────
#  Scene Drawing
# ─────────────────────────────────────────────

def draw_scene():
    glPushMatrix()
    glScalef(zoom, zoom, 1.0)

    # Stars
    draw_stars()

    # Orbit rings
    glLineWidth(0.5)
    for (orb, *_) in PLANETS:
        glColor4f(0.4, 0.4, 0.6, 0.3)
        draw_circle_outline(sun_x, sun_y, orb)

    # Sun  ── shading via colour gradient layers
    if blend_on:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        draw_glow(sun_x, sun_y, 0.10, (1.0, 0.9, 0.2))

    # Sun core – simple Gouraud-style shading with vertex colours
    glBegin(GL_TRIANGLE_FAN)
    glColor3f(1.0, 1.0, 0.6)          # bright centre
    glVertex2f(sun_x, sun_y)
    slices = 60
    for i in range(slices + 1):
        theta = 2.0 * math.pi * i / slices
        glColor3f(1.0, 0.55, 0.0)     # orange rim  ← shading effect
        glVertex2f(sun_x + 0.10 * math.cos(theta),
                   sun_y + 0.10 * math.sin(theta))
    glEnd()

    # Planets
    for idx, (orb, size, r, g, b, spd, name) in enumerate(PLANETS):
        planet_angle = math.radians(angle * spd)
        px = sun_x + orb * math.cos(planet_angle)
        py = sun_y + orb * math.sin(planet_angle)

        # Glow
        if blend_on:
            draw_glow(px, py, size, (r, g, b))

        # Planet body with simple shading (bright centre → dark edge)
        glBegin(GL_TRIANGLE_FAN)
        glColor3f(min(r + 0.3, 1.0), min(g + 0.3, 1.0), min(b + 0.3, 1.0))
        glVertex2f(px, py)
        for i in range(61):
            theta = 2.0 * math.pi * i / 60
            glColor3f(r * 0.6, g * 0.6, b * 0.6)
            glVertex2f(px + size * math.cos(theta),
                       py + size * math.sin(theta))
        glEnd()

        # Saturn's ring
        if name == "Saturn":
            glLineWidth(2.0)
            glColor4f(0.85, 0.75, 0.5, 0.6)
            draw_circle_outline(px, py, size * 1.7)
            glLineWidth(1.0)

    if blend_on:
        glDisable(GL_BLEND)

    glPopMatrix()


def draw_hud():
    """On-screen key hints."""
    if not show_help:
        return
    hints = [
        "SPACE : pause/resume",
        "F     : toggle fog",
        "B     : toggle blend/glow",
        "C     : change background",
        "H     : hide/show help",
        "Scroll: zoom in/out",
        "Drag  : move sun",
    ]
    # Draw a semi-transparent panel
    if blend_on:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(-1.0,  1.0)
    glVertex2f(-0.55, 1.0)
    glVertex2f(-0.55, 0.56)
    glVertex2f(-1.0,  0.56)
    glEnd()
    if blend_on:
        glDisable(GL_BLEND)

    glColor3f(0.8, 0.8, 0.8)
    for i, line in enumerate(hints):
        glRasterPos2f(-0.98, 0.95 - i * 0.057)
        for ch in line:
            glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(ch))


# ─────────────────────────────────────────────
#  OpenGL Fog Setup
# ─────────────────────────────────────────────

def apply_fog():
    if fog_on:
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE,    GL_LINEAR)
        glFogf(GL_FOG_START,   0.3)
        glFogf(GL_FOG_END,     1.5)
        fog_col = list(BG_COLORS[bg_color]) + [1.0]
        glFogfv(GL_FOG_COLOR,  fog_col)
        glHint(GL_FOG_HINT,    GL_NICEST)
    else:
        glDisable(GL_FOG)


# ─────────────────────────────────────────────
#  GLUT Callbacks
# ─────────────────────────────────────────────

def show_screen():
    bc = BG_COLORS[bg_color]
    glClearColor(bc[0], bc[1], bc[2], 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    apply_fog()
    draw_scene()
    draw_hud()

    glFlush()


def update(value):
    """Timer callback – advances animation."""
    global angle
    if not paused:
        angle = (angle + 0.5) % 360
    glutPostRedisplay()
    glutTimerFunc(16, update, 0)   # ~60 fps


def keyboard(key, x, y):
    """Normal key handler."""
    global fog_on, blend_on, show_help, paused, bg_color
    if key == b' ':
        paused = not paused
    elif key == b'f':
        fog_on = not fog_on
    elif key == b'b':
        blend_on = not blend_on
    elif key == b'h':
        show_help = not show_help
    elif key == b'c':
        bg_color = (bg_color + 1) % len(BG_COLORS)
    elif key == b'q' or key == b'\x1b':   # q or ESC
        import sys; sys.exit(0)
    glutPostRedisplay()


def special_key(key, x, y):
    """Arrow-key handler – manually orbit planets."""
    global angle
    if key == GLUT_KEY_RIGHT:
        angle = (angle + 5) % 360
    elif key == GLUT_KEY_LEFT:
        angle = (angle - 5) % 360
    glutPostRedisplay()


def screen_to_world(sx, sy):
    """Convert GLUT pixel coords → OpenGL world coords."""
    w = glutGet(GLUT_WINDOW_WIDTH)
    h = glutGet(GLUT_WINDOW_HEIGHT)
    wx = (sx / (w / 2.0)) - 1.0
    wy = -((sy / (h / 2.0)) - 1.0)
    return wx / zoom, wy / zoom


def mouse_click(button, state, x, y):
    """Mouse button handler – start/stop drag; scroll zoom."""
    global dragging, zoom
    if button == GLUT_LEFT_BUTTON:
        dragging = (state == GLUT_DOWN)
        if dragging:
            # Move sun to click position
            global sun_x, sun_y
            sun_x, sun_y = screen_to_world(x, y)
    # Scroll wheel zoom (button 3 = up, 4 = down)
    elif button == 3 and state == GLUT_DOWN:
        zoom = min(zoom + 0.1, 3.0)
    elif button == 4 and state == GLUT_DOWN:
        zoom = max(zoom - 0.1, 0.3)
    glutPostRedisplay()


def mouse_drag(x, y):
    """Passive/active mouse motion – drag sun."""
    global sun_x, sun_y
    if dragging:
        sun_x, sun_y = screen_to_world(x, y)
    glutPostRedisplay()


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_SINGLE)
glutInitWindowSize(700, 700)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"2D Solar System  |  OpenGL Beginner Project")

glEnable(GL_LINE_SMOOTH)
glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

glutDisplayFunc(show_screen)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_key)
glutMouseFunc(mouse_click)
glutMotionFunc(mouse_drag)
glutTimerFunc(16, update, 0)

glutMainLoop()