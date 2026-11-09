import bpy, math, random
from mathutils import Vector, Matrix, Euler
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *
PI = math.pi

def mat_foliage(name, burn=0.5):
    m, nt, out = fa_common._new(name)
    if not nt: return m
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 6; n1.inputs['Detail'].default_value = 6
    g = nt.nodes.new('ShaderNodeValToRGB'); e = g.color_ramp.elements
    e[0].color = (0.008, 0.025, 0.004, 1); e[1].color = (0.05, 0.1, 0.01, 1); x = e.new(0.6); x.color = (0.02, 0.055, 0.006, 1)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 0.8; n2.inputs['Detail'].default_value = 4
    zf = nt.nodes.new('ShaderNodeMapRange'); zf.inputs['From Min'].default_value = 0.0; zf.inputs['From Max'].default_value = 1.0
    zf.inputs['To Min'].default_value = burn; zf.inputs['To Max'].default_value = burn - 0.6
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    bm = nt.nodes.new('ShaderNodeValToRGB'); b = bm.color_ramp.elements
    b[0].position = 0.45; b[0].color = (0, 0, 0, 1); b[1].position = 0.75; b[1].color = (1, 1, 1, 1)
    burnt = nt.nodes.new('ShaderNodeValToRGB'); c = burnt.color_ramp.elements
    c[0].color = (0.008, 0.006, 0.005, 1); c[1].color = (0.12, 0.04, 0.008, 1); c[1].position = 0.5
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    band = nt.nodes.new('ShaderNodeMapRange'); band.inputs['From Min'].default_value = 0.55; band.inputs['From Max'].default_value = 0.68
    band2 = nt.nodes.new('ShaderNodeMapRange'); band2.inputs['From Min'].default_value = 0.85; band2.inputs['From Max'].default_value = 0.68
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    es = nt.nodes.new('ShaderNodeMath'); es.operation = 'MULTIPLY'; es.inputs[1].default_value = 2.5
    p = fa_common.principled(nt, None, 0.6)
    p.inputs['Emission Color'].default_value = (1.0, 0.33, 0.03, 1)
    L(tc.outputs['Object'], n1.inputs['Vector']); L(n1.outputs['Fac'], g.inputs[0])
    L(tc.outputs['Generated'], sep.inputs[0]); L(sep.outputs['Z'], zf.inputs[0])
    L(tc.outputs['Object'], n2.inputs['Vector']); L(n2.outputs['Fac'], add.inputs[0]); L(zf.outputs[0], add.inputs[1])
    L(add.outputs[0], bm.inputs[0]); L(n1.outputs['Fac'], burnt.inputs[0])
    L(bm.outputs[0], mix.inputs['Factor']); L(g.outputs[0], mix.inputs['A']); L(burnt.outputs[0], mix.inputs['B'])
    L(mix.outputs['Result'], p.inputs['Base Color'])
    L(add.outputs[0], band.inputs[0]); L(add.outputs[0], band2.inputs[0]); L(band.outputs[0], mul.inputs[0]); L(band2.outputs[0], mul.inputs[1])
    L(mul.outputs[0], es.inputs[0]); L(es.outputs[0], p.inputs['Emission Strength'])
    L(p.outputs[0], out.inputs[0])
    m.diffuse_color = (0.08, 0.12, 0.02, 1)
    return m

