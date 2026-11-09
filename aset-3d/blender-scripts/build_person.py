import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *
PI = math.pi

def mat_plaid(name, c1, c2, c3):
    m, nt, out = fa_common._new(name)
    if not nt: return m
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    w1 = nt.nodes.new('ShaderNodeTexWave'); w1.wave_profile = 'SAW'; w1.inputs['Scale'].default_value = 9; w1.bands_direction = 'X'
    w2 = nt.nodes.new('ShaderNodeTexWave'); w2.wave_profile = 'SAW'; w2.inputs['Scale'].default_value = 9; w2.bands_direction = 'Z'
    g1 = nt.nodes.new('ShaderNodeMath'); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = 0.6
    g2 = nt.nodes.new('ShaderNodeMath'); g2.operation = 'GREATER_THAN'; g2.inputs[1].default_value = 0.6
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements; cr.color_ramp.interpolation = 'CONSTANT'
    e[0].color = (*c1, 1); e[1].position = 0.75; e[1].color = (*c3, 1); x = e.new(0.4); x.color = (*c2, 1)
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.5
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 300
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.15
    p = fa_common.principled(nt, None, 0.85)
    L(tc.outputs['Object'], w1.inputs['Vector']); L(tc.outputs['Object'], w2.inputs['Vector']); L(tc.outputs['Object'], nz.inputs['Vector'])
    L(w1.outputs['Fac'], g1.inputs[0]); L(w2.outputs['Fac'], g2.inputs[0]); L(g1.outputs[0], ad.inputs[0]); L(g2.outputs[0], ad.inputs[1])
    L(ad.outputs[0], mul.inputs[0]); L(mul.outputs[0], cr.inputs[0]); L(cr.outputs[0], p.inputs['Base Color'])
    L(nz.outputs['Fac'], bp.inputs['Height']); L(bp.outputs[0], p.inputs['Normal']); L(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*c1, 1)
    return m

def vloft(b, mat, sections, seg=24, e=2.2):
    """vertical loft: sections (z, half_y, half_x, xc, yc)"""
    rings = []
    for (z, hy, hx, xc, yc) in sections:
        ring = []
        for j in range(seg):
            a = math.tau * j / seg; c, s = math.cos(a), math.sin(a)
            cx = math.copysign(abs(c) ** (2 / e), c); sy = math.copysign(abs(s) ** (2 / e), s)
            ring.append(b.bm.verts.new((xc + cx * hx, yc + sy * hy, z)))
        rings.append(ring)
    vs = []
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for j in range(seg): b.bm.faces.new((A[j], A[(j + 1) % seg], B[(j + 1) % seg], B[j]))
    b.bm.faces.new(rings[0][::-1]); b.bm.faces.new(rings[-1])
    for r in rings: vs += r
    b._finish(vs, mat, Matrix.Identity(4))

