import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *
PI = math.pi

def tree(b, bark, base, height, radius, depth, rnd, tips, lean=0.0, gnarl=0.2, spread=0.75, child_n=(2, 3)):
    def branch(p, d, length, r, lvl):
        pts = [Vector(p)]; radii = [r]; steps = 7
        for i in range(steps):
            d = (d + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 1.0))) * gnarl).normalized()
            pts.append(pts[-1] + d * length / steps); radii.append(r * (1 - 0.55 * (i + 1) / steps))
        b.tube(bark, pts, r, seg=max(6, int(14 * r / radius + 6)), radii=radii)
        if lvl <= 0 or r < 0.01: tips.append((pts[-1], d)); return
        for k in range(rnd.randint(*child_n)):
            idx = int(rnd.uniform(0.45, 0.95) * steps)
            axis = d.orthogonal().normalized()
            rot = Matrix.Rotation(rnd.uniform(0, math.tau), 3, d) @ Matrix.Rotation(rnd.uniform(0.45, 0.95) * spread / 0.6, 3, axis)
            branch(pts[idx], (rot @ d).normalized(), length * rnd.uniform(0.5, 0.72), radii[idx] * rnd.uniform(0.55, 0.7), lvl - 1)
    for k in range(5):
        a = math.tau * k / 5 + rnd.uniform(-0.3, 0.3); dv = Vector((math.cos(a), math.sin(a), 0))
        b.tube(bark, [Vector(base) + Vector((0, 0, 0.4)), Vector(base) + dv * 0.3 + Vector((0, 0, 0.1)), Vector(base) + dv * 0.7 + Vector((0, 0, -0.04))],
               radius * 0.5, seg=10, radii=[radius * 0.55, radius * 0.35, radius * 0.06])
    branch(base, Vector((lean, 0, 1)).normalized(), height, radius, depth)