def tree(b, bark, base, height, radius, depth, rnd, tips, lean=0.0, gnarl=0.15, spread=0.6, child_n=(2, 4)):
    def branch(p, d, length, r, lvl):
        pts = [Vector(p)]; radii = [r]
        steps = 7
        for i in range(steps):
            d = (d + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 1.0))) * gnarl).normalized()
            pts.append(pts[-1] + d * length / steps)
            radii.append(r * (1 - 0.55 * (i + 1) / steps))
        b.tube(bark, pts, r, seg=max(6, int(14 * r / radius + 6)), radii=radii)
        if lvl <= 0 or r < 0.012:
            tips.append((pts[-1], d)); return
        for k in range(rnd.randint(*child_n)):
            t = rnd.uniform(0.45, 0.95)
            idx = int(t * steps)
            q = pts[idx]
            axis = d.orthogonal().normalized()
            ang = rnd.uniform(0.45, 0.95) * spread / 0.6
            rot = Matrix.Rotation(rnd.uniform(0, math.tau), 3, d) @ Matrix.Rotation(ang, 3, axis)
            nd = (rot @ d).normalized()
            branch(q, nd, length * rnd.uniform(0.5, 0.72), radii[idx] * rnd.uniform(0.55, 0.7), lvl - 1)
        tips.append((pts[-1], d))
    # root flare
    for k in range(6):
        a = math.tau * k / 6 + rnd.uniform(-0.3, 0.3)
        dvec = Vector((math.cos(a), math.sin(a), 0))
        pts = [Vector(base) + Vector((0, 0, 0.45)), Vector(base) + dvec * 0.35 + Vector((0, 0, 0.12)), Vector(base) + dvec * 0.8 + Vector((0, 0, -0.05))]
        b.tube(bark, pts, radius * 0.5, seg=10, radii=[radius * 0.55, radius * 0.35, radius * 0.08])
    branch(base, Vector((lean, 0, 1)).normalized(), height, radius, depth)

def leaves(b, mat, center, rad, n, rnd, size=0.11):
    for i in range(n):
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 0.8))).normalized() * rad * rnd.random() ** 0.35
        p = Vector(center) + v
        s = size * rnd.uniform(0.7, 1.3)
        pts = [(0, 0), (s * 0.45, s * 0.5), (0, s * 1.3), (-s * 0.45, s * 0.5)]
        b.poly(mat, pts, 0.002, tuple(p), (rnd.uniform(0, PI), rnd.uniform(0, PI), rnd.uniform(0, math.tau)))

def build_tree(C, origin):
    rnd = random.Random(301)
    root = empty("BurningTree", C, (0, 0, 0), 2)
    bark = mat_burning("M_Nat_BarkBurning", (0.09, 0.065, 0.045), burn=0.45, scale=1.2, ember_str=6, bark=True)
    fol = mat_foliage("M_Nat_FoliageBurning", 0.55)
    b = Builder("Tree_Trunk"); tips = []
    tree(b, bark, (0, 0, 0), 3.2, 0.28, 3, rnd, tips, lean=0.05)
    trunk = b.build(C, wn=False, parent=root)
    f = Builder("Tree_Foliage")
    clusters = [t for t in tips if t[0].z > 2.2]
    twig = mat_burning("M_Nat_Twig", (0.08, 0.05, 0.03), burn=0.6, scale=4, ember_str=8, bark=True)
    for p, d in clusters:     # fine twigs inside each leaf cluster
        for k in range(5):
            v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.8))).normalized() * rnd.uniform(0.3, 0.6)
            f.tube(twig, [tuple(p), tuple(p + v * 0.5 + Vector((0, 0, 0.05))), tuple(p + v)], 0.01, 5, radii=[0.012, 0.008, 0.003])
    f.build(C, wn=False, parent=root)
    lv = Builder("Tree_Leaves")
    for p, d in clusters:
        leaves(lv, fol, tuple(p + d * 0.15), 0.62, 320, rnd, 0.05)
    lv.build(C, wn=False, parent=root)
    fx = C
    fire("NF_TreeBase", fx, (0.1, 0.1, 0.0), 0.55, 1.5, 9, 311, power=900, parent=root)
    fire("NF_TreeTrunk", fx, (0.2, -0.1, 1.2), 0.15, 1.3, 5, 312, power=400, parent=root)
    lowest = sorted(clusters, key=lambda t: t[0].z)[:5]
    for i, (p, d) in enumerate(lowest):
        fire(f"NF_Canopy{i}", fx, tuple(p + Vector((0, 0, -0.2))), 0.3, 1.0, 6, 320 + i, light=(i == 0), power=250, parent=root)
    embers("NE_Tree", fx, (0, 0, 1.5), 1.6, 4.5, 120, 330, parent=root)
    smoke("NS_Tree", fx, (0.3, 0, 4.6), 3.5, 0.9, 6, 331, density=1.8, color=(0.05, 0.05, 0.05), drift=(0.2, 0.05), parent=root)
    root.location = origin
    mark_asset(root, "Leafy tree catching fire: procedural branching trunk, burning canopy, flames and embers.", ["tree", "fire", "nature", "forest fire"])
    return root