def build(origin=(8, -40, 0)):
    purge(["M_Pers"])
    C = collection("A06_FlamethrowerMan")
    root = empty("FlamethrowerMan", C, (0, 0, 0), 1)
    skin = mat_noise("M_Pers_Skin", (0.42, 0.25, 0.16), (0.5, 0.31, 0.2), 40, (0.45, 0.6), 0, 0.05)
    shirt = mat_plaid("M_Pers_Flannel", (0.35, 0.03, 0.02), (0.12, 0.02, 0.02), (0.02, 0.02, 0.02))
    pants = mat_noise("M_Pers_Cargo", (0.12, 0.12, 0.07), (0.18, 0.17, 0.1), 60, (0.8, 0.95), 0, 0.25)
    boots = mat_noise("M_Pers_Boot", (0.06, 0.035, 0.02), (0.12, 0.07, 0.035), 30, (0.5, 0.7), 0, 0.2)
    sole = mat_basic("M_Pers_Sole", (0.02, 0.02, 0.02), 0.8)
    glove = mat_noise("M_Pers_Glove", (0.25, 0.18, 0.08), (0.35, 0.25, 0.12), 50, (0.7, 0.9), 0, 0.3)
    cap = mat_noise("M_Pers_Cap", (0.6, 0.45, 0.05), (0.7, 0.55, 0.1), 50, (0.7, 0.9), 0, 0.1)
    band = mat_noise("M_Pers_Bandana", (0.05, 0.05, 0.06), (0.1, 0.1, 0.12), 80, (0.8, 0.95), 0, 0.2)
    gogg = mat_glass("M_Pers_Goggle", (0.4, 0.25, 0.05), 0.05)
    strap = mat_basic("M_Pers_Strap", (0.03, 0.03, 0.03), 0.6)
    tank = mat_paint("M_Pers_Tank", (0.65, 0.42, 0.02), 0.3, 0.3)
    metal = mat_noise("M_Pers_Steel", (0.3, 0.3, 0.32), (0.45, 0.45, 0.47), 20, (0.3, 0.5), 1.0, 0.1)
    chrome = mat_basic("M_Chrome", (0.92, 0.92, 0.94), 0.06, 1.0)
    hosem = mat_noise("M_Pers_Hose", (0.04, 0.04, 0.04), (0.08, 0.08, 0.08), 90, (0.6, 0.8), 0, 0.3, stretch=(1, 1, 20))
    soot = mat_noise("M_Pers_Soot", (0.03, 0.025, 0.02), (0.1, 0.08, 0.06), 20, (0.5, 0.8), 0.6, 0.2)
    b = Builder("Person")
    # legs (stance: left foot forward)
    for s, fx in ((1, 0.18), (-1, -0.18)):
        hip = Vector((0.0, s * 0.1, 0.95)); knee = Vector((fx * 0.6 + 0.04, s * 0.13, 0.52)); ank = Vector((fx, s * 0.15, 0.1))
        b.tube(pants, [hip, (hip + knee) / 2, knee, (knee + ank) / 2, ank + Vector((0, 0, 0.06))], 0.1, 16, radii=[0.1, 0.085, 0.075, 0.068, 0.072])
        b.sphere(pants, 0.07, tuple(knee + Vector((0.01, 0, 0))), scale=(1, 1, 1.1))
        for zz in (0.62, 0.66):  # cargo pocket
            b.box(pants, (0.03, 0.12, 0.16), (hip.x * 0.5 + knee.x * 0.5 + 0.0, s * 0.215, 0.72), (0, 0, 0))
        # boot
        b.box(boots, (0.27, 0.11, 0.12), (fx + 0.06, s * 0.15, 0.075))
        b.cyl(boots, 0.065, 0.16, (fx, s * 0.15, 0.17), seg=16)
        b.box(sole, (0.29, 0.12, 0.025), (fx + 0.06, s * 0.15, 0.012))
        b.sphere(boots, 0.06, (fx + 0.17, s * 0.15, 0.07), scale=(1.1, 0.95, 0.8))
    # pelvis + belt
    vloft(b, pants, [(0.86, 0.17, 0.12, 0.0, 0), (0.95, 0.19, 0.13, 0.0, 0), (1.02, 0.18, 0.12, 0.0, 0)], 24)
    vloft(b, strap, [(1.0, 0.185, 0.125, 0.0, 0), (1.05, 0.185, 0.125, 0.0, 0)], 24)
    b.box(chrome, (0.02, 0.06, 0.045), (0.125, 0, 1.025))
    # torso (flannel shirt), slightly leaning forward
    vloft(b, shirt, [(1.02, 0.18, 0.12, 0.0, 0), (1.15, 0.19, 0.12, 0.01, 0), (1.3, 0.21, 0.13, 0.02, 0), (1.42, 0.23, 0.12, 0.02, 0),
                     (1.48, 0.21, 0.1, 0.015, 0), (1.52, 0.12, 0.07, 0.01, 0)], 28)
    for z in (1.1, 1.2, 1.3, 1.4): b.sphere(chrome, 0.008, (0.135, 0, z))
    b.box(shirt, (0.12, 0.08, 0.1), (0.1, 0.11, 1.33))                                   # chest pocket
    # neck + head
    b.cyl(skin, 0.05, 0.12, (0.02, 0, 1.56), seg=16)
    b.sphere(skin, 0.105, (0.035, 0, 1.68), scale=(1.0, 0.88, 1.12), sub=3)
    for s in (-1, 1): b.sphere(skin, 0.025, (0.02, s * 0.093, 1.68), scale=(0.6, 0.4, 1))
    b.sphere(skin, 0.025, (0.135, 0, 1.68), scale=(0.8, 0.6, 1.0))                      # nose
    # bandana mask over lower face
    vloft(b, band, [(1.58, 0.095, 0.1, 0.045, 0), (1.62, 0.1, 0.11, 0.05, 0), (1.67, 0.095, 0.108, 0.05, 0)], 24)
    # goggles + strap
    b.box(strap, (0.03, 0.2, 0.02), (0.06, 0, 1.73))
    for s in (-1, 1):
        b.cyl(strap, 0.032, 0.03, (0.13, s * 0.04, 1.72), rot=(0, PI / 2, 0), seg=16)
        b.cyl(gogg, 0.026, 0.035, (0.135, s * 0.04, 1.72), rot=(0, PI / 2, 0), seg=16)
    # cap with brim
    b.sphere(cap, 0.112, (0.03, 0, 1.75), scale=(1.02, 0.92, 0.65), sub=3)
    b.cyl(cap, 0.095, 0.012, (0.14, 0, 1.755), rot=(0, 0.08, 0), seg=24)
    b.box(cap, (0.02, 0.16, 0.035), (-0.075, 0, 1.73))
    # arms: right hand on rear grip, left on front grip of the flamethrower
    sh_r = Vector((0.0, -0.24, 1.43)); el_r = Vector((0.08, -0.3, 1.18)); wr_r = Vector((0.27, -0.13, 0.99))
    sh_l = Vector((0.0, 0.24, 1.43)); el_l = Vector((0.3, 0.2, 1.13)); wr_l = Vector((0.6, -0.03, 0.97))
    for sh, el, wr in ((sh_r, el_r, wr_r), (sh_l, el_l, wr_l)):
        b.sphere(shirt, 0.075, tuple(sh), sub=2)
        b.tube(shirt, [sh, (sh + el) / 2, el, (el + wr) / 2, wr], 0.07, 14, radii=[0.07, 0.062, 0.055, 0.05, 0.045])
        b.sphere(glove, 0.05, tuple(wr + (wr - el).normalized() * 0.05), scale=(1.2, 0.8, 0.95))
        b.tube(shirt, [wr - (wr - el).normalized() * 0.04, wr + (wr - el).normalized() * 0.005], 0.052, 14)
    # backpack: frame + 2 fuel tanks + small pressure bottle
    b.box(strap, (0.04, 0.34, 0.5), (-0.14, 0, 1.25))
    for s in (-1, 1):
        b.tube(strap, [(-0.12, s * 0.15, 1.5), (0.0, s * 0.15, 1.52), (0.12, s * 0.13, 1.38), (0.12, s * 0.13, 1.1), (-0.1, s * 0.15, 1.05)], 0.018, 8)
        b.cyl(tank, 0.095, 0.48, (-0.27, s * 0.1, 1.28), seg=28)
        b.sphere(tank, 0.095, (-0.27, s * 0.1, 1.52), scale=(1, 1, 0.5)); b.sphere(tank, 0.095, (-0.27, s * 0.1, 1.04), scale=(1, 1, 0.5))
        b.cyl(chrome, 0.025, 0.06, (-0.27, s * 0.1, 1.58), seg=12)
        for z in (1.12, 1.44): b.torus(strap, 0.097, 0.008, (-0.27, s * 0.1, z), maj=24, mnr=6)
    b.cyl(metal, 0.055, 0.36, (-0.37, 0, 1.3), seg=20)
    b.cyl(chrome, 0.03, 0.05, (-0.37, 0, 1.5), seg=12)
    b.box(soot, (0.08, 0.2, 0.05), (-0.27, 0, 1.0))
    # hose from tanks to the gun
    b.tube(hosem, [(-0.27, 0.0, 0.98), (-0.2, -0.15, 0.85), (0.05, -0.28, 0.82), (0.25, -0.24, 0.9), (0.33, -0.15, 0.98)], 0.022, 10)
    # flamethrower wand: body, grips, barrel with heat shroud, nozzle, igniter
    d = Vector((1, 0, -0.08)).normalized()
    base = Vector((0.26, -0.12, 1.02))
    pt = lambda t: base + d * t
    b.tube(metal, [pt(0.0), pt(0.18)], 0.035, 16)                                       # body
    b.box(strap, (0.05, 0.04, 0.12), tuple(pt(0.06) + Vector((0, 0, -0.07))), (0, 0.3, 0))  # rear grip
    b.tube(metal, [pt(0.18), pt(0.95)], 0.016, 12)                                     # fuel line
    for k in range(12):
        b.cyl(soot, 0.03, 0.03, tuple(pt(0.3 + k * 0.05)), rot=(0, PI / 2 - 0.08, 0), seg=14)   # shroud rings
    b.tube(soot, [pt(0.28), pt(0.9)], 0.028, 14)
    b.box(strap, (0.04, 0.04, 0.11), tuple(pt(0.42) + Vector((0, 0.08, -0.06))), (0, 0.2, 0))   # front grip (offset to left hand)
    b.tube(metal, [pt(0.42) + Vector((0, 0.0, -0.01)), pt(0.42) + Vector((0, 0.08, -0.02))], 0.012, 8)
    b.cyl(chrome, 0.026, 0.08, tuple(pt(0.97)), rot=(0, PI / 2 - 0.08, 0), seg=16, r2=0.018)   # nozzle
    b.tube(metal, [pt(0.75) + Vector((0, 0, -0.04)), pt(0.95) + Vector((0, 0, -0.04))], 0.008, 8)  # igniter
    b.box(metal, (0.03, 0.01, 0.025), tuple(pt(0.08) + Vector((0.02, 0, -0.04))))        # trigger
    person = b.build(C, bevel=0.0, parent=root, smooth_angle=50)
    e = empty("NODE_jet", C, tuple(pt(1.02)), 0.1); e.parent = root
    e2 = empty("NODE_jetdir", C, tuple(pt(1.6)), 0.1); e2.parent = root
    root.location = origin
    mark_asset(root, "Original character: land-clearer with backpack flamethrower (fire jet node).", ["character", "flamethrower", "arson"])
    return root, C

root, C = build()
result = {"faces": sum(len(o.data.polygons) for o in C.objects if o.type == 'MESH')}
