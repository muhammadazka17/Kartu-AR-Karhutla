import bpy, math, random
from mathutils import Vector
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *

PI = math.pi
def R(b, mat, x0, x1, y0, y1, z0, z1, rot=(0, 0, 0)):
    return b.box(mat, (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), rot)

def apply_all(o):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    old = o.data; o.modifiers.clear(); o.data = me
    if old.users == 0: bpy.data.meshes.remove(old)
    try: me.set_sharp_from_angle(angle=math.radians(32))
    except Exception: pass
    return o

def build():
    C = collection("A01_FireTruck")
    root = empty("FireTruck", C, (0, 0, 0), 2.0)
    # ---------------- materials
    red = mat_paint("M_Truck_RedPaint", (0.55, 0.012, 0.01), 0.22, 0.18)
    red_dark = mat_paint("M_Truck_RedDark", (0.3, 0.01, 0.008), 0.3, 0.2)
    chrome = mat_basic("M_Chrome", (0.92, 0.92, 0.94), 0.06, 1.0)
    alu = mat_noise("M_BrushedAlu", (0.62, 0.63, 0.65), (0.78, 0.79, 0.8), 3, (0.22, 0.35), 1.0, 0.05, stretch=(60, 1, 1))
    plate = mat_diamond_plate()
    black = mat_basic("M_BlackPlastic", (0.018, 0.018, 0.02), 0.55)
    rubber = mat_noise("M_TireRubber", (0.02, 0.02, 0.022), (0.05, 0.05, 0.05), 40, (0.75, 0.95), 0, 0.15)
    under = mat_noise("M_UnderGrime", (0.02, 0.018, 0.016), (0.06, 0.055, 0.05), 12, (0.7, 0.9), 0.3, 0.2)
    interior = mat_basic("M_CabInterior", (0.03, 0.032, 0.035), 0.8)
    seat = mat_noise("M_SeatFabric", (0.04, 0.04, 0.045), (0.08, 0.08, 0.09), 120, (0.85, 1.0), 0, 0.3)
    glass = mat_glass("M_Glass_Tinted", (0.55, 0.62, 0.65), 0.02)
    white_ref = mat_basic("M_Stripe_White", (0.85, 0.85, 0.82), 0.3, 0.0, 0.5)
    lime = mat_basic("M_Stripe_Lime", (0.55, 0.75, 0.02), 0.35, 0.0, 0.5)
    yellow = mat_basic("M_Stripe_Yellow", (0.85, 0.62, 0.02), 0.35)
    head = mat_emit("M_Headlight", (1.0, 0.95, 0.85), 18)
    amber = mat_lens("M_Lens_Amber", (1.0, 0.38, 0.0), 5)
    tail = mat_lens("M_Lens_Red", (0.9, 0.0, 0.0), 6)
    rev = mat_lens("M_Lens_White", (0.9, 0.9, 0.9), 2)
    beacon_r = mat_lens("M_Beacon_Red", (1.0, 0.02, 0.01), 22)
    beacon_b = mat_lens("M_Beacon_Blue", (0.02, 0.12, 1.0), 26)
    gauge = mat_basic("M_GaugeFace", (0.92, 0.92, 0.88), 0.4, 0, 0, (1, 1, 0.9), 0.4)
    needle = mat_basic("M_GaugeNeedle", (0.8, 0.02, 0.02), 0.4)
    blue_p = mat_basic("M_ValveBlue", (0.02, 0.12, 0.55), 0.35)
    yel_p = mat_basic("M_ValveYellow", (0.9, 0.6, 0.02), 0.35)
    hose = mat_noise("M_HoseRed", (0.45, 0.03, 0.02), (0.6, 0.06, 0.04), 80, (0.6, 0.8), 0, 0.25, stretch=(1, 1, 20))
    hose_cream = mat_noise("M_HoseCanvas", (0.75, 0.68, 0.52), (0.9, 0.84, 0.7), 90, (0.7, 0.9), 0, 0.3)
    mirror = mat_basic("M_Mirror", (0.95, 0.95, 0.95), 0.0, 1.0)
    lettering = mat_basic("M_Lettering", (0.95, 0.95, 0.93), 0.3, 0, 0.4)
    gold = mat_basic("M_LetteringGold", (0.9, 0.62, 0.15), 0.25, 1.0)

    W = 1.25
    FRONT_AXLE, REAR_AXLES = 3.5, (-1.35, -2.55)
    WR, WZ = 0.52, 0.52

    # ---------------- cutters (wheel arches + cab cavity/windows)
    CC = collection("A01_cutters", C)
    cut_dark = Builder("cut_arches")
    for x in (FRONT_AXLE,) + REAR_AXLES:
        cut_dark.cyl(under, 0.66, 3.2, (x, 0, WZ), rot=(PI / 2, 0, 0), seg=48)
    cut_dark.build(CC, wn=False)
    cut_cab = Builder("cut_cab")
    R(cut_cab, interior, 1.62, 4.05, -1.12, 1.12, 1.98, 2.84)       # cabin cavity
    R(cut_cab, interior, 3.95, 4.5, -1.06, 1.06, 2.02, 2.8)         # windshield opening
    R(cut_cab, interior, 2.45, 3.25, -1.5, 1.5, 2.02, 2.78)         # driver door windows
    R(cut_cab, interior, 1.68, 2.22, -1.5, 1.5, 2.02, 2.78)         # crew door windows
    cut_cab.build(CC, wn=False)
    CC.hide_render = True
    for o in CC.objects: o.display_type = 'WIRE'; o.hide_render = True

    # ---------------- cab shell
    b = Builder("Cab_Shell")
    R(b, red, 1.45, 4.2, -W, W, 0.88, 2.98)
    R(b, red, 1.45, 2.4, -W, W, 2.9, 3.12)                          # raised crew roof
    shell = b.build(C, parent=root)
    m = shell.modifiers.new("Arches", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.operand_type = 'COLLECTION'
    m.collection = CC; m.solver = 'EXACT'; m.material_mode = 'TRANSFER'
    bv = shell.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.07; bv.segments = 4; bv.limit_method = 'ANGLE'
    bv.angle_limit = math.radians(40); bv.use_clamp_overlap = True
    apply_all(shell)

    # ---------------- body shell
    b = Builder("Body_Shell")
    R(b, red, -3.95, 1.35, -W, W, 0.88, 2.78)
    body = b.build(C, parent=root)
    m = body.modifiers.new("Arches", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.operand_type = 'OBJECT'
    m.object = bpy.data.objects["cut_arches"]; m.solver = 'EXACT'; m.material_mode = 'TRANSFER'
    bv = body.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.03; bv.segments = 3; bv.limit_method = 'ANGLE'
    bv.angle_limit = math.radians(40); bv.use_clamp_overlap = True
    apply_all(body)
    for o in list(CC.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(CC)

    # ---------------- cab details
    d = Builder("Cab_Details")
    # windshield + seals, side glass
    R(d, glass, 4.13, 4.145, -1.04, 1.04, 2.03, 2.79)
    for z in (2.02, 2.8):
        R(d, black, 4.12, 4.2, -1.07, 1.07, z - 0.012, z + 0.012)
    for y in (-1.06, 1.06):
        R(d, black, 4.12, 4.2, y - 0.012, y + 0.012, 2.02, 2.8)
    for s in (-1, 1):
        for x0, x1 in ((2.45, 3.25), (1.68, 2.22)):
            R(d, glass, x0, x1, s * 1.205, s * 1.215, 2.02, 2.78)
            R(d, black, x0 - 0.02, x1 + 0.02, s * 1.2, s * 1.26, 2.0, 2.02)
            R(d, black, x0 - 0.02, x1 + 0.02, s * 1.2, s * 1.26, 2.78, 2.8)
        # door seams
        for (x0, x1, zb) in ((2.35, 3.32, 1.22), (1.55, 2.3, 0.92)):
            R(d, black, x0, x0 + 0.012, s * 1.248, s * 1.256, zb, 2.9)
            R(d, black, x1 - 0.012, x1, s * 1.248, s * 1.256, zb, 2.9)
            R(d, black, x0, x1, s * 1.248, s * 1.256, 2.888, 2.9)
            R(d, black, x0, x1, s * 1.248, s * 1.256, zb, zb + 0.012)
            # handles
            R(d, chrome, x0 + 0.08, x0 + 0.26, s * 1.25, s * 1.29, 1.82, 1.86)
            R(d, black, x0 + 0.1, x0 + 0.24, s * 1.252, s * 1.262, 1.79, 1.82)
        # grab rails beside doors
        d.cyl(chrome, 0.018, 1.0, (2.36, s * 1.3, 1.95), seg=12)
        d.cyl(chrome, 0.018, 1.0, (1.54, s * 1.3, 1.75), seg=12)
        for z in (1.45, 2.45):
            d.cyl(chrome, 0.012, 0.06, (2.36, s * 1.275, z), rot=(PI / 2, 0, 0), seg=8)
        # steps (diamond plate) behind front wheel
        for z, dep in ((0.48, 0.22), (0.78, 0.12)):
            R(d, plate, 1.6, 2.75, s * (W - 0.02), s * (W + dep), z - 0.025, z + 0.025)
        R(d, black, 1.6, 2.75, s * (W - 0.01), s * (W + 0.005), 0.45, 0.88)
        # stripes
        for x0, x1 in ((1.45, 2.78), (4.07, 4.2)):
            R(d, white_ref, x0, x1, s * 1.251, s * 1.258, 1.25, 1.4)
            R(d, lime, x0, x1, s * 1.251, s * 1.258, 1.42, 1.5)
        R(d, white_ref, 2.78, 4.07, s * 1.251, s * 1.258, 1.25, 1.4)
        R(d, lime, 2.78, 4.07, s * 1.251, s * 1.258, 1.42, 1.5)
        # mirrors
        d.tube(chrome, [(4.0, s * 1.22, 2.3), (4.08, s * 1.45, 2.32), (4.06, s * 1.55, 2.5)], 0.016, 10)
        d.tube(chrome, [(4.0, s * 1.22, 2.75), (4.06, s * 1.5, 2.85), (4.06, s * 1.55, 2.78)], 0.016, 10)
        R(d, black, 4.0, 4.1, s * 1.47, s * 1.65, 2.42, 2.82)
        R(d, mirror, 3.995, 4.0, s * 1.49, s * 1.63, 2.44, 2.8)
        R(d, black, 4.0, 4.09, s * 1.49, s * 1.63, 2.3, 2.4)
        R(d, mirror, 3.995, 4.0, s * 1.5, s * 1.62, 2.31, 2.39)
        # headlights (dual round) + bezel + indicators
        yc = s * 0.86
        R(d, chrome, 4.19, 4.24, yc - 0.27, yc + 0.27, 1.22, 1.5)
        R(d, black, 4.22, 4.245, yc - 0.25, yc + 0.25, 1.24, 1.48)
        for dy in (-0.12, 0.12):
            d.cyl(chrome, 0.1, 0.03, (4.245, yc + dy, 1.36), rot=(0, PI / 2, 0), seg=32)
            d.cyl(head, 0.085, 0.03, (4.255, yc + dy, 1.36), rot=(0, PI / 2, 0), seg=32)
        R(d, amber, 4.19, 4.235, yc - 0.2, yc + 0.2, 1.53, 1.6)
        R(d, amber, 4.0, 4.2, s * 1.25, s * 1.262, 1.55, 1.62)      # side repeater
        # front wheel fender arch
        d.arch(black, 0.69, 0.655, 0.42, (FRONT_AXLE, s * 1.12, WZ), seg=32, a0=0.0, a1=PI)
        d.arch(chrome, 0.705, 0.69, 0.43, (FRONT_AXLE, s * 1.12, WZ), seg=32, a0=0.05, a1=PI - 0.05)
    # sun visor above windshield + roof marker lights
    R(d, black, 4.12, 4.32, -1.12, 1.12, 2.86, 2.9, rot=(0, -0.12, 0))
    for y in (-0.9, -0.3, 0.3, 0.9):
        R(d, amber, 4.19, 4.22, y - 0.05, y + 0.05, 2.92, 2.95)
    # cab side body-line moulding
    for s2 in (-1, 1):
        R(d, chrome, 1.45, 4.15, s2 * 1.252, s2 * 1.262, 1.86, 1.875)
    # grille
    R(d, black, 4.19, 4.22, -0.58, 0.58, 1.02, 1.8)
    for i in range(11):
        z = 1.06 + i * 0.068
        R(d, chrome, 4.21, 4.245, -0.56, 0.56, z, z + 0.028)
    R(d, chrome, 4.2, 4.25, -0.6, 0.6, 1.8, 1.84); R(d, chrome, 4.2, 4.25, -0.6, 0.6, 0.99, 1.03)
    for y in (-0.6, 0.6):
        R(d, chrome, 4.2, 4.25, y - 0.02, y + 0.02, 0.99, 1.84)
    # bumper with siren speaker + tow hooks
    R(d, chrome, 4.2, 4.5, -1.28, 1.28, 0.58, 0.92)
    R(d, black, 4.49, 4.505, -0.3, 0.3, 0.64, 0.86)
    for i in range(7):
        R(d, chrome, 4.5, 4.51, -0.28, 0.28, 0.66 + i * 0.03, 0.672 + i * 0.03)
    for y in (-0.85, 0.85):
        d.torus(red_dark, 0.07, 0.02, (4.55, y, 0.6), rot=(0, 0, 0), maj=20, mnr=8)
        R(d, black, 4.48, 4.52, y - 0.05, y + 0.05, 0.56, 0.62)
    R(d, black, 4.2, 4.45, -1.2, 1.2, 0.5, 0.58)                     # lower valance
    # front number / emblem
    # wipers
    for y in (-0.55, 0.35):
        d.tube(black, [(4.17, y, 2.04), (4.17, y + 0.12, 2.45), (4.17, y + 0.2, 2.62)], 0.01, 6)
    # roof: lightbar + air horns + handrail
    R(d, black, 3.55, 3.9, -1.05, 1.05, 2.98, 3.05)
    for i in range(8):
        y = -0.92 + i * (1.84 / 7)
        mt = beacon_r if (i // 2) % 2 == 0 else beacon_b
        d.uvsphere(mt, 0.12, (3.72, y, 3.08), scale=(1.25, 0.95, 0.65), seg=24, rings=12)
    for y in (-1.06, 1.06):
        d.cyl(chrome, 0.04, 0.36, (3.72, y, 3.03), rot=(0, 0, 0), seg=16)
        d.sphere(chrome, 0.045, (3.72, y, 3.21), sub=2)
    for y in (-0.4, 0.4):
        d.cyl(chrome, 0.05, 0.38, (3.2, y, 3.06), rot=(0, PI / 2, 0), seg=20, r2=0.075)
    d.tube(chrome, [(1.6, 1.15, 3.12), (1.6, 1.15, 3.18), (2.3, 1.15, 3.18), (2.3, 1.15, 3.12)], 0.016, 10)
    d.tube(chrome, [(1.6, -1.15, 3.12), (1.6, -1.15, 3.18), (2.3, -1.15, 3.18), (2.3, -1.15, 3.12)], 0.016, 10)
    # cab interior
    R(d, interior, 3.85, 4.05, -1.1, 1.1, 1.98, 2.15)                # dashboard
    R(d, black, 3.9, 4.05, -1.05, 1.05, 2.15, 2.19)
    d.torus(black, 0.19, 0.022, (3.72, 0.55, 2.28), rot=(0, -1.0, 0), maj=32, mnr=10)
    d.tube(black, [(3.72, 0.55, 2.28), (3.92, 0.55, 2.05)], 0.03, 10)
    for x in (3.25, 2.0):
        for y in (-0.6, 0.6):
            R(d, seat, x - 0.25, x + 0.25, y - 0.27, y + 0.27, 1.98, 2.1)
            R(d, seat, x - 0.32, x - 0.22, y - 0.27, y + 0.27, 2.08, 2.75, rot=(0, 0.12, 0))
            R(d, seat, x - 0.34, x - 0.26, y - 0.15, y + 0.15, 2.76, 2.88, rot=(0, 0.12, 0))
    cabd = d.build(C, bevel=0.006, seg=2, parent=root)

    # ---------------- body details: compartments with roll-up shutters, pump panel
    d = Builder("Body_Details")
    comps = [(-3.85, -3.27, 0.98), (-3.15, -1.97, 1.3), (-1.93, -0.75, 1.3), (-0.65, 0.45, 0.98)]
    for s in (-1, 1):
        y_face = s * W
        for x0, x1, zb in comps:
            zt = 2.62
            R(d, alu, x0 - 0.04, x1 + 0.04, y_face - s * 0.01, y_face + s * 0.025, zb - 0.04, zb)
            R(d, alu, x0 - 0.04, x1 + 0.04, y_face - s * 0.01, y_face + s * 0.025, zt, zt + 0.08)
            for xx in (x0 - 0.04, x1):
                R(d, alu, xx, xx + 0.04, y_face - s * 0.01, y_face + s * 0.025, zb - 0.04, zt + 0.08)
            n = int((zt - zb) / 0.045)
            for i in range(n):
                z = zb + i * (zt - zb) / n
                R(d, alu, x0, x1, y_face, y_face + s * 0.018, z + 0.004, z + (zt - zb) / n - 0.002)
            R(d, alu, x0, x1, y_face, y_face + s * 0.04, zb, zb + 0.06)          # bottom bar
            R(d, black, (x0 + x1) / 2 - 0.18, (x0 + x1) / 2 + 0.18, y_face + s * 0.035, y_face + s * 0.065, zb + 0.07, zb + 0.1)
            R(d, chrome, (x0 + x1) / 2 - 0.2, (x0 + x1) / 2 + 0.2, y_face + s * 0.03, y_face + s * 0.045, zb + 0.065, zb + 0.105)
            # reflective stripe across shutters
            R(d, white_ref, x0, x1, y_face + s * 0.019, y_face + s * 0.024, 1.36, 1.5)
            R(d, lime, x0, x1, y_face + s * 0.019, y_face + s * 0.024, 1.52, 1.6)
        # stripe on red pillars between compartments
        for x0, x1 in ((-3.95, -3.89), (-3.23, -3.19), (-0.71, -0.69), (0.49, 1.35)):
            R(d, white_ref, x0, x1, y_face, y_face + s * 0.007, 1.36, 1.5)
            R(d, lime, x0, x1, y_face, y_face + s * 0.007, 1.52, 1.6)
        # rear wheel fenders (one long arch per tandem)
        for x in REAR_AXLES:
            d.arch(black, 0.69, 0.655, 0.5, (x, s * 1.08, WZ), seg=32, a0=0.0, a1=PI)
            d.arch(chrome, 0.705, 0.69, 0.51, (x, s * 1.08, WZ), seg=32, a0=0.05, a1=PI - 0.05)
        # side marker lights
        for x in (-3.7, -0.5, 1.0):
            R(d, amber, x - 0.05, x + 0.05, y_face, y_face + s * 0.02, 0.92, 0.96)
        # pump panel
        px0, px1 = 0.55, 1.3
        R(d, alu, px0, px1, y_face - s * 0.01, y_face + s * 0.02, 0.98, 2.62)
        for i, (gx, gz) in enumerate([(0.7, 2.35), (0.92, 2.35), (1.14, 2.35), (0.7, 2.12), (0.92, 2.12), (1.14, 2.12)]):
            rot = (PI / 2, 0, 0)
            d.cyl(chrome, 0.085, 0.03, (gx, y_face + s * 0.03, gz), rot=rot, seg=32)
            d.cyl(gauge, 0.07, 0.03, (gx, y_face + s * 0.04, gz), rot=rot, seg=32)
            a = random.Random(i).uniform(-1.2, 1.2)
            d.box(needle, (0.008, 0.006, 0.06), (gx + 0.025 * math.sin(a), y_face + s * 0.057, gz + 0.025 * math.cos(a)), (0, -a, 0))
        for i, (vx, vz, mt) in enumerate([(0.68, 1.75, red_dark), (0.92, 1.75, blue_p), (1.16, 1.75, yel_p),
                                           (0.68, 1.5, yel_p), (0.92, 1.5, red_dark), (1.16, 1.5, blue_p)]):
            d.cyl(chrome, 0.03, 0.12, (vx, y_face + s * 0.07, vz), rot=(PI / 2, 0, 0), seg=16)
            d.cyl(mt, 0.055, 0.03, (vx, y_face + s * 0.14, vz), rot=(PI / 2, 0, 0), seg=24)
            R(d, mt, vx - 0.012, vx + 0.012, y_face + s * 0.08, y_face + s * 0.1, vz - 0.12, vz)
        for ox in (0.75, 1.1):   # discharge outlets with caps & chains
            d.cyl(chrome, 0.07, 0.16, (ox, y_face + s * 0.1, 1.15), rot=(PI / 2, 0, 0), seg=24)
            d.cyl(chrome, 0.085, 0.05, (ox, y_face + s * 0.2, 1.15), rot=(PI / 2, 0, 0), seg=8)
            d.tube(chrome, [(ox, y_face + s * 0.2, 1.08), (ox + 0.02, y_face + s * 0.21, 0.98), (ox + 0.04, y_face + s * 0.03, 1.02)], 0.005, 6)
        R(d, black, 0.6, 1.25, y_face + s * 0.02, y_face + s * 0.03, 1.9, 1.98)   # label plate
        # hand rails along body top edge
        d.tube(chrome, [(-3.8, s * 1.2, 2.78), (-3.8, s * 1.2, 2.95), (1.2, s * 1.2, 2.95), (1.2, s * 1.2, 2.78)], 0.018, 10)
    # top deck
    R(d, plate, -3.95, 1.35, -W + 0.02, W - 0.02, 2.78, 2.81)
    # rear
    R(d, plate, -4.28, -3.95, -1.2, 1.2, 0.5, 0.58)                  # rear step
    R(d, black, -4.0, -3.95, -1.2, 1.2, 0.58, 0.88)
    for s in (-1, 1):
        y = s * 0.95
        R(d, chrome, -3.98, -3.95, y - 0.16, y + 0.16, 0.98, 1.72)
        for i, (mt, z0) in enumerate(((tail, 1.5), (amber, 1.3), (rev, 1.12), (tail, 1.0))):
            R(d, mt, -4.0, -3.97, y - 0.13, y + 0.13, z0 + 0.01, z0 + (0.2 if i == 0 else 0.17))
        d.cyl(beacon_r if s > 0 else beacon_b, 0.1, 0.16, (-3.85, s * 1.08, 2.9), seg=24)
        d.cyl(black, 0.11, 0.04, (-3.85, s * 1.08, 2.82), seg=24)
        R(d, white_ref, -3.97, -3.95, s * 0.35, s * 1.2, 1.36, 1.5)
    for i in range(10):   # rear chevrons
        x = -3.955
        z = 1.8 + (i % 2) * 0.0
        R(d, yellow if i % 2 else red_dark, x - 0.01, x, -0.8 + i * 0.16, -0.64 + i * 0.16, 1.8, 2.5)
    # rear ladder
    for y in (0.3, 0.75):
        d.tube(chrome, [(-3.96, y, 0.6), (-4.05, y, 0.65), (-4.05, y, 3.05), (-3.96, y, 3.1)], 0.02, 10)
    for i in range(8):
        z = 0.85 + i * 0.3
        d.cyl(alu, 0.016, 0.45, (-4.05, 0.525, z), rot=(PI / 2, 0, 0), seg=10)
    R(d, black, -3.96, -3.95, -0.3, 0.3, 0.62, 0.78)                 # plate holder
    bodyd = d.build(C, bevel=0.003, seg=1, parent=root)

    # ---------------- ladder rack + hose reel on top
    d = Builder("Roof_Ladder_HoseReel")
    def ladder(x0, x1, y0, y1, z, rail=(0.05, 0.1), pitch=0.3):
        R(d, alu, x0, x1, y0, y0 + rail[0], z, z + rail[1]); R(d, alu, x0, x1, y1 - rail[0], y1, z, z + rail[1])
        n = int((x1 - x0) / pitch)
        for i in range(n + 1):
            x = x0 + 0.05 + i * (x1 - x0 - 0.1) / n
            d.cyl(alu, 0.018, y1 - y0, (x, (y0 + y1) / 2, z + rail[1] / 2), rot=(PI / 2, 0, 0), seg=10)
    ladder(-3.75, 3.65, -0.38, 0.38, 3.28)
    ladder(-3.55, 3.25, -0.31, 0.31, 3.4)
    for x in (-3.4, -0.6, 2.2, 3.4):
        z0 = 2.81 if x < 1.35 else (3.12 if x < 2.4 else 2.98)
        for y in (-0.42, 0.42):
            R(d, black, x - 0.04, x + 0.04, y - 0.03, y + 0.03, z0, 3.28)
        R(d, black, x - 0.05, x + 0.05, -0.45, 0.45, 3.24, 3.28)
    # ladder hooks + pike poles
    for i, y in enumerate((-0.95, -0.85)):
        d.cyl(alu if i else yellow, 0.02, 3.4, (-1.5, y, 2.92), rot=(0, PI / 2, 0), seg=10)
    # hose reel
    xr = -2.9
    for y in (-0.95, 0.95):
        d.cyl(red_dark, 0.4, 0.04, (xr, y * 0.8, 3.3), rot=(PI / 2, 0, 0), seg=40)
        R(d, black, xr - 0.04, xr + 0.04, y * 0.8 - 0.03, y * 0.8 + 0.03, 2.81, 3.3)
    d.cyl(chrome, 0.06, 1.6, (xr, 0, 3.3), rot=(PI / 2, 0, 0), seg=20)
    for i in range(9):
        y = -0.66 + i * 0.165
        for k in range(3):
            d.torus(hose, 0.18 + k * 0.045, 0.024, (xr, y, 3.3), rot=(PI / 2, 0, 0), maj=40, mnr=10)
    # flat canvas hose coils on deck
    for k, x in enumerate((-1.2, -0.2)):
        for j in range(5):
            d.torus(hose_cream, 0.12 + j * 0.05, 0.022, (x, 0.75, 2.84), maj=36, mnr=8)
    # storage boxes
    R(d, alu, 0.3, 1.2, -1.15, -0.55, 2.81, 3.05); R(d, chrome, 0.6, 0.9, -1.16, -1.15, 2.95, 2.98)
    # deck gun / water monitor on the front of the body roof
    d.cyl(red_dark, 0.16, 0.18, (1.0, 0, 2.9), seg=24)
    d.cyl(chrome, 0.11, 0.12, (1.0, 0, 3.04), seg=24)
    d.tube(chrome, [(1.0, 0, 3.08), (1.0, 0, 3.25), (1.12, 0, 3.36), (1.4, 0, 3.45)], 0.06, 16)
    d.cyl(chrome, 0.075, 0.3, (1.55, 0, 3.5), rot=(0, PI / 2 - 0.3, 0), seg=20, r2=0.05)
    d.torus(red_dark, 0.07, 0.015, (1.42, 0, 3.46), rot=(0, PI / 2 - 0.3, 0), maj=20, mnr=6)
    d.tube(black, [(0.95, 0.1, 3.25), (0.85, 0.25, 3.2), (0.8, 0.3, 3.05)], 0.012, 6)
    roof = d.build(C, bevel=0.004, seg=1, parent=root)
    ew = empty("NODE_water", C, (1.72, 0, 3.55), 0.2); ew.parent = root

    # ---------------- chassis / underside
    d = Builder("Chassis")
    for y in (-0.45, 0.45):
        R(d, under, -3.95, 4.15, y - 0.06, y + 0.06, 0.58, 0.86)
    for x in (FRONT_AXLE,) + REAR_AXLES:
        d.cyl(under, 0.07, 2.0, (x, 0, WZ), rot=(PI / 2, 0, 0), seg=16)
        d.cyl(under, 0.16, 0.6, (x, 0, WZ), rot=(PI / 2, 0, 0), seg=20)   # diff
        for y in (-0.45, 0.45):                                          # leaf springs
            for k in range(5):
                R(d, under, x - 0.6 + k * 0.05, x + 0.6 - k * 0.05, y - 0.04, y + 0.04, WZ + 0.08 + k * 0.025, WZ + 0.1 + k * 0.025)
    d.cyl(chrome, 0.25, 0.9, (0.45, -0.98, 0.62), rot=(0, PI / 2, 0), seg=40)       # fuel tank
    for x in (0.1, 0.8):
        R(d, black, x - 0.03, x + 0.03, -1.25, -0.7, 0.36, 0.88)
    d.cyl(chrome, 0.06, 0.06, (0.6, -1.23, 0.75), rot=(PI / 2, 0, 0), seg=16)
    R(d, black, 0.0, 0.9, 0.7, 1.22, 0.4, 0.86)                                     # battery box
    d.tube(chrome, [(1.4, -0.7, 0.5), (0.2, -0.7, 0.45), (-0.3, -1.0, 0.42), (-0.35, -1.18, 0.4)], 0.05, 14)  # exhaust
    for s in (-1, 1):
        R(d, rubber, -3.35, -3.32, s * 0.85, s * 1.25, 0.18, 0.65)                 # mudflaps
        R(d, rubber, 2.73, 2.76, s * 0.9, s * 1.22, 0.25, 0.7)
    chassis = d.build(C, bevel=0.004, seg=1, parent=root)

    # ---------------- wheels
    def wheel(name, x, side, dual=False):
        w = Builder(name)
        offs = (0.0,) if not dual else (-0.2, 0.2)
        yc = side * (1.04 if not dual else 0.98)
        for k, oy in enumerate(offs):
            y = yc + oy * side
            w.cyl(rubber, WR, 0.36, (0, oy * side, 0), rot=(PI / 2, 0, 0), seg=64)
            # tread blocks (two staggered rows)
            nb = 44
            for i in range(nb):
                a = math.tau * i / nb
                for row, dy in enumerate((-0.09, 0.09)):
                    aa = a + (math.pi / nb if row else 0)
                    w.box(rubber, (0.075, 0.15, 0.028), (math.cos(aa) * (WR + 0.008), oy * side + dy, math.sin(aa) * (WR + 0.008)), (0, -aa + PI / 2, 0))
            # sidewall bulge
            for sd in (-1, 1):
                w.torus(rubber, WR - 0.07, 0.06, (0, oy * side + sd * 0.16, 0), rot=(PI / 2, 0, 0), maj=48, mnr=12)
        outer = side * (0.19 if not dual else 0.39)
        # rim
        w.cyl(chrome, 0.34, 0.3, (0, outer - side * 0.16, 0), rot=(PI / 2, 0, 0), seg=48)
        w.cyl(chrome, 0.35, 0.025, (0, outer - side * 0.01, 0), rot=(PI / 2, 0, 0), seg=48)
        w.cyl(under, 0.3, 0.02, (0, outer - side * 0.005, 0), rot=(PI / 2, 0, 0), seg=48)
        for i in range(10):   # rim vent holes (dark discs)
            a = math.tau * i / 10
            w.cyl(black, 0.045, 0.02, (math.cos(a) * 0.235, outer + side * 0.003, math.sin(a) * 0.235), rot=(PI / 2, 0, 0), seg=16)
        w.cyl(chrome, 0.13, 0.06, (0, outer + side * 0.02, 0), rot=(PI / 2, 0, 0), seg=32, r2=0.1)
        w.cyl(red_dark, 0.06, 0.03, (0, outer + side * 0.06, 0), rot=(PI / 2, 0, 0), seg=24)
        for i in range(10):   # lug nuts
            a = math.tau * i / 10
            w.cyl(chrome, 0.018, 0.05, (math.cos(a) * 0.165, outer + side * 0.03, math.sin(a) * 0.165), rot=(PI / 2, 0, 0), seg=6)
        o = w.build(C, bevel=0.004, seg=1, parent=root)
        o.location = (x, yc, WZ)
        bv = o.modifiers.get("Bevel")
        return o
    wheels = []
    for s, sn in ((1, "L"), (-1, "R")):
        wheels.append(wheel(f"Wheel_Front_{sn}", FRONT_AXLE, s))
        for i, x in enumerate(REAR_AXLES):
            wheels.append(wheel(f"Wheel_Rear{i+1}_{sn}", x, s, dual=True))

    # ---------------- lettering (converted to mesh)
    texts = []
    for s in (1, -1):
        rot = (PI / 2, 0, PI) if s > 0 else (PI / 2, 0, 0)
        texts.append(text_obj(f"Txt_Door_{s}", "FIRE\nRESCUE", C, 0.17, (2.83, s * 1.259, 1.72), rot, lettering, 0.003))
        texts.append(text_obj(f"Txt_Unit_{s}", "112", C, 0.2, (1.93, s * 1.259, 1.7), rot, gold, 0.003))
    t = text_obj("Txt_Front", "RESCUE", C, 0.13, (4.205, 0, 1.93), (PI / 2, 0, PI / 2), lettering, 0.003)
    texts.append(t)
    for t in texts:
        t.data.space_line = 0.85
        try:
            f = bpy.data.fonts.load("C:/Windows/Fonts/arialbd.ttf", check_existing=True); t.data.font = f
        except Exception: pass
        t.parent = root
    bpy.context.view_layer.update()
    for t in texts:
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(t.evaluated_get(dg))
        o = bpy.data.objects.new(t.name.replace("Txt_", "Decal_"), me); C.objects.link(o)
        o.matrix_world = t.matrix_world.copy(); o.parent = root; o.matrix_parent_inverse = root.matrix_world.inverted()
        bpy.data.objects.remove(t, do_unlink=True)

    # ---------------- smooth shading for all
    for o in C.objects:
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = True
            try: o.data.set_sharp_from_angle(angle=math.radians(32))
            except Exception: pass
    mark_asset(root, "Detailed fire engine (crew cab, roll-up compartments, pump panel, aerial ladder rack, hose reel, beacons).",
               ["fire truck", "vehicle", "emergency", "fire"])
    return root, C

root, C = build()
result = {"objects": len(C.objects), "tris": sum(len(o.data.polygons) for o in C.objects if o.type == 'MESH')}