def build_deadtree(C, origin):
    rnd = random.Random(402)
    root = empty("BurningDeadTree", C, (0, 0, 0), 2)
    bark = mat_burning("M_Nat_BarkCharred", (0.06, 0.045, 0.035), burn=0.8, scale=1.6, ember_str=14, bark=True)
    b = Builder("DeadTree"); tips = []
    tree(b, bark, (0, 0, 0), 2.9, 0.24, 4, rnd, tips, lean=-0.08, gnarl=0.22, spread=0.75, child_n=(2, 3))
    b.build(C, wn=False, parent=root)
    fx = C
    fire("NF_DeadBase", fx, (0, 0, 0.0), 0.7, 1.7, 11, 411, power=1100, parent=root)
    fire("NF_DeadMid", fx, (-0.1, 0.05, 1.3), 0.2, 1.0, 5, 412, power=300, parent=root)
    for i, (p, d) in enumerate(rnd.sample(tips, 5)):
        fire(f"NF_DeadTip{i}", fx, tuple(p), 0.06, 0.5, 3, 420 + i, light=False, parent=root)
    # grass tuft burning at base
    g = Builder("DeadTree_Grass")
    dry = mat_noise("M_Nat_DryGrass", (0.25, 0.18, 0.06), (0.45, 0.35, 0.12), 20, (0.6, 0.85), 0, 0.1)
    burnt = mat_burning("M_Nat_GrassBurnt", (0.2, 0.15, 0.05), burn=0.85, scale=3, ember_str=10, rings=False)
    for i in range(500):
        a = rnd.uniform(0, math.tau); d = 1.4 * math.sqrt(rnd.random())
        h = rnd.uniform(0.15, 0.45); w = 0.012
        mat = burnt if d < 0.9 or rnd.random() < 0.4 else dry
        g.poly(mat, [(-w, 0), (w, 0), (rnd.uniform(-0.08, 0.08), h)], 0.002, (math.cos(a) * d, math.sin(a) * d, 0), (rnd.uniform(-0.3, 0.3), 0, rnd.uniform(0, math.tau)))
    g.build(C, wn=False, parent=root)
    embers("NE_Dead", fx, (0, 0, 1.0), 1.4, 3.5, 100, 430, parent=root)
    smoke("NS_Dead", fx, (0, 0, 2.2), 3.0, 0.8, 6, 431, density=2.0, color=(0.04, 0.04, 0.04), drift=(0.15, 0.1), parent=root)
    root.location = origin
    mark_asset(root, "Dead charred tree burning from the base, glowing bark cracks.", ["tree", "dead", "fire", "charred"])
    return root

