import bpy, math, random
from mathutils import Vector
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *
PI = math.pi

def build(origin=(18, 22, 0)):
    rnd = random.Random(99)
    purge(["M_Ruin"])
    C = collection("A02b_BurnedStoneRuin")
    root = empty("BurnedStoneRuin", C, (0, 0, 0), 3.0)
    m_stone = mat_burning("M_Ruin_Stone", (0.17, 0.15, 0.12), burn=0.45, scale=0.8, ember_str=0.0, rings=False)
    m_stone2 = mat_burning("M_Ruin_StoneDark", (0.11, 0.1, 0.085), burn=0.6, scale=1.1, ember_str=0.0, rings=False)
    m_plaster = mat_noise("M_Ruin_Plaster", (0.05, 0.045, 0.04), (0.16, 0.14, 0.12), 3, (0.85, 1.0), 0, 0.4)
    m_beam = mat_burning("M_Ruin_Beam", (0.12, 0.07, 0.04), burn=0.9, scale=2.0, ember_str=9)
    m_ash = mat_noise("M_Ruin_Ash", (0.03, 0.03, 0.03), (0.12, 0.115, 0.11), 9, (0.9, 1.0), 0, 0.5)
    X0, X1, Y0, Y1 = -3.6, 3.6, -2.8, 2.8
    T = 0.36; H = 6.4
    def hmax(u_world, wall):
        base = H - 0.6 * (0.5 + 0.5 * math.sin(u_world * 1.7 + wall)) - 0.4 * (0.5 + 0.5 * math.sin(u_world * 4.1 + wall * 2))
        if wall == 0 and u_world > 0.8: base -= (u_world - 0.8) * 1.3       # front-right collapse
        if wall == 3: base -= 1.2 + 0.6 * math.sin(u_world * 2.0)            # right wall partly gone
        if wall == 1 and u_world < -1.5: base -= 0.9
        return max(base, 1.2)
    wins = {0: [(-2.5, -1.3, 1.0, 2.4), (1.4, 2.6, 1.0, 2.4), (-0.55, 0.55, 0.0, 2.3), (-2.5, -1.3, 4.0, 5.3), (-0.6, 0.6, 4.0, 5.3)],
            1: [(-2.2, -1.0, 1.0, 2.4), (1.0, 2.2, 1.0, 2.4), (1.0, 2.2, 4.0, 5.3)],
            2: [(-0.6, 0.6, 1.0, 2.4), (-0.6, 0.6, 4.0, 5.3)],
            3: [(-1.5, -0.4, 1.0, 2.4), (0.6, 1.7, 1.0, 2.4)]}
    walls = [('x', Y0, -1, X0, X1), ('x', Y1, 1, X0, X1), ('y', X0, -1, Y0, Y1), ('y', X1, 1, Y0, Y1)]
    b = Builder("Ruin_Walls")
    for wi, (axis, plane, out, u0, u1) in enumerate(walls):
        z = 0.0; row = 0
        while z < H:
            h = 0.24 if row % 3 else 0.3
            u = u0 - (0.2 if row % 2 else 0.0)
            while u < u1:
                L = rnd.uniform(0.32, 0.55)
                a0, a1 = max(u, u0 - T / 2 if wi >= 2 else u0), min(u + L, u1 + (T / 2 if wi >= 2 else 0))
                u += L
                if a1 - a0 < 0.06: continue
                cu = (a0 + a1) / 2
                hm = hmax(cu, wi)
                if z + h > hm: continue
                if z + h > hm - 0.6 and rnd.random() < 0.35: continue          # ragged edge
                hole = False
                for (w0, w1, wz0, wz1) in wins[wi]:
                    if a1 > w0 and a0 < w1 and z + h > wz0 and z < wz1: hole = True
                if hole: continue
                mat = m_stone2 if (rnd.random() < 0.3 or z > hm - 1.2) else m_stone
                jit = rnd.uniform(-0.015, 0.015)
                if axis == 'x': b.box(mat, (a1 - a0 - 0.012, T + rnd.uniform(-0.02, 0.03), h - 0.012), (cu, plane + jit, z + h / 2), (rnd.uniform(-0.02, 0.02), 0, rnd.uniform(-0.015, 0.015)))
                else: b.box(mat, (T + rnd.uniform(-0.02, 0.03), a1 - a0 - 0.012, h - 0.012), (plane + jit, cu, z + h / 2), (0, rnd.uniform(-0.02, 0.02), rnd.uniform(-0.015, 0.015)))
            z += h; row += 1
        # mortar core so gaps look filled & interior plaster
        for (cz0, cz1) in ((0, 1.0), (2.4, 4.0)):
            pass
    # lintels & sills (charred timber) for each opening
    for wi, (axis, plane, out, u0, u1) in enumerate(walls):
        for (w0, w1, wz0, wz1) in wins[wi]:
            if wz1 > hmax((w0 + w1) / 2, wi) - 0.2: continue
            if axis == 'x':
                b.box(m_beam, (w1 - w0 + 0.4, T + 0.04, 0.2), ((w0 + w1) / 2, plane, wz1 + 0.1))
                if wz0 > 0.1: b.box(m_stone2, (w1 - w0 + 0.2, T + 0.12, 0.08), ((w0 + w1) / 2, plane + out * 0.04, wz0 - 0.04))
            else:
                b.box(m_beam, (T + 0.04, w1 - w0 + 0.4, 0.2), (plane, (w0 + w1) / 2, wz1 + 0.1))
                if wz0 > 0.1: b.box(m_stone2, (T + 0.12, w1 - w0 + 0.2, 0.08), (plane + out * 0.04, (w0 + w1) / 2, wz0 - 0.04))
    # corner quoins (larger dressed stones)
    for x in (X0, X1):
        for y in (Y0, Y1):
            z = 0
            k = 0
            while z < 5.0:
                hm = min(hmax(x, 2 if x < 0 else 3), hmax(y if False else x, 0 if y < 0 else 1))
                if z + 0.32 > hm: break
                sx, sy = (0.62, 0.42) if k % 2 else (0.42, 0.62)
                b.box(m_stone, (sx, sy, 0.3), (x + (sx / 2 - 0.21) * (-1 if x > 0 else 1), y + (sy / 2 - 0.21) * (-1 if y > 0 else 1), z + 0.16))
                z += 0.32; k += 1
    # interior plaster skin (dark, sooty)
    b.box(m_plaster, (X1 - X0 - 0.5, 0.04, 3.0), (0, Y1 - 0.2, 1.6))
    b.box(m_plaster, (0.04, Y1 - Y0 - 0.5, 2.6), (X0 + 0.2, 0, 1.4))
    # foundation plinth + steps
    b.box(m_stone2, (X1 - X0 + 0.3, Y1 - Y0 + 0.3, 0.25), (0, 0, -0.1))
    for k in range(3):
        b.box(m_stone, (1.6 - k * 0.15, 0.35, 0.16), (0, Y0 - 0.35 - (2 - k) * 0.3, 0.08 + k * 0.0), (0, 0, rnd.uniform(-0.03, 0.03)))
    walls_o = b.build(C, bevel=0.018, seg=2, parent=root)
    displace(walls_o, 0.018, 0.06, 'CLOUDS', 0)

    # ---------------- collapsed floor, beams, rubble
    r = Builder("Ruin_Debris")
    # remaining joists of first floor (some broken & hanging)
    for i in range(10):
        x = X0 + 0.5 + i * 0.7
        if i in (3, 6):
            r.box(m_beam, (0.16, 3.4, 0.24), (x, -0.7, 2.0), (rnd.uniform(0.5, 0.75), 0, rnd.uniform(-0.15, 0.15)))
            continue
        if i > 7: continue
        L = rnd.uniform(2.0, Y1 - Y0 - 0.2)
        r.box(m_beam, (0.16, L, 0.24), (x, Y1 - L / 2 - 0.1, 3.2), (rnd.uniform(-0.05, 0.08), 0, 0))
    # floor boards fragments on joists
    for i in range(30):
        x = rnd.uniform(X0 + 0.4, 1.8); y = rnd.uniform(0.4, Y1 - 0.3)
        r.box(m_beam, (rnd.uniform(0.5, 1.5), 0.14, 0.035), (x, y, 3.35), (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.08, 0.08), rnd.uniform(-0.1, 0.1) + PI / 2 * (i % 2 == 9)))
    # rubble piles: inside, at the collapsed corner and in front
    def pile(cx, cy, rad, hgt, n, seed):
        rr = random.Random(seed)
        for _ in range(n):
            a = rr.uniform(0, math.tau); d = rad * math.sqrt(rr.random())
            zz = hgt * (1 - (d / rad) ** 1.5) * rr.uniform(0.3, 1.0)
            sz = rr.uniform(0.12, 0.38)
            mat = m_stone if rr.random() < 0.6 else (m_stone2 if rr.random() < 0.7 else m_beam)
            if mat is m_beam:
                r.box(mat, (sz * 0.4, rr.uniform(0.6, 1.8), sz * 0.4), (cx + math.cos(a) * d, cy + math.sin(a) * d, zz + 0.05), (rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), rr.uniform(0, PI)))
            else:
                r.box(mat, (sz * rr.uniform(1, 1.6), sz, sz * 0.7), (cx + math.cos(a) * d, cy + math.sin(a) * d, zz + sz * 0.3), (rr.uniform(-0.5, 0.5), rr.uniform(-0.5, 0.5), rr.uniform(0, PI)))
    pile(2.9, -2.6, 1.9, 1.2, 260, 1)
    pile(3.9, 0.5, 1.6, 0.9, 160, 2)
    pile(0.5, 0.4, 2.4, 0.9, 260, 3)
    pile(-2.0, -3.5, 1.0, 0.35, 60, 4)
    r.box(m_ash, (X1 - X0 - 0.4, Y1 - Y0 - 0.4, 0.1), (0, 0, 0.05))
    # ash ground skirt
    r.cyl(m_ash, 5.6, 0.04, (0.4, -0.4, 0.0), seg=48)
    deb = r.build(C, bevel=0.02, seg=1, parent=root)
    displace(deb, 0.03, 0.08, 'CLOUDS', 0)

    fx = collection("A02b_FX", C)
    fire("RF_Win1", fx, (2.0, Y0 + 0.4, 0.6), 0.6, 1.7, 9, 61, power=1500, parent=root)
    fire("RF_Inside", fx, (0.5, 0.4, 0.5), 1.4, 2.4, 14, 62, power=3000, parent=root)
    fire("RF_Back", fx, (-1.6, 1.8, 0.3), 0.7, 1.5, 8, 63, power=1200, parent=root)
    fire("RF_Pile", fx, (2.9, -2.4, 0.6), 0.7, 1.2, 8, 64, power=900, parent=root)
    fire("RF_Beam", fx, (-0.6, -0.7, 2.2), 0.5, 1.1, 6, 65, power=600, parent=root)
    fire("RF_Side", fx, (3.9, 0.5, 0.7), 0.6, 1.0, 7, 66, power=600, parent=root)
    smoke("RS_Main", fx, (0.6, 0.3, 4.0), 8.0, 1.8, 11, 67, density=3.0, color=(0.03, 0.03, 0.03), drift=(0.1, 0.05), parent=root)
    embers("RE_1", fx, (0.6, 0, 2.5), 3.0, 6.0, 180, 68, parent=root)
    for o in C.all_objects:
        if o.type == 'MESH' and not o.get("fx"):
            for pg in o.data.polygons: pg.use_smooth = True
            try: o.data.set_sharp_from_angle(angle=math.radians(30))
            except Exception: pass
    root.location = origin
    mark_asset(root, "Burned-out two-storey stone house ruin: ragged walls, charred lintels and joists, rubble piles, interior fire and smoke.",
               ["ruin", "house", "fire", "destroyed", "disaster"])
    return root, C

root, C = build()
result = {"objects": len(C.all_objects), "polys": sum(len(o.data.polygons) for o in C.all_objects if o.type == 'MESH')}
