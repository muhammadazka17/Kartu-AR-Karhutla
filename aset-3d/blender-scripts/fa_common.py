"""Fire & Disaster asset pack - shared helpers (Blender 5.2)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler

# ---------------------------------------------------------------- collections
def collection(name, parent=None, clear=True):
    c = bpy.data.collections.get(name)
    if c and clear:
        for o in list(c.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for ch in list(c.children):
            bpy.data.collections.remove(ch)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    _unexclude(c.name)
    return c

def _unexclude(name):
    def find(lc, path):
        if lc.collection.name == name: return path + [lc]
        for ch in lc.children:
            r = find(ch, path + [lc])
            if r: return r
        return None
    path = find(bpy.context.view_layer.layer_collection, [])
    if path:
        for lc in path[1:]: lc.exclude = False

def put(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    return obj

# ---------------------------------------------------------------- materials
def purge(prefixes):
    for m in list(bpy.data.materials):
        if any(m.name.startswith(p) for p in prefixes) and m.users == 0:
            bpy.data.materials.remove(m)
    for m in list(bpy.data.materials):
        if any(m.name.startswith(p) for p in prefixes):
            m.name = m.name + "_old"

def _new(name):
    m = bpy.data.materials.get(name)
    if m:
        return m, None, None
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (900, 0)
    return m, nt, out

def principled(nt, color=None, rough=0.5, metal=0.0, coat=0.0):
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    if color: p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if coat:
        p.inputs['Coat Weight'].default_value = coat
        p.inputs['Coat Roughness'].default_value = 0.04
    return p

def mat_basic(name, color, rough=0.5, metal=0.0, coat=0.0, emit=None, emit_str=0.0):
    m, nt, out = _new(name)
    if not nt: return m
    p = principled(nt, color, rough, metal, coat)
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1)
        p.inputs['Emission Strength'].default_value = emit_str
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*color, 1)
    return m

def mat_paint(name, color, rough=0.28, dirt=0.25):
    """Car paint: clearcoat, subtle grime from ambient occlusion + noise."""
    m, nt, out = _new(name)
    if not nt: return m
    L = nt.links.new
    p = principled(nt, None, rough, 0.0, 1.0)
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.25
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14; nz.inputs['Detail'].default_value = 8
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    cl = nt.nodes.new('ShaderNodeMath'); cl.operation = 'MULTIPLY'; cl.inputs[1].default_value = dirt * 2
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*color, 1)
    mix.inputs['B'].default_value = (0.05, 0.04, 0.03, 1)
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough; rr.inputs['To Max'].default_value = 0.8
    L(ao.outputs['AO'], inv.inputs[1]); L(inv.outputs[0], mul.inputs[0]); L(nz.outputs['Fac'], mul.inputs[1])
    L(mul.outputs[0], cl.inputs[0]); L(cl.outputs[0], mix.inputs['Factor'])
    L(mix.outputs['Result'], p.inputs['Base Color']); L(cl.outputs[0], rr.inputs[0]); L(rr.outputs[0], p.inputs['Roughness'])
    L(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*color, 1)
    return m

def mat_noise(name, c1, c2, scale=8.0, rough=(0.5, 0.8), metal=0.0, bump=0.3, detail=8.0, stretch=None, coat=0.0, voronoi=False):
    m, nt, out = _new(name)
    if not nt: return m
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    if stretch: mp.inputs['Scale'].default_value = stretch
    if voronoi:
        nz = nt.nodes.new('ShaderNodeTexVoronoi'); nz.inputs['Scale'].default_value = scale; fac = nz.outputs['Distance']
    else:
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale
        nz.inputs['Detail'].default_value = detail; nz.inputs['Roughness'].default_value = 0.62; fac = nz.outputs['Fac']
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[1].position = 0.72
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough[0]; rr.inputs['To Max'].default_value = rough[1]
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    p = principled(nt, None, 0.5, metal, coat)
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs[0], nz.inputs['Vector'])
    L(fac, cr.inputs[0]); L(fac, rr.inputs[0]); L(fac, bp.inputs['Height'])
    L(cr.outputs[0], p.inputs['Base Color']); L(rr.outputs[0], p.inputs['Roughness']); L(bp.outputs[0], p.inputs['Normal'])
    L(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*c1, 1)
    return m

def mat_diamond_plate(name="M_DiamondPlate"):
    m, nt, out = _new(name)
    if not nt: return m
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 22; br.inputs['Mortar Size'].default_value = 0.0
    br.inputs['Brick Width'].default_value = 0.5; br.inputs['Row Height'].default_value = 0.25
    br.offset = 0.5
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 60; wv.bands_direction = 'DIAGONAL'
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.75
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 30
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.15; rr.inputs['To Max'].default_value = 0.4
    p = principled(nt, (0.72, 0.73, 0.75), 0.25, 1.0)
    L(tc.outputs['Object'], wv.inputs['Vector']); L(tc.outputs['Object'], nz.inputs['Vector'])
    L(wv.outputs['Fac'], gt.inputs[0]); L(gt.outputs[0], bp.inputs['Height'])
    L(nz.outputs['Fac'], rr.inputs[0]); L(rr.outputs[0], p.inputs['Roughness'])
    L(bp.outputs[0], p.inputs['Normal']); L(p.outputs[0], out.inputs[0])
    nt.nodes.remove(br); nt.nodes.remove(mul)
    m.diffuse_color = (0.7, 0.7, 0.72, 1)
    return m

def _wood_color(nt, base, rings=True, scale=3.0):
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 6, 1) if rings else (8, 1, 1)
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS' if rings else 'BANDS'
    wv.inputs['Scale'].default_value = scale; wv.inputs['Distortion'].default_value = 7; wv.inputs['Detail'].default_value = 4
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MULTIPLY_ADD'; mx.inputs[1].default_value = 0.6
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].color = (*[c * 0.5 for c in base], 1)
    cr.color_ramp.elements[1].color = (*base, 1)
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs[0], wv.inputs['Vector']); L(tc.outputs['Object'], nz.inputs['Vector'])
    L(wv.outputs['Fac'], mx.inputs[0]); L(nz.outputs['Fac'], mx.inputs[2]); L(mx.outputs[0], cr.inputs[0])
    return cr.outputs[0], tc

def mat_wood(name, base=(0.36, 0.22, 0.12), rough=0.72):
    m, nt, out = _new(name)
    if not nt: return m
    col, tc = _wood_color(nt, base)
    p = principled(nt, None, rough)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.2
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(col, p.inputs['Base Color']); nt.links.new(bp.outputs[0], p.inputs['Normal'])
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*base, 1)
    return m

def mat_burning(name, base=(0.36, 0.22, 0.12), burn=0.5, scale=1.2, ember_str=5.0, rings=True, bark=False):
    """Surface partly charred: wood -> black char with glowing ember cracks in the char.
    burn 0..1 controls how much area is charred."""
    m, nt, out = _new(name)
    if not nt: return m
    L = nt.links.new
    if bark:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        bk = nt.nodes.new('ShaderNodeTexVoronoi'); bk.inputs['Scale'].default_value = 9
        mpb = nt.nodes.new('ShaderNodeMapping'); mpb.inputs['Scale'].default_value = (3, 3, 0.6)
        crb = nt.nodes.new('ShaderNodeValToRGB')
        crb.color_ramp.elements[0].color = (*[c * 0.35 for c in base], 1); crb.color_ramp.elements[1].color = (*base, 1)
        L(tc.outputs['Object'], mpb.inputs['Vector']); L(mpb.outputs[0], bk.inputs['Vector']); L(bk.outputs['Distance'], crb.inputs[0])
        col = crb.outputs[0]
    else:
        col, tc = _wood_color(nt, base, rings)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 10
    nz.inputs['Roughness'].default_value = 0.65
    burnr = nt.nodes.new('ShaderNodeValToRGB')
    lo = 0.62 - 0.35 * burn
    burnr.color_ramp.elements[0].position = lo; burnr.color_ramp.elements[1].position = lo + 0.08
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs['Scale'].default_value = 22
    crack = nt.nodes.new('ShaderNodeValToRGB')
    crack.color_ramp.elements[0].position = 0.0; crack.color_ramp.elements[0].color = (1, 1, 1, 1)
    crack.color_ramp.elements[1].position = 0.028; crack.color_ramp.elements[1].color = (0, 0, 0, 1)
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 2.5; nz2.inputs['Detail'].default_value = 6
    flick = nt.nodes.new('ShaderNodeMapRange'); flick.inputs['From Min'].default_value = 0.57; flick.inputs['From Max'].default_value = 0.7
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'
    m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; m3.inputs[1].default_value = ember_str
    char = nt.nodes.new('ShaderNodeTexNoise'); char.inputs['Scale'].default_value = 40
    charc = nt.nodes.new('ShaderNodeValToRGB')
    charc.color_ramp.elements[0].color = (0.008, 0.007, 0.006, 1); charc.color_ramp.elements[1].color = (0.06, 0.05, 0.045, 1)
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    bb = nt.nodes.new('ShaderNodeBlackbody'); bb.inputs[0].default_value = 1350
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.7; rr.inputs['To Max'].default_value = 0.95
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7; bp.invert = True
    p = principled(nt, None, 0.7)
    L(tc.outputs['Object'], nz.inputs['Vector']); L(tc.outputs['Object'], vor.inputs['Vector'])
    L(tc.outputs['Object'], nz2.inputs['Vector']); L(tc.outputs['Object'], char.inputs['Vector'])
    L(nz.outputs['Fac'], burnr.inputs[0]); L(vor.outputs['Distance'], crack.inputs[0])
    L(nz2.outputs['Fac'], flick.inputs[0])
    L(burnr.outputs[0], m1.inputs[0]); L(crack.outputs[0], m1.inputs[1])
    L(m1.outputs[0], m2.inputs[0]); L(flick.outputs[0], m2.inputs[1]); L(m2.outputs[0], m3.inputs[0])
    L(char.outputs['Fac'], charc.inputs[0])
    L(burnr.outputs[0], mix.inputs['Factor']); L(col, mix.inputs['A']); L(charc.outputs[0], mix.inputs['B'])
    L(mix.outputs['Result'], p.inputs['Base Color'])
    L(burnr.outputs[0], rr.inputs[0]); L(rr.outputs[0], p.inputs['Roughness'])
    L(bb.outputs[0], p.inputs['Emission Color']); L(m3.outputs[0], p.inputs['Emission Strength'])
    L(m1.outputs[0], bp.inputs['Height']); L(bp.outputs[0], p.inputs['Normal'])
    L(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*[c * 0.5 for c in base], 1)
    return m

def mat_glass(name, tint=(0.75, 0.82, 0.85), rough=0.02):
    m, nt, out = _new(name)
    if not nt: return m
    p = principled(nt, tint, rough)
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 1.5
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*tint, 0.3)
    return m

def mat_emit(name, color, strength=10.0):
    m, nt, out = _new(name)
    if not nt: return m
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    m.diffuse_color = (*color, 1)
    return m

def mat_lens(name, color, strength=6.0):
    """Light lens: glassy, coloured, with emission (for beacons/tail lights)."""
    m, nt, out = _new(name)
    if not nt: return m
    p = principled(nt, color, 0.08)
    p.inputs['Transmission Weight'].default_value = 0.6
    p.inputs['Emission Color'].default_value = (*color, 1); p.inputs['Emission Strength'].default_value = strength
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*color, 1)
    return m

def mat_fire(name="FX_Fire", strength=3.5):
    """Stylised flame: blackbody-like ramp by height, noise-eroded silhouette (alpha)."""
    m, nt, out = _new(name)
    if not nt: return m
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 5.5
    nz.inputs['Detail'].default_value = 12; nz.inputs['Distortion'].default_value = 1.2
    mz = nt.nodes.new('ShaderNodeMath'); mz.operation = 'MULTIPLY_ADD'; mz.inputs[1].default_value = 0.75
    nzs = nt.nodes.new('ShaderNodeMath'); nzs.operation = 'MULTIPLY'; nzs.inputs[1].default_value = 0.55
    col = nt.nodes.new('ShaderNodeValToRGB'); e = col.color_ramp.elements
    e[0].position = 0.12; e[0].color = (1.0, 0.72, 0.28, 1)
    e[1].position = 0.95; e[1].color = (0.25, 0.02, 0.0, 1)
    x = e.new(0.38); x.color = (1.0, 0.36, 0.03, 1)
    x = e.new(0.7); x.color = (0.7, 0.07, 0.0, 1)
    al = nt.nodes.new('ShaderNodeValToRGB'); a = al.color_ramp.elements
    a[0].position = 0.62; a[0].color = (1, 1, 1, 1); a[1].position = 0.92; a[1].color = (0, 0, 0, 1)
    fr = nt.nodes.new('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.35
    edge = nt.nodes.new('ShaderNodeMath'); edge.operation = 'MULTIPLY_ADD'; edge.inputs[1].default_value = 0.35
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[1].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    L(tc.outputs['Generated'], sep.inputs[0]); L(tc.outputs['Object'], nz.inputs['Vector'])
    L(nz.outputs['Fac'], nzs.inputs[0])
    L(sep.outputs['Z'], mz.inputs[0]); L(nzs.outputs[0], mz.inputs[2])
    L(fr.outputs['Facing'], edge.inputs[0]); L(mz.outputs[0], edge.inputs[2])
    L(mz.outputs[0], col.inputs[0]); L(edge.outputs[0], al.inputs[0])
    L(col.outputs[0], em.inputs[0]); L(al.outputs[0], mx.inputs[0])
    L(tr.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs[0])
    m.diffuse_color = (1.0, 0.45, 0.05, 1)
    return m

def mat_smoke(name="FX_Smoke", density=1.5, color=(0.1, 0.1, 0.1), glow=0.0):
    m, nt, out = _new(name)
    if not nt: return m
    L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 9
    nz.inputs['Roughness'].default_value = 0.6
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    fall = nt.nodes.new('ShaderNodeMapRange'); fall.inputs['From Min'].default_value = 1.0; fall.inputs['From Max'].default_value = 0.2
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    cr = nt.nodes.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.18; cr.inputs['From Max'].default_value = 0.45
    dm = nt.nodes.new('ShaderNodeMath'); dm.operation = 'MULTIPLY'; dm.inputs[1].default_value = density
    vol = nt.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Color'].default_value = (*color, 1)
    vol.inputs['Anisotropy'].default_value = 0.3
    if glow:
        vol.inputs['Emission Color'].default_value = (1.0, 0.35, 0.08, 1)
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        gz = nt.nodes.new('ShaderNodeMapRange'); gz.inputs['From Min'].default_value = 0.0; gz.inputs['From Max'].default_value = -1.0
        gz.inputs['To Max'].default_value = glow
        gm = nt.nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'
        L(tc.outputs['Generated'], sep.inputs[0]); 
        L(tc.outputs['Object'], sep.inputs[0])
        L(sep.outputs['Z'], gz.inputs[0]); L(gz.outputs[0], gm.inputs[0]); L(cr.outputs[0], gm.inputs[1])
        L(gm.outputs[0], vol.inputs['Emission Strength'])
    L(tc.outputs['Object'], nz.inputs['Vector']); L(tc.outputs['Object'], ln.inputs[0])
    L(ln.outputs['Value'], fall.inputs[0]); L(nz.outputs['Fac'], mul.inputs[0]); L(fall.outputs[0], mul.inputs[1])
    L(mul.outputs[0], cr.inputs[0]); L(cr.outputs[0], dm.inputs[0]); L(dm.outputs[0], vol.inputs['Density'])
    L(vol.outputs[0], out.inputs['Volume'])
    m.diffuse_color = (*color, 1)
    return m

# ---------------------------------------------------------------- bmesh batch builder
class Builder:
    """Accumulate many primitives into one mesh with per-part material slots."""
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new(); self.mats = []
    def _slot(self, mat):
        if mat not in self.mats: self.mats.append(mat)
        return self.mats.index(mat)
    def _finish(self, geom_verts, mat, mtx):
        bmesh.ops.transform(self.bm, matrix=mtx, verts=geom_verts)
        idx = self._slot(mat)
        faces = set()
        for v in geom_verts:
            for f in v.link_faces: faces.add(f)
        for f in faces: f.material_index = idx; f.smooth = True
        return geom_verts
    def box(self, mat, size, loc, rot=(0, 0, 0)):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        vs = r['verts']
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
        return self._finish(vs, mat, mtx)
    def cyl(self, mat, r, depth, loc, rot=(0, 0, 0), seg=24, r2=None, cap=True):
        res = bmesh.ops.create_cone(self.bm, cap_ends=cap, cap_tris=False, segments=seg,
                                    radius1=r, radius2=r if r2 is None else r2, depth=depth)
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        return self._finish(res['verts'], mat, mtx)
    def sphere(self, mat, r, loc, scale=(1, 1, 1), sub=2, rot=(0, 0, 0)):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r)
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))
        return self._finish(res['verts'], mat, mtx)
    def uvsphere(self, mat, r, loc, scale=(1, 1, 1), seg=24, rings=12, rot=(0, 0, 0)):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=rings, radius=r)
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))
        return self._finish(res['verts'], mat, mtx)
    def torus(self, mat, R, r, loc, rot=(0, 0, 0), maj=32, mnr=12, arc=math.tau):
        verts = []; rings = []
        closed = arc >= math.tau - 1e-6
        n = maj if closed else maj + 1
        for i in range(n):
            a = arc * i / maj; ring = []
            for j in range(mnr):
                b = math.tau * j / mnr
                ring.append(self.bm.verts.new((math.cos(a) * (R + r * math.cos(b)), math.sin(a) * (R + r * math.cos(b)), r * math.sin(b))))
            rings.append(ring); verts += ring
        for i in range(maj if closed else maj):
            A = rings[i]; B = rings[(i + 1) % n]
            for j in range(mnr):
                self.bm.faces.new((A[j], A[(j + 1) % mnr], B[(j + 1) % mnr], B[j]))
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        return self._finish(verts, mat, mtx)
    def arch(self, mat, R_out, R_in, width, loc, rot=(0, 0, 0), seg=24, a0=0.0, a1=math.pi):
        """Half-ring shell (wheel fender). Axis along local Y, arc in XZ."""
        vs = []; prof = []
        for i in range(seg + 1):
            a = a0 + (a1 - a0) * i / seg
            c, s = math.cos(a), math.sin(a)
            prof.append([(R_out * c, -width / 2, R_out * s), (R_out * c, width / 2, R_out * s),
                         (R_in * c, width / 2, R_in * s), (R_in * c, -width / 2, R_in * s)])
        rows = [[self.bm.verts.new(p) for p in ring] for ring in prof]
        for r in rows: vs += r
        for i in range(seg):
            A, B = rows[i], rows[i + 1]
            for j in range(4):
                self.bm.faces.new((A[j], A[(j + 1) % 4], B[(j + 1) % 4], B[j]))
        self.bm.faces.new(rows[0][::-1]); self.bm.faces.new(rows[-1])
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        return self._finish(vs, mat, mtx)
    def poly(self, mat, pts, thickness, loc=(0, 0, 0), rot=(0, 0, 0)):
        """Extruded planar polygon (pts in XZ plane), thickness along Y."""
        top = [self.bm.verts.new((x, -thickness / 2, z)) for x, z in pts]
        bot = [self.bm.verts.new((x, thickness / 2, z)) for x, z in pts]
        n = len(pts)
        self.bm.faces.new(top); self.bm.faces.new(bot[::-1])
        for i in range(n):
            self.bm.faces.new((top[i], bot[i], bot[(i + 1) % n], top[(i + 1) % n]))
        mtx = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        return self._finish(top + bot, mat, mtx)
    def tube(self, mat, pts, radius, seg=12, radii=None):
        """Sweep a circle along a polyline (pipes, hoses, branches). radii per point optional."""
        rings = []; vs = []
        P = [Vector(p) for p in pts]
        for i, p in enumerate(P):
            t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
            up = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
            u = t.cross(up).normalized(); w = t.cross(u).normalized()
            rr = radii[i] if radii else radius
            ring = [self.bm.verts.new(p + (u * math.cos(math.tau * j / seg) + w * math.sin(math.tau * j / seg)) * rr) for j in range(seg)]
            rings.append(ring); vs += ring
        for i in range(len(rings) - 1):
            A, B = rings[i], rings[i + 1]
            for j in range(seg):
                self.bm.faces.new((A[j], A[(j + 1) % seg], B[(j + 1) % seg], B[j]))
        self.bm.faces.new(rings[0][::-1]); self.bm.faces.new(rings[-1])
        return self._finish(vs, mat, Matrix.Identity(4))
    def build(self, coll, bevel=0.0, seg=2, smooth_angle=30, parent=None, wn=True):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6) if False else None
        self.bm.normal_update()
        self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        o = bpy.data.objects.new(self.name, me); coll.objects.link(o)
        if bevel > 0:
            b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = seg
            b.limit_method = 'ANGLE'; b.angle_limit = math.radians(40); b.use_clamp_overlap = True
        if wn:
            try:
                me.set_sharp_from_angle(angle=math.radians(smooth_angle))
            except Exception:
                pass
        if parent:
            o.parent = parent
        return o

# ---------------------------------------------------------------- object helpers
def empty(name, coll, loc=(0, 0, 0), size=1.0):
    e = bpy.data.objects.new(name, None); e.location = loc; e.empty_display_size = size
    e.empty_display_type = 'PLAIN_AXES'; coll.objects.link(e)
    return e

def displace(o, strength, scale, kind='CLOUDS', subdiv=2, depth=4, coords='LOCAL'):
    if subdiv:
        s = o.modifiers.new("Subd", 'SUBSURF'); s.levels = min(subdiv, 2); s.render_levels = subdiv
    t = bpy.data.textures.new(o.name + "_disp", kind)
    if kind in ('CLOUDS',):
        t.noise_scale = scale; t.noise_depth = depth
    elif kind == 'VORONOI':
        t.noise_scale = scale; t.distance_metric = 'DISTANCE'
    d = o.modifiers.new("Displace" + kind, 'DISPLACE'); d.texture = t; d.strength = strength
    d.texture_coords = coords
    return o

def text_obj(name, body, coll, size, loc, rot, mat, extrude=0.004, font_bold=True):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    o = bpy.data.objects.new(name, cu); o.location = loc; o.rotation_euler = rot
    cu.materials.append(mat); coll.objects.link(o)
    return o

# ---------------------------------------------------------------- FX
def flame(name, coll, loc, h=1.0, r=0.3, seed=0, mat=None, lean=(0, 0)):
    """Tongue-shaped flame: tapered lathe profile, twisted/bent, split tip via displacement."""
    rnd = random.Random(seed)
    b = Builder(name)
    prof = [(0.0, 0.55), (0.12, 0.95), (0.3, 1.0), (0.5, 0.78), (0.7, 0.5), (0.85, 0.26), (1.0, 0.0)]
    pts = [(0, 0, h * z) for z, _ in prof]
    radii = [max(r * w, r * 0.02) for _, w in prof]
    b.tube(mat or mat_fire(), pts, r, seg=18, radii=radii)
    o = b.build(coll, wn=False)
    o.location = loc; o.rotation_euler = (lean[0], lean[1], rnd.uniform(0, math.tau))
    o.scale = (1.0, rnd.uniform(0.55, 0.85), 1.0)
    for p in o.data.polygons: p.use_smooth = True
    sd = o.modifiers.new("Subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    t = bpy.data.textures.new(name + "_n", 'CLOUDS'); t.noise_scale = max(r * 0.8, 0.04); t.noise_depth = 4
    d = o.modifiers.new("Disp", 'DISPLACE'); d.texture = t; d.strength = r * 0.9; d.texture_coords = 'GLOBAL'
    tw = o.modifiers.new("Twist", 'SIMPLE_DEFORM'); tw.deform_method = 'TWIST'; tw.deform_axis = 'Z'
    tw.angle = math.radians(rnd.uniform(-120, 120))
    bd = o.modifiers.new("Bend", 'SIMPLE_DEFORM'); bd.deform_method = 'BEND'; bd.deform_axis = 'Y'
    bd.angle = math.radians(rnd.uniform(-50, 50))
    o.visible_shadow = False
    o["fx"] = "flame"
    return o

def fire(name, coll, center, radius=0.5, height=1.2, count=8, seed=1, light=True, power=None, parent=None,
         mat=None, spread_z=0.0):
    rnd = random.Random(seed); out = []
    for i in range(count):
        a = rnd.uniform(0, math.tau); d = radius * math.sqrt(rnd.random())
        f = 1.0 - 0.45 * d / max(radius, 1e-4)
        h = height * rnd.uniform(0.45, 1.0) * f
        r = h * rnd.uniform(0.11, 0.17)
        p = (center[0] + math.cos(a) * d, center[1] + math.sin(a) * d, center[2] + rnd.uniform(0, spread_z))
        o = flame(f"{name}_{i:02d}", coll, p, h, r, seed * 131 + i, mat,
                  lean=(rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15)))
        if parent: o.parent = parent
        out.append(o)
    if light:
        ld = bpy.data.lights.new(name + "_Glow", 'POINT'); ld.color = (1.0, 0.45, 0.12)
        ld.energy = (power if power else 260 * height * height * max(count, 3) / 7) * 0.45
        ld.shadow_soft_size = max(radius * 0.7, 0.1)
        lo = bpy.data.objects.new(name + "_Glow", ld)
        lo.location = (center[0], center[1], center[2] + height * 0.4); coll.objects.link(lo)
        if parent: lo.parent = parent
        out.append(lo)
    return out

def smoke(name, coll, base, height=4.0, width=1.2, puffs=9, seed=3, density=1.5, color=(0.1, 0.1, 0.1),
          drift=(0.6, 0.2), parent=None, glow=0.0):
    rnd = random.Random(seed)
    m = mat_smoke(f"FX_Smoke_{name}", density, color, glow)
    out = []
    for i in range(puffs):
        t = i / max(puffs - 1, 1)
        r = width * (0.55 + 1.0 * t) * rnd.uniform(0.85, 1.2)
        p = (base[0] + drift[0] * height * t * t + rnd.uniform(-0.25, 0.25) * width,
             base[1] + drift[1] * height * t * t + rnd.uniform(-0.25, 0.25) * width,
             base[2] + height * t)
        b = Builder(f"{name}_{i:02d}"); b.sphere(m, 1.0, (0, 0, 0), sub=3)
        o = b.build(coll, wn=False); o.location = p; o.scale = (r, r, r * rnd.uniform(0.8, 1.0))
        o.rotation_euler = (rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6))
        o.visible_shadow = False
        if parent: o.parent = parent
        out.append(o)
    return out

def embers(name, coll, center, radius=1.0, height=2.0, count=80, seed=5, parent=None, rmin=0.004, rmax=0.012):
    rnd = random.Random(seed); m = mat_emit("FX_Ember", (1.0, 0.42, 0.06), 45)
    b = Builder(name)
    for i in range(count):
        z = height * rnd.random() ** 1.6
        p = (center[0] + rnd.uniform(-radius, radius) * (0.4 + z / max(height, 1e-3)),
             center[1] + rnd.uniform(-radius, radius) * (0.4 + z / max(height, 1e-3)), center[2] + z)
        b.sphere(m, rnd.uniform(rmin, rmax), p, scale=(1, 1, rnd.uniform(1.5, 3.5)), sub=1)
    o = b.build(coll, wn=False); o.visible_shadow = False
    if parent: o.parent = parent
    return o

# ---------------------------------------------------------------- render
def gpu_render(samples=128, res=(1600, 1000)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences
        cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
        for d in cp.devices: d.use = (d.type == 'OPTIX')
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.samples = samples; sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPTIX'
    except Exception: pass
    sc.cycles.max_bounces = 8; sc.cycles.transparent_max_bounces = 24; sc.cycles.volume_bounces = 1
    sc.cycles.volume_step_rate = 1.0
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    try:
        sc.view_settings.view_transform = 'Filmic'
        sc.view_settings.look = 'Filmic - Medium High Contrast'
    except Exception:
        try: sc.view_settings.look = 'Medium High Contrast'
        except Exception: pass
    sc.view_settings.exposure = -0.3
    sc.render.film_transparent = False

def studio_world(strength=0.25, color=(0.02, 0.022, 0.028)):
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get('Background') or w.node_tree.nodes.new('ShaderNodeBackground')
    bg.inputs[0].default_value = (*color, 1); bg.inputs[1].default_value = strength * 4
    return w

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def area_light(name, coll, loc, target, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
    lo = bpy.data.objects.new(name, ld); lo.location = loc; coll.objects.link(lo); look_at(lo, target)
    return lo

def camera(name, coll, loc, target, lens=50):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); c.location = loc; coll.objects.link(c); look_at(c, target)
    return c

def mark_asset(obj, desc, tags):
    try:
        obj.asset_mark(); obj.asset_data.description = desc
        for t in tags: obj.asset_data.tags.new(t, skip_if_exists=True)
        obj.asset_generate_preview()
    except Exception:
        pass