def build_brush(C, origin):
    rnd = random.Random(503)
    root = empty("BurningBrush", C, (0, 0, 0), 2)
    dry = mat_noise("M_Nat_DryGrass", (0.25, 0.18, 0.06), (0.45, 0.35, 0.12), 20, (0.6, 0.85), 0, 0.1)
    green = mat_noise("M_Nat_GreenGrass", (0.04, 0.08, 0.01), (0.12, 0.2, 0.03), 15, (0.5, 0.8), 0, 0.1)
    burnt = mat_burning("M_Nat_GrassBurnt", (0.2, 0.15, 0.05), burn=0.85, scale=3, ember_str=10, rings=False)
    twig = mat_burning("M_Nat_Twig", (0.08, 0.05, 0.03), burn=0.6, scale=4, ember_str=8, bark=True)
    fol = mat_foliage("M_Nat_BushLeaves", 0.7)
    g = Builder("Brush_Grass")
    for i in range(1600):
        x = rnd.uniform(-1.8, 1.8); y = rnd.uniform(-1.0, 1.0) * (1 - (x / 2.0) ** 2) ** 0.5
        h = rnd.uniform(0.2, 0.6); w = 0.012
        f = (x + 1.8) / 3.6
        mat = burnt if rnd.random() < f * 0.9 else (dry if rnd.random() < 0.6 else green)
        g.poly(mat, [(-w, 0), (w, 0), (rnd.uniform(-0.12, 0.12), h)], 0.002, (x, y, 0), (rnd.uniform(-0.35, 0.35), 0, rnd.uniform(0, math.tau)))
    g.build(C, wn=False, parent=root)
    bsh = Builder("Brush_Shrubs")
    for k, (cx, cy, s) in enumerate(((-0.9, 0.2, 0.7), (0.4, -0.2, 0.85), (1.2, 0.35, 0.6))):
        tips = []
        tree(bsh, twig, (cx, cy, 0), s * 0.6, 0.035, 2, rnd, tips, gnarl=0.35, spread=0.9, child_n=(3, 4))
        for p, d in tips:
            leaves(bsh, fol, tuple(p), 0.22 * s, 14, rnd, 0.07)
    bsh.build(C, wn=False, parent=root)
    fx = C
    for i, x in enumerate((-0.2, 0.5, 1.2)):
        fire(f"NF_Brush{i}", fx, (x, 0.0, 0.0), 0.55, 1.1 + 0.3 * (i == 1), 10, 510 + i, power=700, parent=root)
    fire("NF_BrushFront", fx, (0.3, -0.6, 0.0), 0.5, 0.6, 8, 515, power=300, parent=root)
    smoke("NS_Brush", fx, (0.7, 0.0, 1.2), 3.2, 0.9, 7, 520, density=2.0, color=(0.06, 0.06, 0.06), drift=(0.25, 0.1), parent=root)
    embers("NE_Brush", fx, (0.6, 0, 0.6), 1.4, 2.5, 90, 521, parent=root)
    root.location = origin
    mark_asset(root, "Patch of dry grass and shrubs on fire; fire front from burnt to unburnt.", ["grass", "bush", "wildfire", "fire"])
    return root

def build_rocks(C, origin):
    rnd = random.Random(604)
    root = empty("RockCluster", C, (0, 0, 0), 1.5)
    rock = mat_burning("M_Nat_Rock", (0.075, 0.07, 0.065), burn=0.25, scale=0.9, ember_str=0.0, rings=False)
    out = []
    for i, (x, y, s) in enumerate(((0, 0, 0.75), (0.85, 0.35, 0.45), (-0.8, 0.25, 0.4), (0.4, -0.65, 0.32), (-0.5, -0.6, 0.25), (1.3, -0.3, 0.22), (-1.25, -0.2, 0.18), (0.95, 0.95, 0.16))):
        b = Builder(f"Rock_{i:02d}")
        b.sphere(rock, 1.0, (0, 0, 0), sub=4)
        o = b.build(C, wn=False, parent=root)
        o.location = (x, y, s * 0.35); o.scale = (s * rnd.uniform(1.0, 1.4), s * rnd.uniform(0.8, 1.1), s * rnd.uniform(0.55, 0.8))
        o.rotation_euler = (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(0, math.tau))
        displace(o, 0.35, 0.6, 'VORONOI', 0)
        displace(o, 0.08, 0.15, 'CLOUDS', 2, 6)
        for p in o.data.polygons: p.use_smooth = True
    root.location = origin
    mark_asset(root, "Cluster of 8 weathered rocks (soot-stained).", ["rock", "stone", "nature"])
    return root

