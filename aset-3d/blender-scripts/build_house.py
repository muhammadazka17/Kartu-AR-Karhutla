import bpy, math, random
from mathutils import Vector
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *
PI = math.pi

def build(origin=(0, 22, 0)):
    rnd = random.Random(7)
    purge(["M_House", "M_Shingle", "M_FieldStone", "M_Mortar", "M_SootGlass", "M_RustIron", "FX_"])
    C = collection("A02_BurningWoodHouse")
    root = empty("BurningWoodHouse", C, (0, 0, 0), 3.0)
    WOOD = (0.2, 0.12, 0.065)
    m_fresh = mat_wood("M_House_Wood", WOOD, 0.75)
    m_burn = mat_burning("M_House_WoodBurning", WOOD, burn=0.4, scale=0.9, ember_str=4)
    m_char = mat_burning("M_House_WoodCharred", (0.15, 0.09, 0.05), burn=0.9, scale=1.6, ember_str=8)
    m_trim = mat_noise("M_House_TrimPaint", (0.3, 0.29, 0.26), (0.45, 0.43, 0.39), 25, (0.6, 0.85), 0, 0.2)
    m_trim_burn = mat_burning("M_House_TrimBurning", (0.35, 0.33, 0.29), burn=0.5, scale=1.1, ember_str=3, rings=False)
    m_shingle = mat_noise("M_Shingle", (0.08, 0.06, 0.05), (0.2, 0.15, 0.11), 18, (0.75, 0.95), 0, 0.35)
    m_shingle_b = mat_burning("M_ShingleBurning", (0.12, 0.09, 0.07), burn=0.65, scale=1.3, ember_str=5, rings=False)
    m_stone = mat_noise("M_FieldStone", (0.07, 0.065, 0.06), (0.2, 0.19, 0.17), 6, (0.7, 0.95), 0, 0.6, voronoi=True)
    m_mortar = mat_noise("M_Mortar", (0.1, 0.095, 0.09), (0.15, 0.14, 0.13), 30, (0.85, 1.0), 0, 0.2)
    m_glass = mat_glass("M_SootGlass", (0.25, 0.22, 0.2), 0.25)
    m_inside = mat_burning("M_House_InteriorBurnt", (0.12, 0.08, 0.05), burn=0.8, scale=0.7, ember_str=3)
    m_iron = mat_noise("M_RustIron", (0.08, 0.05, 0.03), (0.3, 0.12, 0.05), 20, (0.6, 0.9), 0.6, 0.4)

    X0, X1, Y0, Y1 = -4.0, 4.0, -3.0, 3.0
    ZF, ZW = 0.5, 3.3           # floor level, wall top
    ZR = 5.6                    # ridge
    BH = 0.2                    # board height

    def pick(x, z, bias=0.0):
        s = (x - X0) / 8 * 0.55 + z / ZR * 0.45 + rnd.uniform(-0.15, 0.15) + bias
        return m_char if s > 0.78 else (m_burn if s > 0.42 else m_fresh)

    walls = Builder("House_Walls")
    def siding(axis, plane, out, u0, u1, z0, z1, openings, gable=False):
        z = z0
        while z < z1 - 1e-4:
            h = min(BH, z1 - z)
            if gable:
                t0 = (z - ZW) / (ZR - ZW); half = (u1 - u0) / 2 * (1 - t0); c = (u0 + u1) / 2
                spans = [(c - half, c + half)] if half > 0.05 else []
            else:
                spans = [(u0, u1)]
            for (a0, a1, oz0, oz1) in openings:
                if oz0 < z + h and oz1 > z:
                    ns = []
                    for s0, s1 in spans:
                        if a1 <= s0 or a0 >= s1: ns.append((s0, s1)); continue
                        if a0 > s0: ns.append((s0, a0))
                        if a1 < s1: ns.append((a1, s1))
                    spans = ns
            for s0, s1 in spans:
                L = s1 - s0
                if L < 0.03: continue
                c = (s0 + s1) / 2; zc = z + h / 2
                tilt = 0.07
                if axis == 'x':
                    loc = (c, plane + out * 0.02, zc); size = (L, 0.07, h + 0.035); rot = (tilt * out, 0, 0); xx = c
                else:
                    loc = (plane + out * 0.02, c, zc); size = (0.07, L, h + 0.035); rot = (0, -tilt * out, 0); xx = plane
                walls.box(pick(xx, zc), size, loc, rot)
            z += BH

    WIN = 1.2
    front = [(-0.5, 0.5, ZF, 2.6), (-3.0, -1.8, 1.3, 2.5), (1.8, 3.0, 1.3, 2.5)]
    back = [(-2.5, -1.3, 1.3, 2.5), (1.3, 2.5, 1.3, 2.5)]
    side = [(-0.6, 0.6, 1.3, 2.5)]
    attic = [(-0.35, 0.35, 3.9, 4.6)]
    siding('x', Y0, -1, X0, X1, ZF, ZW, front)
    siding('x', Y1, 1, X0, X1, ZF, ZW, back)
    siding('y', X0, -1, Y0, Y1, ZF, ZW, side)
    siding('y', X1, 1, Y0, Y1, ZF, ZW, side)
    siding('y', X0, -1, Y0, Y1, ZW, ZR, attic, gable=True)
    siding('y', X1, 1, Y0, Y1, ZW, ZR, attic, gable=True)
    # corner boards
    for x in (X0, X1):
        for y in (Y0, Y1):
            walls.box(m_trim_burn if x > 0 else m_trim, (0.16, 0.16, ZW - ZF + 0.1), (x + (0.03 if x > 0 else -0.03), y + (0.03 if y > 0 else -0.03), (ZF + ZW) / 2))
    # interior lining (dark, burnt) so windows read as rooms
    walls.box(m_inside, (8.0 - 0.3, 0.06, ZW - ZF), (0, Y1 - 0.12, (ZF + ZW) / 2))
    walls.box(m_inside, (0.06, 6.0 - 0.3, ZW - ZF), (X1 - 0.12, 0, (ZF + ZW) / 2))
    walls.box(m_inside, (0.06, 6.0 - 0.3, ZW - ZF), (X0 + 0.12, 0, (ZF + ZW) / 2))
    walls.box(m_inside, (0.08, 4.0, ZW - ZF), (0.8, 0.6, (ZF + ZW) / 2))   # partition wall
    walls.box(m_inside, (8.0, 6.0, 0.06), (0, 0, ZW - 0.05))             # ceiling
    wall_o = walls.build(C, bevel=0.008, seg=1, parent=root)

    # ---------------- windows / door trim
    t = Builder("House_WindowsDoors")
    def window(axis, plane, out, a0, a1, z0, z1, broken=0.5, burnt=False, seed=0):
        r = random.Random(seed); tm = m_trim_burn if burnt else m_trim
        w = 0.09; d = 0.12
        def B(u, v, su, sv, sz, z, mat=tm):   # u along wall, v outward offset
            if axis == 'x': t.box(mat, (su, sv, sz), (u, plane + out * v, z))
            else: t.box(mat, (sv, su, sz), (plane + out * v, u, z))
        cu = (a0 + a1) / 2; W_ = a1 - a0
        B(a0 - w / 2, 0.06, w, d, z1 - z0 + w * 2, (z0 + z1) / 2); B(a1 + w / 2, 0.06, w, d, z1 - z0 + w * 2, (z0 + z1) / 2)
        B(cu, 0.06, W_ + 2 * w, d, w, z1 + w / 2)
        B(cu, 0.06, W_ + 0.1, d * 0.6, 0.03, z1 + w + 0.015)               # drip cap
        B(cu, 0.12, W_ + 0.3, 0.2, 0.06, z0 - 0.03)                          # sill
        B(cu, 0.1, W_ + 0.1, 0.06, 0.08, z0 - 0.1)                           # apron
        B(cu, -0.02, 0.05, 0.06, z1 - z0, (z0 + z1) / 2)                     # mullion
        B(cu, -0.02, W_, 0.06, 0.05, (z0 + z1) / 2)                          # muntin
        for i in range(2):
            for j in range(2):
                if r.random() < broken: 
                    # jagged shard remaining in corner
                    pu = a0 + (i + 0.5) * W_ / 2; pz = z0 + (j + 0.5) * (z1 - z0) / 2
                    pts = [(-W_ / 4, -(z1 - z0) / 4), (W_ / 4 * r.uniform(-0.3, 0.6), -(z1 - z0) / 4), (-W_ / 4, (z1 - z0) / 4 * r.uniform(-0.2, 0.7))]
                    if axis == 'x': t.poly(m_glass, pts, 0.008, (pu, plane - out * 0.0, pz))
                    else: t.poly(m_glass, pts, 0.008, (plane - out * 0.0, pu, pz), rot=(0, 0, PI / 2))
                    continue
                pu = a0 + (i + 0.5) * W_ / 2; pz = z0 + (j + 0.5) * (z1 - z0) / 2
                B(pu, 0.0, W_ / 2 - 0.04, 0.008, (z1 - z0) / 2 - 0.04, pz, m_glass)
        # shutters (one hanging askew)
        for k, uu in enumerate((a0 - 0.1 - W_ / 4, a1 + 0.1 + W_ / 4)):
            rot_off = r.uniform(-0.25, 0.25) if k == 1 and broken > 0.5 else 0
            for sl in range(7):
                zz = z0 + 0.05 + sl * (z1 - z0) / 7
                if axis == 'x': t.box(tm, (W_ / 2, 0.025, (z1 - z0) / 7 + 0.01), (uu, plane + out * 0.08, zz + (z1 - z0) / 14), (0.35 * out, rot_off, 0))
                else: t.box(tm, (0.025, W_ / 2, (z1 - z0) / 7 + 0.01), (plane + out * 0.08, uu, zz + (z1 - z0) / 14), (rot_off, -0.35 * out, 0))
    window('x', Y0, -1, -3.0, -1.8, 1.3, 2.5, 0.25, False, 1)
    window('x', Y0, -1, 1.8, 3.0, 1.3, 2.5, 0.9, True, 2)
    window('x', Y1, 1, -2.5, -1.3, 1.3, 2.5, 0.3, False, 3)
    window('x', Y1, 1, 1.3, 2.5, 1.3, 2.5, 0.8, True, 4)
    window('y', X0, -1, -0.6, 0.6, 1.3, 2.5, 0.2, False, 5)
    window('y', X1, 1, -0.6, 0.6, 1.3, 2.5, 1.0, True, 6)
    window('y', X0, -1, -0.35, 0.35, 3.9, 4.6, 0.5, False, 7)
    window('y', X1, 1, -0.35, 0.35, 3.9, 4.6, 1.0, True, 8)
    # door frame + door hanging open
    for x in (-0.55, 0.55): t.box(m_trim, (0.1, 0.14, 2.15), (x, Y0 - 0.06, ZF + 1.05))
    t.box(m_trim, (1.2, 0.14, 0.12), (0, Y0 - 0.06, 2.66))
    door_planks = 6
    for i in range(door_planks):
        u = -0.45 + 0.9 * (i + 0.5) / door_planks
        p = Vector((u + 0.45, 0, 0)); a = -0.9
        loc = Vector((-0.45 + p.x * math.cos(a), Y0 - 0.02 + p.x * math.sin(a), ZF + 1.03))
        t.box(m_burn, (0.9 / door_planks - 0.01, 0.05, 2.04), loc, (0, 0, a))
    for zz in (0.9, 2.2):
        loc = Vector((-0.45 + 0.45 * math.cos(-0.9), Y0 - 0.06 + 0.45 * math.sin(-0.9), zz))
        t.box(m_iron, (0.85, 0.02, 0.08), loc, (0, 0, -0.9))
    wins = t.build(C, bevel=0.006, seg=1, parent=root)

    # ---------------- foundation + chimney (field stone)
    s = Builder("House_StoneWork")
    def stones(x0, x1, y0, y1, z0, z1, size=0.32, seed=1):
        r = random.Random(seed)
        z = z0
        while z < z1 - 0.02:
            h = r.uniform(0.16, 0.24); h = min(h, z1 - z)
            # run around the rectangle perimeter
            for (ax, a0, a1, fixed) in (('x', x0, x1, y0), ('x', x0, x1, y1), ('y', y0, y1, x0), ('y', y0, y1, x1)):
                u = a0 + r.uniform(-0.1, 0)
                while u < a1:
                    L = min(r.uniform(size * 0.7, size * 1.4), a1 - u)
                    if L > 0.04:
                        cu = u + L / 2; j = r.uniform(-0.012, 0.012)
                        if ax == 'x': s.box(m_stone, (L - 0.02, 0.22, h - 0.02), (cu, fixed + j, z + h / 2), (0, 0, r.uniform(-0.03, 0.03)))
                        else: s.box(m_stone, (0.22, L - 0.02, h - 0.02), (fixed + j, cu, z + h / 2), (0, 0, r.uniform(-0.03, 0.03)))
                    u += L
            z += h
        s.box(m_mortar, (x1 - x0 - 0.04, y1 - y0 - 0.04, z1 - z0 - 0.02), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    stones(X0 - 0.05, X1 + 0.05, Y0 - 0.05, Y1 + 0.05, 0.0, ZF, 0.38, 11)
    stones(-4.75, -4.1, -0.45, 0.45, 0.0, 6.4, 0.3, 12)
    s.box(m_stone, (0.85, 1.1, 0.12), (-4.42, 0, 6.45))
    s.box(m_mortar, (0.4, 0.5, 0.35), (-4.42, 0, 6.68))
    stone_o = s.build(C, bevel=0.025, seg=2, parent=root)
    for mname, strength, scale in (("DispStone", 0.03, 0.08),):
        displace(stone_o, strength, scale, 'CLOUDS', 0)

    # ---------------- roof
    r = Builder("House_Roof")
    run = (Y1 - Y0) / 2 + 0.45; rise = ZR - ZW; ang = math.atan2(rise, run - 0.45)
    slope_len = run / math.cos(ang)
    hole = (0.3, 2.6, 0.25, 0.85)  # x0,x1, t0,t1 (fraction along front slope from eave to ridge)
    for side_ in (-1, 1):             # -1 front slope (faces -Y), +1 back slope
        # rafters
        x = X0 - 0.4
        while x <= X1 + 0.41:
            mid_t = 0.5
            cy = side_ * (run * (1 - mid_t)); cz = ZR - rise / (run - 0.45) * run * (1 - mid_t) + 0.0
            loc = (x, side_ * run / 2, ZR - (run / 2) * math.tan(ang) - 0.12)
            r.box(m_char if (side_ < 0 and hole[0] - 0.4 < x < hole[1] + 0.4) else m_burn, (0.06, slope_len, 0.18), loc, ((ang if side_ < 0 else -ang), 0, 0))
            x += 0.6
        # sheathing + shingles
        rows = int(slope_len / 0.26)
        for i in range(rows):
            tt = (i + 0.5) / rows
            yy = side_ * run * (1 - tt); zz = ZR - math.tan(ang) * run * (1 - tt)
            xx = X0 - 0.45 + (0.17 if i % 2 else 0)
            while xx < X1 + 0.45:
                w = 0.34
                in_hole = side_ < 0 and hole[0] < xx < hole[1] and hole[2] < tt < hole[3]
                near = side_ < 0 and hole[0] - 1.2 < xx < hole[1] + 1.0 and hole[2] - 0.2 < tt < hole[3] + 0.15
                if not in_hole:
                    if near and rnd.random() < 0.18:
                        xx += w; continue              # missing shingle
                    mat = m_shingle_b if (near or (xx > 1.5 and rnd.random() < 0.5)) else m_shingle
                    lift = rnd.uniform(0, 0.04) if near else rnd.uniform(0, 0.008)
                    nrm = Vector((0, side_ * math.sin(ang), math.cos(ang)))
                    loc = Vector((xx + w / 2, yy, zz)) + nrm * (0.02 + lift)
                    r.box(mat, (w - 0.012, 0.34, 0.022), loc, ((ang if side_ < 0 else -ang) + rnd.uniform(-0.03, 0.03) + (rnd.uniform(-0.15, 0.05) if near else 0), rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02)))
                xx += w
        # sheathing (planks) except hole
        for i in range(int(slope_len / 0.3)):
            tt = (i + 0.5) / int(slope_len / 0.3)
            yy = side_ * run * (1 - tt); zz = ZR - math.tan(ang) * run * (1 - tt)
            segs = [(X0 - 0.45, X1 + 0.45)]
            if side_ < 0 and hole[2] < tt < hole[3]:
                segs = [(X0 - 0.45, hole[0] + rnd.uniform(-0.2, 0.2)), (hole[1] + rnd.uniform(-0.2, 0.2), X1 + 0.45)]
            for a0, a1 in segs:
                r.box(m_burn if side_ < 0 else m_fresh, (a1 - a0, 0.29, 0.025), ((a0 + a1) / 2, yy, zz), ((ang if side_ < 0 else -ang), 0, 0))
        # fascia
        r.box(m_trim_burn, (8.9, 0.04, 0.2), (0, side_ * (run + 0.02), ZR - math.tan(ang) * run - 0.06))
    # ridge cap + rake boards
    r.box(m_shingle, (8.9, 0.22, 0.06), (0, 0, ZR + 0.03))
    for x in (X0 - 0.45, X1 + 0.45):
        for side_ in (-1, 1):
            r.box(m_trim_burn if x > 0 else m_trim, (0.05, slope_len + 0.1, 0.2), (x, side_ * run / 2, ZR - run / 2 * math.tan(ang) - 0.02), ((ang if side_ < 0 else -ang), 0, 0))
    # broken charred beams poking out of the hole
    for i in range(4):
        x = rnd.uniform(hole[0] + 0.2, hole[1] - 0.2)
        r.box(m_char, (0.1, 1.6, 0.12), (x, -1.2, 4.6), (rnd.uniform(-0.9, -0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-0.4, 0.4)))
    roof_o = r.build(C, bevel=0.006, seg=1, parent=root)

    # ---------------- porch
    p = Builder("House_Porch")
    PY0, PY1 = -5.2, Y0
    for i in range(int((PY1 - PY0) / 0.15)):
        y = PY0 + 0.075 + i * 0.15
        for x0, x1 in ((X0, -0.2), (-0.2, X1)):
            p.box(m_burn if x0 > 0 else m_fresh, (x1 - x0 - 0.01, 0.13, 0.04), ((x0 + x1) / 2, y, 0.48), (0, 0, rnd.uniform(-0.004, 0.004)))
    for x in (X0, -2.0, 0, 2.0, X1):
        p.box(m_fresh, (0.08, PY1 - PY0, 0.2), (x, (PY0 + PY1) / 2, 0.36))
    p.box(m_fresh, (8.0, 0.12, 0.3), (0, PY0 + 0.06, 0.31))
    posts = (-3.9, -1.3, 1.3, 3.9)
    for i, x in enumerate(posts):
        m = m_char if x > 2 else (m_burn if x > 0 else m_fresh)
        p.box(m, (0.16, 0.16, 2.3), (x, PY0 + 0.15, 0.5 + 1.15))
        p.box(m_stone, (0.3, 0.3, 0.45), (x, PY0 + 0.15, 0.22))
        p.box(m_trim, (0.24, 0.24, 0.06), (x, PY0 + 0.15, 2.8))
    # railing with balusters (gap at stairs)
    for xa, xb in ((-3.9, -1.3), (1.3, 3.9)):
        m = m_burn if xa > 0 else m_fresh
        p.box(m, (xb - xa, 0.09, 0.07), ((xa + xb) / 2, PY0 + 0.15, 1.45))
        p.box(m, (xb - xa, 0.07, 0.06), ((xa + xb) / 2, PY0 + 0.15, 0.6))
        n = int((xb - xa) / 0.14)
        for k in range(1, n):
            x = xa + k * (xb - xa) / n
            if xa > 0 and 2.6 < x < 3.3: 
                p.box(m_char, (0.04, 0.04, 0.5), (x, PY0 + 0.2, 0.75), (rnd.uniform(-0.6, 0.6), rnd.uniform(0.3, 1.0), 0))
                continue
            p.box(m, (0.045, 0.045, 0.82), (x, PY0 + 0.15, 1.03))
    for yy in (-4.0, -3.1):   # side rails
        pass
    for sx in (X0, X1):
        m = m_burn if sx > 0 else m_fresh
        p.box(m, (0.09, PY1 - PY0 - 0.2, 0.07), (sx + (0.0), (PY0 + PY1) / 2 + 0.05, 1.45))
        for k in range(1, 14):
            y = PY0 + 0.15 + k * (PY1 - PY0 - 0.15) / 14
            p.box(m, (0.045, 0.045, 0.82), (sx, y, 1.03))
    # stairs
    for k in range(3):
        p.box(m_fresh, (1.4, 0.32, 0.05), (0, PY0 - 0.18 - k * 0.3, 0.46 - (k + 1) * 0.15))
        p.box(m_fresh, (1.4, 0.04, 0.15), (0, PY0 - 0.04 - k * 0.3, 0.46 - (k + 1) * 0.15 - 0.07))
    for x in (-0.68, 0.68):
        p.box(m_fresh, (0.06, 1.1, 0.25), (x, PY0 - 0.5, 0.2), (0.45, 0, 0))
    # porch roof (lean-to)
    pz0, pz1 = 3.18, 2.82
    pang = math.atan2(pz0 - pz1, PY1 - PY0 + 0.4)
    plen = (PY1 - PY0 + 0.45) / math.cos(pang)
    p.box(m_burn, (8.4, 0.18, 0.2), (0, PY0 + 0.15, 2.92))                # beam
    for x in [X0 + i * 0.6 for i in range(14)]:
        p.box(m_burn if x < 2 else m_char, (0.06, plen, 0.14), (x, (PY0 + PY1) / 2 - 0.15, (pz0 + pz1) / 2 + 0.05), (pang, 0, 0))
    rows = int(plen / 0.26)
    for i in range(rows):
        tt = (i + 0.5) / rows
        yy = PY1 - tt * (PY1 - PY0 + 0.45); zz = pz0 - math.tan(pang) * tt * (PY1 - PY0 + 0.45) + 0.16
        xx = X0 - 0.2 + (0.17 if i % 2 else 0)
        while xx < X1 + 0.2:
            if xx > 2.4 and rnd.random() < 0.35: xx += 0.34; continue
            mat = m_shingle_b if xx > 1.2 else m_shingle
            p.box(mat, (0.33, 0.34, 0.022), (xx + 0.17, yy, zz), (pang + rnd.uniform(-0.03, 0.03), 0, rnd.uniform(-0.02, 0.02)))
            xx += 0.34
    # props: rocking chair-ish bench, barrel, lantern
    p.box(m_fresh, (1.2, 0.4, 0.05), (-2.6, -3.35, 0.95)); p.box(m_fresh, (1.2, 0.05, 0.5), (-2.6, -3.15, 1.2))
    for x in (-3.1, -2.1): p.box(m_fresh, (0.06, 0.35, 0.45), (x, -3.35, 0.72))
    p.cyl(m_burn, 0.28, 0.75, (3.3, -3.6, 0.88), seg=24)
    for zz in (0.62, 1.12): p.torus(m_iron, 0.285, 0.012, (3.3, -3.6, zz), maj=32, mnr=6)
    porch_o = p.build(C, bevel=0.005, seg=1, parent=root)

    # ---------------- interior: floor + debris
    f = Builder("House_InteriorFloor")
    for i in range(int(6 / 0.14)):
        y = Y0 + 0.07 + i * 0.14
        f.box(m_inside, (7.9, 0.13, 0.04), (0, y, ZF + 0.0))
    for i in range(14):
        f.box(m_char, (rnd.uniform(0.6, 1.6), 0.1, 0.1), (rnd.uniform(-1, 3.5), rnd.uniform(-2.5, 2.5), ZF + 0.08), (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.3, 0.3), rnd.uniform(0, PI)))
    f.build(C, bevel=0.004, seg=1, parent=root)

    # ---------------- FIRE + SMOKE
    fx = collection("A02_FX", C)
    fire("F_RoofHole", fx, (1.45, -1.6, 4.0), 0.9, 2.8, 16, 21, power=4500, parent=root)
    fire("F_RoofHole2", fx, (2.1, -1.0, 4.4), 0.6, 2.0, 9, 22, power=1500, parent=root)
    fire("F_WinFR", fx, (2.4, Y0 - 0.15, 1.35), 0.45, 1.9, 9, 23, power=1500, parent=root)
    fire("F_WinSide", fx, (X1 + 0.15, 0, 1.35), 0.45, 1.9, 9, 24, power=1500, parent=root)
    fire("F_WinBack", fx, (1.9, Y1 + 0.15, 1.35), 0.4, 1.4, 7, 25, power=900, parent=root)
    fire("F_Attic", fx, (X1 + 0.12, 0, 3.95), 0.25, 1.1, 6, 26, power=500, parent=root)
    fire("F_PorchRoof", fx, (3.2, -4.4, 3.0), 0.6, 1.3, 9, 27, power=1100, parent=root)
    fire("F_PorchFloor", fx, (3.2, -3.9, 0.5), 0.5, 0.8, 7, 28, power=500, parent=root)
    fire("F_Inside1", fx, (2.4, -1.8, ZF), 0.9, 2.2, 10, 29, power=3500, parent=root)
    fire("F_Inside2", fx, (2.8, 1.6, ZF), 0.8, 2.0, 8, 30, power=2500, parent=root)
    fire("F_Inside3", fx, (-1.0, 0.4, ZF), 0.6, 1.2, 6, 31, power=900, parent=root)
    fire("F_Door", fx, (0.0, -2.5, ZF), 0.4, 1.3, 6, 32, power=700, parent=root)
    smoke("S_Main", fx, (1.6, -1.3, 6.0), 9.0, 2.0, 12, 41, density=3.0, color=(0.03, 0.028, 0.026), drift=(0.08, 0.04), parent=root, glow=0.0)
    smoke("S_Win", fx, (2.4, -3.6, 3.4), 3.0, 0.7, 6, 42, density=2.2, color=(0.04, 0.04, 0.04), drift=(0.1, -0.05), parent=root)
    smoke("S_Side", fx, (4.6, 0, 3.6), 3.0, 0.7, 6, 43, density=2.2, color=(0.04, 0.04, 0.04), drift=(0.15, 0.05), parent=root)
    smoke("S_Chimney", fx, (-4.42, 0, 7.0), 3.5, 0.45, 7, 44, density=0.8, color=(0.25, 0.25, 0.25), drift=(-0.2, 0.05), parent=root)
    embers("E_House", fx, (1.6, -1.5, 3.5), 3.2, 6.5, 260, 51, parent=root)
    embers("E_Ground", fx, (2.5, -4.5, 0.05), 2.5, 0.25, 90, 52, parent=root, rmin=0.008, rmax=0.025)

    for o in C.all_objects:
        if o.type == 'MESH' and not o.get("fx"):
            for pg in o.data.polygons: pg.use_smooth = True
            try: o.data.set_sharp_from_angle(angle=math.radians(30))
            except Exception: pass
    root.location = origin
    mark_asset(root, "Burning wooden cabin: lap siding, broken windows, shingle roof with burnt-through hole, porch, stone chimney, flames/smoke/embers.",
               ["house", "fire", "burning", "building", "disaster"])
    return root, C

root, C = build()
result = {"objects": len(C.all_objects), "polys": sum(len(o.data.polygons) for o in C.all_objects if o.type == 'MESH')}