def build(origin=(16, -40, 0)):
    purge(["M_Wx"])
    rnd = random.Random(1201)
    C = collection("A07_ExtremeWeather")
    root = empty("ExtremeWeather", C, (0, 0, 0), 2)
    # --- cracked earth material: plates + dark crack lines + pale dusty tops
    m, nt, out = fa_common._new("M_Wx_CrackedSoil")
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 3.2
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.03, 0.02, 0.012, 1); e[1].position = 0.12; e[1].color = (0.42, 0.3, 0.17, 1)
    x = e.new(0.04); x.color = (0.16, 0.1, 0.05, 1)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 7; nz.inputs['Detail'].default_value = 10
    dust = nt.nodes.new('ShaderNodeMix'); dust.data_type = 'RGBA'; dust.inputs['B'].default_value = (0.62, 0.5, 0.34, 1)
    dm = nt.nodes.new('ShaderNodeMapRange'); dm.inputs['From Min'].default_value = 0.45; dm.inputs['From Max'].default_value = 0.75; dm.inputs['To Max'].default_value = 0.7
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.8
    p = fa_common.principled(nt, None, 0.95)
    L(tc.outputs['Object'], vor.inputs['Vector']); L(tc.outputs['Object'], nz.inputs['Vector'])
    L(vor.outputs['Distance'], cr.inputs[0]); L(nz.outputs['Fac'], dm.inputs[0])
    L(dm.outputs[0], dust.inputs['Factor']); L(cr.outputs[0], dust.inputs['A']); L(dust.outputs['Result'], p.inputs['Base Color'])
    L(vor.outputs['Distance'], bp.inputs['Height']); L(bp.outputs[0], p.inputs['Normal']); L(p.outputs[0], out.inputs[0])
    soil = m
    grass_dry = mat_noise("M_Wx_DryGrass", (0.42, 0.32, 0.12), (0.62, 0.5, 0.22), 25, (0.6, 0.85), 0, 0.1)
    grass_dead = mat_noise("M_Wx_DeadGrass", (0.18, 0.12, 0.06), (0.3, 0.22, 0.1), 25, (0.7, 0.9), 0, 0.1)
    bark = mat_noise("M_Wx_DryBark", (0.12, 0.09, 0.07), (0.32, 0.26, 0.2), 6, (0.7, 0.95), 0, 0.5, stretch=(3, 3, 0.5), voronoi=True)
    rock = mat_noise("M_Wx_Rock", (0.2, 0.16, 0.12), (0.42, 0.35, 0.27), 5, (0.7, 0.95), 0, 0.6, voronoi=True)
    sun_core = mat_emit("M_Wx_SunCore", (1.0, 0.72, 0.25), 9)
    sun_ray = mat_emit("M_Wx_SunRay", (1.0, 0.42, 0.04), 6)

    # --- ground with real crack geometry (voronoi F2-F1 displacement)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=220, y_segments=220, size=3.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.xy.length > 2.95], context='VERTS')
    for v in bm.verts:
        r = v.co.xy.length
        v.co.z = 0.04 * max(0, 1 - (r / 2.95) ** 6) - 0.02 * (r / 2.95) ** 4
    me = bpy.data.meshes.new("Wx_Ground"); bm.to_mesh(me); bm.free()
    me.materials.append(soil)
    g = bpy.data.objects.new("Wx_Ground", me); C.objects.link(g); g.parent = root
    t = bpy.data.textures.new("Wx_Cracks", 'VORONOI'); t.noise_scale = 0.32
    t.weight_1 = -1.0; t.weight_2 = 1.0; t.noise_intensity = 2.0; t.distance_metric = 'DISTANCE'
    d = g.modifiers.new("Cracks", 'DISPLACE'); d.texture = t; d.strength = 0.045; d.mid_level = 0.0; d.texture_coords = 'LOCAL'
    t2 = bpy.data.textures.new("Wx_Undulate", 'CLOUDS'); t2.noise_scale = 1.2
    d2 = g.modifiers.new("Undulate", 'DISPLACE'); d2.texture = t2; d2.strength = 0.08; d2.texture_coords = 'LOCAL'
    for pg in me.polygons: pg.use_smooth = True
    # rim skirt so the disc reads as a slab of earth
    b = Builder("Wx_Skirt"); b.cyl(soil, 2.97, 0.25, (0, 0, -0.1), seg=96, r2=3.05)
    b.build(C, parent=root, wn=False)

    # --- dead trees, dry shrubs, grass tufts, rocks
    v = Builder("Wx_Vegetation"); tips = []
    tree(v, bark, (-1.3, 0.6, 0), 2.6, 0.2, 4, rnd, tips, lean=0.06)
    tree(v, bark, (1.5, -0.9, 0), 1.9, 0.15, 3, rnd, tips, lean=-0.1)
    tree(v, bark, (0.9, 1.6, 0), 1.3, 0.1, 3, rnd, tips, lean=0.1)
    for (cx, cy) in ((-0.2, -1.5), (1.9, 0.8), (-2.1, -0.6), (0.3, 0.3)):
        tree(v, bark, (cx, cy, 0), 0.45, 0.025, 2, rnd, tips, gnarl=0.4, spread=1.0, child_n=(3, 4))
    for c in range(46):
        a = rnd.uniform(0, math.tau); dd = 2.7 * math.sqrt(rnd.random()); cx, cy = math.cos(a) * dd, math.sin(a) * dd
        for i in range(rnd.randint(12, 26)):
            h = rnd.uniform(0.1, 0.32); w = 0.009
            mt = grass_dry if rnd.random() < 0.7 else grass_dead
            v.poly(mt, [(-w, 0), (w, 0), (rnd.uniform(-0.1, 0.1), h)], 0.002, (cx + rnd.gauss(0, 0.06), cy + rnd.gauss(0, 0.06), 0.02),
                   (rnd.uniform(-0.5, 0.5), 0, rnd.uniform(0, math.tau)))
    for i in range(9):
        a = rnd.uniform(0, math.tau); dd = rnd.uniform(0.8, 2.6); s = rnd.uniform(0.08, 0.3)
        v.sphere(rock, s, (math.cos(a) * dd, math.sin(a) * dd, s * 0.25), scale=(1.3, 1.0, 0.6), sub=2, rot=(0, 0, rnd.uniform(0, 6)))
    veg = v.build(C, parent=root, wn=False)
    for pg in veg.data.polygons: pg.use_smooth = True

    # --- blazing sun (separate part so it can slowly spin)
    s = Builder("SUN")
    s.sphere(sun_core, 0.42, (0, 0, 0), sub=3)
    for k in range(24):
        a = math.tau * k / 24; L_ = 0.55 if k % 2 else 0.95
        dv = Vector((math.cos(a), 0, math.sin(a)))
        s.cyl(sun_ray, 0.07 if k % 2 else 0.1, L_, tuple(dv * (0.45 + L_ / 2)), rot=(0, math.atan2(dv.x, dv.z), 0), seg=8, r2=0.0)
    for k in range(12):   # rays in the other plane so it reads from any side
        a = math.tau * k / 12 + 0.26; dv = Vector((0, math.cos(a), math.sin(a)))
        s.cyl(sun_ray, 0.08, 0.7, tuple(dv * 0.8), rot=(-math.atan2(dv.y, dv.z), 0, 0), seg=8, r2=0.0)
    sun = s.build(C, parent=root, wn=False); sun.location = (0.4, 0.2, 4.3); sun["ar_part"] = "SUN"
    sl = bpy.data.lights.new("Wx_SunLight", 'SUN'); sl.energy = 4; sl.color = (1, 0.85, 0.6)
    lo = bpy.data.objects.new("Wx_SunLight", sl); lo.rotation_euler = (0.5, 0.2, 0.3); C.objects.link(lo); lo.parent = root

    # --- AR effect anchors (heat shimmer, smoulder, small fires that the heat ignites)
    for i, (x, y) in enumerate(((0.3, 0.3), (-0.2, -1.5), (1.9, 0.8), (-2.1, -0.6))):
        e = empty(f"FX_fire_r{20 + 5 * i}_h{45 + 10 * i}", C, (x, y, 0.02), 0.2); e.parent = root
    for i, (x, y) in enumerate(((0.0, 0.0), (-1.4, 1.0), (1.4, -1.0))):
        e = empty(f"FX_heat_r{90}_h{120}", C, (x, y, 0.05), 0.2); e.parent = root
    e = empty("FX_smoke_w40_h250", C, (0.3, 0.3, 0.3), 0.2); e.parent = root
    root.location = origin
    mark_asset(root, "Extreme heat / drought scene: cracked earth, dry dead trees and grass, blazing sun.", ["drought", "el nino", "heat", "trigger"])
    return root, C

root, C = build()
result = {"objs": len(C.objects)}