def build_log(C, origin):
    rnd = random.Random(705)
    root = empty("FallenLog", C, (0, 0, 0), 1.5)
    bark = mat_burning("M_Nat_LogBark", (0.1, 0.07, 0.045), burn=0.3, scale=1.4, ember_str=4, bark=True)
    endg = mat_wood("M_Nat_LogEndGrain", (0.35, 0.22, 0.11), 0.85)
    b = Builder("Log")
    L = 3.0; n = 14
    pts = [(-L / 2 + L * i / (n - 1), rnd.uniform(-0.03, 0.03), 0.3 + rnd.uniform(-0.02, 0.02)) for i in range(n)]
    radii = [0.3 * (1 - 0.18 * i / (n - 1)) * rnd.uniform(0.95, 1.05) for i in range(n)]
    b.tube(bark, pts, 0.3, seg=28, radii=radii)
    b.cyl(endg, radii[0] * 0.93, 0.02, (pts[0][0] - 0.005, pts[0][1], pts[0][2]), rot=(0, PI / 2, 0), seg=28)
    b.cyl(endg, radii[-1] * 0.93, 0.02, (pts[-1][0] + 0.005, pts[-1][1], pts[-1][2]), rot=(0, PI / 2, 0), seg=28)
    for k in range(4):   # branch stubs
        x = rnd.uniform(-1.0, 1.2); a = rnd.uniform(-1.2, 1.2)
        base = Vector((x, 0, 0.3)); d = Vector((rnd.uniform(-0.3, 0.3), math.sin(a), math.cos(a))).normalized()
        b.tube(bark, [tuple(base), tuple(base + d * 0.35), tuple(base + d * 0.55)], 0.07, 10, radii=[0.08, 0.06, 0.045])
        b.cyl(endg, 0.04, 0.01, tuple(base + d * 0.555), rot=(math.acos(max(-1, min(1, d.z))), 0, math.atan2(-d.x, d.y) if False else 0), seg=10)
    o = b.build(C, wn=False, parent=root)
    t = bpy.data.textures.new("LogBarkDisp", 'VORONOI'); t.noise_scale = 0.08
    sd = o.modifiers.new("Subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    d = o.modifiers.new("Bark", 'DISPLACE'); d.texture = t; d.strength = 0.025
    for p in o.data.polygons: p.use_smooth = True
    root.location = origin
    mark_asset(root, "Fallen log with bark, end grain, branch stubs.", ["log", "wood", "nature"])
    return root

def build_ground(C, origin):
    rnd = random.Random(806)
    root = empty("BurntGroundEmbers", C, (0, 0, 0), 1.5)
    ash = mat_burning("M_Nat_AshGround", (0.06, 0.055, 0.05), burn=0.7, scale=2.5, ember_str=18, rings=False)
    coal = mat_burning("M_Nat_Charcoal", (0.03, 0.025, 0.02), burn=0.9, scale=5, ember_str=25, rings=False)
    b = Builder("BurntGround"); b.cyl(ash, 1.8, 0.03, (0, 0, 0.015), seg=64)
    g = b.build(C, wn=False, parent=root)
    sd = g.modifiers.new("Subd", 'SUBSURF'); sd.subdivision_type = 'SIMPLE'; sd.levels = 4; sd.render_levels = 5
    t = bpy.data.textures.new("AshDisp", 'CLOUDS'); t.noise_scale = 0.3
    dm = g.modifiers.new("Disp", 'DISPLACE'); dm.texture = t; dm.strength = 0.06
    c = Builder("Charcoal")
    for i in range(140):
        a = rnd.uniform(0, math.tau); d = 1.5 * math.sqrt(rnd.random())
        s = rnd.uniform(0.03, 0.12)
        c.box(coal, (s * rnd.uniform(1, 3), s, s * 0.6), (math.cos(a) * d, math.sin(a) * d, 0.04), (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0, PI)))
    co = c.build(C, bevel=0.01, seg=1, parent=root)
    displace(co, 0.02, 0.05, 'CLOUDS', 1)
    fire("NF_Smoulder", C, (0.2, 0.1, 0.02), 0.6, 0.35, 8, 811, power=200, parent=root)
    embers("NE_Ground", C, (0, 0, 0.05), 1.3, 0.8, 120, 812, parent=root)
    smoke("NS_Ground", C, (0.1, 0, 0.4), 2.2, 0.5, 6, 813, density=1.0, color=(0.15, 0.15, 0.15), drift=(0.2, 0.1), parent=root)
    root.location = origin
    mark_asset(root, "Burnt ground patch with glowing charcoal, smouldering flames and embers.", ["embers", "ash", "fire", "ground"])
    return root

