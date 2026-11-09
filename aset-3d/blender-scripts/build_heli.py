import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *
PI = math.pi

def loft(b, sections, seg, matfn):
    """sections: list of (x, half_w, half_h, zc). Builds closed loft along X. matfn(x,z,zc,hh)->material"""
    rings = []
    for (x, hw, hh, zc) in sections:
        ring = []
        for j in range(seg):
            a = math.tau * j / seg
            # superellipse for a slightly boxy cabin
            c, s = math.cos(a), math.sin(a)
            e = 2.6
            cy = math.copysign(abs(c) ** (2 / e), c); sz = math.copysign(abs(s) ** (2 / e), s)
            ring.append(b.bm.verts.new((x, cy * hw, zc + sz * hh)))
        rings.append(ring)
    faces = []
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for j in range(seg):
            f = b.bm.faces.new((A[j], B[j], B[(j + 1) % seg], A[(j + 1) % seg])); faces.append(f)
    for cap in (rings[0][::-1], rings[-1]):
        faces.append(b.bm.faces.new(cap))
    b.bm.normal_update()
    for f in faces:
        c = f.calc_center_median()
        # nearest section for zc/hh
        sec = min(sections, key=lambda s: abs(s[0] - c.x))
        m = matfn(c.x, c.z, sec[3], sec[2], c.y, f.normal)
        f.material_index = b._slot(m); f.smooth = True