def build_fx_library(C, origin):
    root = empty("FX_Library", C, (0, 0, 0), 2)
    ox = 0.0
    for i, (h, r, n) in enumerate(((0.5, 0.2, 5), (1.0, 0.35, 8), (1.8, 0.55, 11), (3.0, 0.8, 16))):
        fire(f"FX_Fire_{['S','M','L','XL'][i]}", C, (ox, 0, 0), r, h, n, 900 + i, power=200 * h * h * 3, parent=root)
        ox += r * 2 + 1.0
    # line of fire
    for k in range(6):
        fire(f"FX_FireLine_{k}", C, (ox + k * 0.45, 0, 0), 0.25, 0.9, 5, 920 + k, power=200, parent=root)
    ox += 3.6
    # fireball / explosion
    fb = mat_fire("FX_Fireball", 6.0)
    b = Builder("FX_Fireball")
    rnd = random.Random(950)
    cx = ox + 1.2
    for k in range(18):
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 0.6))).normalized() * rnd.uniform(0.2, 0.9)
        b.sphere(fb, rnd.uniform(0.45, 0.8), (v.x, v.y, 2.6 + v.z), sub=3)
    for k in range(8):   # stem
        b.sphere(fb, 0.35 - k * 0.02, (rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 0.3 + k * 0.3), sub=3)
    o = b.build(C, wn=False, parent=root); o.location = (cx, 0, 0); o["fx"] = "fire"
    displace(o, 0.35, 0.35, 'CLOUDS', 2)
    lt = bpy.data.lights.new("FX_Fireball_Glow", 'POINT'); lt.energy = 6000; lt.color = (1, 0.45, 0.1); lt.shadow_soft_size = 1.0
    lo = bpy.data.objects.new("FX_Fireball_Glow", lt); lo.location = (cx, 0, 2.4); C.objects.link(lo); lo.parent = root
    smoke("FX_FireballSmoke", C, (cx, 0, 3.3), 2.5, 1.0, 6, 951, density=2.5, color=(0.04, 0.035, 0.03), drift=(0.05, 0.05), parent=root)
    ox += 3.8
    # smoke columns: light, grey, black, dusty
    for i, (col, dens) in enumerate((((0.6, 0.6, 0.6), 1.5), ((0.25, 0.25, 0.25), 2.0), ((0.03, 0.03, 0.03), 3.0), ((0.35, 0.27, 0.18), 1.8))):
        smoke(f"FX_Smoke_{['White','Grey','Black','Dust'][i]}", C, (ox + i * 2.6, 0, 0.6), 4.5, 0.9, 9, 960 + i, density=dens, color=col, drift=(0.15, 0.0), parent=root)
    root.location = origin
    mark_asset(root, "FX library: flames S/M/L/XL, fire line, fireball, four volumetric smoke columns.", ["fx", "fire", "smoke", "explosion"])
    return root

def build():
    purge(["M_Nat", "FX_"])
    C = collection("A03_NatureFire")
    subs = {}
    for name in ("Tree", "DeadTree", "Brush", "Rocks", "Log", "Ground"):
        subs[name] = collection("A03_" + name, C)
    Y = -18
    roots = [build_tree(subs["Tree"], (-11, Y, 0)), build_deadtree(subs["DeadTree"], (-5, Y, 0)),
             build_brush(subs["Brush"], (1, Y, 0)), build_rocks(subs["Rocks"], (6, Y, 0)),
             build_log(subs["Log"], (10, Y, 0)), build_ground(subs["Ground"], (14.5, Y, 0))]
    F = collection("A04_FX_Library")
    build_fx_library(F, (-12, -28, 0))
    return C

C = build()
result = {"objects": len(C.all_objects) + len(bpy.data.collections["A04_FX_Library"].all_objects)}