def build(origin=(0, -40, 0)):
    purge(["M_Heli"])
    C = collection("A05_Helicopter")
    root = empty("WaterBombHelicopter", C, (0, 0, 0), 3)
    white = mat_paint("M_Heli_White", (0.8, 0.8, 0.78), 0.25, 0.12)
    red = mat_paint("M_Heli_Red", (0.6, 0.03, 0.02), 0.25, 0.15)
    orange = mat_paint("M_Heli_Orange", (0.9, 0.3, 0.02), 0.28, 0.1)
    grey = mat_noise("M_Heli_Grey", (0.12, 0.12, 0.13), (0.2, 0.2, 0.21), 10, (0.4, 0.6), 0.4, 0.1)
    dark = mat_basic("M_Heli_Dark", (0.02, 0.02, 0.022), 0.5)
    glass = mat_glass("M_Heli_Glass", (0.2, 0.3, 0.35), 0.02)
    chrome = mat_basic("M_Chrome", (0.92, 0.92, 0.94), 0.06, 1.0)
    blade = mat_noise("M_Heli_Blade", (0.05, 0.05, 0.055), (0.09, 0.09, 0.1), 30, (0.4, 0.55), 0.2, 0.05)
    tipy = mat_basic("M_Heli_BladeTip", (0.95, 0.75, 0.05), 0.4)
    bucket = mat_noise("M_Heli_Bucket", (0.85, 0.35, 0.03), (0.95, 0.45, 0.08), 25, (0.6, 0.8), 0, 0.3)
    canvas = mat_noise("M_Heli_BucketDark", (0.03, 0.03, 0.03), (0.07, 0.07, 0.07), 40, (0.7, 0.9), 0, 0.2)
    navR = mat_lens("M_Heli_NavRed", (1, 0.02, 0.01), 12); navG = mat_lens("M_Heli_NavGreen", (0.02, 1, 0.1), 12)
    strobe = mat_lens("M_Heli_Strobe", (1, 1, 1), 15)
    lettering = mat_basic("M_Lettering", (0.95, 0.95, 0.93), 0.3, 0, 0.4)

    # ---------------- fuselage
    b = Builder("Heli_Fuselage")
    secs = [(6.35, 0.12, 0.12, 1.45), (6.15, 0.55, 0.5, 1.5), (5.7, 0.92, 0.82, 1.6), (5.0, 1.15, 1.0, 1.7), (4.0, 1.28, 1.1, 1.78),
            (2.0, 1.32, 1.15, 1.82), (-0.5, 1.32, 1.15, 1.85), (-2.2, 1.22, 1.08, 1.92), (-3.3, 0.92, 0.85, 2.12), (-4.3, 0.55, 0.55, 2.35),
            (-6.5, 0.36, 0.38, 2.45), (-9.2, 0.24, 0.27, 2.55), (-10.0, 0.2, 0.24, 2.6), (-10.25, 0.05, 0.08, 2.62)]
    def matfn(x, z, zc, hh, y, n):
        rel = (z - zc) / max(hh, 1e-3)
        if x > 4.35 and rel > -0.05: return glass               # cockpit canopy
        if rel < -0.45: return red
        if rel < -0.3: return orange
        return white
    loft(b, secs, 40, matfn)
    # cabin windows + door outlines + step
    for s in (-1, 1):
        for i, x in enumerate((0.3, 1.25, 2.2, 3.15)):
            b.box(glass, (0.7, 0.03, 0.55), (x, s * 1.33, 2.2))
            b.box(dark, (0.78, 0.02, 0.63), (x, s * 1.325, 2.2))
        for (x0, x1) in ((-0.2, 2.75), (3.0, 4.1)):
            for xx in (x0, x1): b.box(dark, (0.02, 0.02, 1.85), (xx, s * 1.335, 1.75))
            b.box(dark, (x1 - x0, 0.02, 0.02), ((x0 + x1) / 2, s * 1.335, 2.68))
        b.box(chrome, (0.12, 0.04, 0.03), (2.6, s * 1.35, 1.9))
        b.box(grey, (1.6, 0.35, 0.05), (1.3, s * 1.45, 0.72))                    # side step
        # stripes
        b.box(orange, (4.3, 0.02, 0.1), (1.75, s * 1.335, 1.32))
        
    # nose details: wipers, pitot, landing light
    for y in (-0.35, 0.35): b.tube(dark, [(5.75, y, 2.0), (5.55, y * 0.6, 2.35)], 0.012, 6)
    b.tube(chrome, [(6.0, 0.25, 1.45), (6.7, 0.25, 1.45)], 0.02, 8)
    b.cyl(mat_emit("M_Heli_Landing", (1, 0.95, 0.85), 15), 0.14, 0.05, (6.0, 0, 0.98), rot=(0, 0.8, 0), seg=24)
    # engine cowling + exhaust + mast fairing
    b.box(white, (4.2, 1.4, 0.6), (0.3, 0, 3.15)); b.box(grey, (4.0, 1.3, 0.12), (0.3, 0, 2.9))
    for s in (-1, 1):
        for i in range(8): b.box(dark, (0.04, 0.02, 0.3), (-1.0 + i * 0.12, s * 0.71, 3.15))
        b.cyl(grey, 0.2, 0.7, (-1.95, s * 0.45, 3.2), rot=(0, PI / 2 + 0.2, s * 0.3), seg=20)
        b.cyl(dark, 0.16, 0.72, (-1.97, s * 0.45, 3.2), rot=(0, PI / 2 + 0.2, s * 0.3), seg=20)
    b.cyl(grey, 0.32, 0.5, (0.6, 0, 3.6), seg=24, r2=0.22)
    b.cyl(chrome, 0.12, 0.6, (0.6, 0, 3.95), seg=16)
    # tail: vertical fin, horizontal stabiliser, skid guard
    b.poly(white, [(-9.4, 2.45), (-10.4, 2.45), (-10.75, 4.1), (-10.2, 4.15)], 0.12)
    b.poly(red, [(-10.4, 2.45), (-10.75, 4.1), (-10.6, 4.1), (-10.3, 2.6)], 0.13)
    b.box(white, (0.7, 2.8, 0.07), (-8.4, 0, 2.5))
    for s in (-1, 1): b.box(white, (0.5, 0.06, 0.45), (-8.5, s * 1.4, 2.62))
    b.tube(grey, [(-9.9, 0, 2.35), (-10.2, 0, 1.9), (-10.5, 0, 1.95)], 0.03, 8)
    b.cyl(grey, 0.12, 0.5, (-10.25, 0.25, 3.6), rot=(PI / 2, 0, 0), seg=16)             # tail rotor gearbox
    # skids
    for s in (-1, 1):
        y = s * 1.15
        b.tube(chrome, [(4.2, y, 0.32), (3.9, y, 0.12), (3.4, y, 0.06), (-2.6, y, 0.06)], 0.06, 12)
        for x in (2.6, -1.0):
            b.tube(grey, [(x, s * 0.7, 0.85), (x, s * 1.0, 0.4), (x, y, 0.08)], 0.07, 12)
    # lights + antenna + beacon
    b.sphere(navR, 0.08, (-0.5, 1.36, 1.6)); b.sphere(navG, 0.08, (-0.5, -1.36, 1.6))
    b.sphere(strobe, 0.07, (-10.7, 0, 4.15)); b.sphere(navR, 0.09, (-2.0, 0, 2.95))
    b.box(dark, (0.03, 0.03, 0.4), (-3.0, 0, 3.0), (0, -0.4, 0))
    # bambi bucket on a cable/hook below the belly
    b.cyl(grey, 0.15, 0.15, (0.6, 0, 0.62), seg=12)
    b.tube(dark, [(0.6, 0, 0.55), (0.6, 0, -3.2)], 0.02, 6)
    for k in range(6):
        a = math.tau * k / 6
        b.tube(dark, [(0.6, 0, -3.2), (0.6 + math.cos(a) * 0.7, math.sin(a) * 0.7, -4.0)], 0.012, 5)
    b.cyl(bucket, 0.75, 1.0, (0.6, 0, -4.45), seg=40, r2=0.68, cap=False)
    b.torus(canvas, 0.74, 0.04, (0.6, 0, -3.97), maj=40, mnr=8)
    b.cyl(canvas, 0.62, 0.25, (0.6, 0, -5.05), seg=32, r2=0.25)
    for k in range(8):
        a = math.tau * k / 8
        b.box(canvas, (0.04, 0.04, 1.0), (0.6 + math.cos(a) * 0.73, math.sin(a) * 0.73, -4.45))
    fus = b.build(C, bevel=0.0, parent=root, smooth_angle=40)

    # ---------------- rotors (separate objects so they can spin in AR)
    r = Builder("ROTOR_main")
    r.cyl(grey, 0.35, 0.18, (0, 0, 0), seg=24)
    r.cyl(chrome, 0.1, 0.35, (0, 0, 0.2), seg=12)
    for k in range(4):
        a = math.tau * k / 4 + 0.3
        for (r0, r1, mt) in ((0.3, 6.6, blade), (6.6, 7.0, tipy)):
            rc = (r0 + r1) / 2
            r.box(mt, (r1 - r0, 0.42, 0.05), (math.cos(a) * rc, math.sin(a) * rc, 0.05 - rc * 0.006), (0.04, 0, a))
        r.box(grey, (0.5, 0.2, 0.12), (math.cos(a) * 0.45, math.sin(a) * 0.45, 0.02), (0, 0, a))
    rot_main = r.build(C, parent=root); rot_main.location = (0.6, 0, 4.3)
    t = Builder("ROTOR_tail")
    t.cyl(grey, 0.1, 0.12, (0, 0, 0), rot=(PI / 2, 0, 0), seg=16)
    for k in range(2):
        a = PI * k + 0.5
        for (r0, r1, mt) in ((0.08, 1.05, blade), (1.05, 1.2, tipy)):
            rc = (r0 + r1) / 2
            t.box(mt, (r1 - r0, 0.03, 0.2), (math.cos(a) * rc, 0.05, math.sin(a) * rc), (0, -a, 0))
    rot_tail = t.build(C, parent=root); rot_tail.location = (-10.25, 0.45, 3.6)
    rot_main["ar_part"] = "ROTOR_main"; rot_tail["ar_part"] = "ROTOR_tail"

    # decals
    texts = [text_obj(f"Txt_H_{s}", "WATER BOMBING", C, 0.26, (-6.2, s * 0.43, 2.47), (PI / 2, 0, PI) if s > 0 else (PI / 2, 0, 0), lettering, 0.004) for s in (1, -1)]
    texts += [text_obj(f"Txt_R_{s}", "PK-WBX", C, 0.34, (1.2, s * 1.34, 1.55), (PI / 2, 0, PI) if s > 0 else (PI / 2, 0, 0), lettering, 0.004) for s in (1, -1)]
    try: f = bpy.data.fonts.load("C:/Windows/Fonts/arialbd.ttf", check_existing=True)
    except Exception: f = None
    bpy.context.view_layer.update()
    for tx in texts:
        if f: tx.data.font = f
    bpy.context.view_layer.update()
    for tx in texts:
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(tx.evaluated_get(dg))
        o = bpy.data.objects.new(tx.name.replace("Txt_", "Decal_"), me); C.objects.link(o)
        o.matrix_world = tx.matrix_world.copy(); o.parent = root
        bpy.data.objects.remove(tx, do_unlink=True)

    # water outlet marker (for AR) under the bucket
    e = empty("NODE_water_out", C, (0.6, 0, -5.2), 0.3); e.parent = root
    for o in C.objects:
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = True
            try: o.data.set_sharp_from_angle(angle=math.radians(35))
            except Exception: pass
    root.location = origin
    mark_asset(root, "Firefighting helicopter with bambi bucket (water bombing); separate main/tail rotors.", ["helicopter", "water bombing", "firefighting"])
    return root, C

root, C = build()
result = {"objs": len(C.objects)}
