import bpy, os, math, json
import numpy as np
from mathutils import Vector, Matrix

OUTDIR = os.path.join(os.path.expanduser("~"), "Documents", "Fire_Disaster_Asset_Pack", "AR_Export")
TEX = os.path.join(OUTDIR, "textures")

ASSETS = {
    "truck":    ("FireTruck", 2048, 120000, False),
    "house":    ("BurningWoodHouse", 2048, 70000, False),
    "ruin":     ("BurnedStoneRuin", 2048, 60000, False),
    "tree":     ("BurningTree", 1024, 60000, True),
    "deadtree": ("BurningDeadTree", 1024, 35000, True),
    "brush":    ("BurningBrush", 1024, 40000, True),
    "rocks":    ("RockCluster", 1024, 20000, False),
    "log":      ("FallenLog", 1024, 12000, False),
    "ground":   ("BurntGroundEmbers", 1024, 16000, False),
    "heli":     ("WaterBombHelicopter", 2048, 200000, False),
    "person":   ("FlamethrowerMan", 1024, 200000, False),
    "weather":  ("ExtremeWeather", 2048, 120000, True),
}

def ctx():
    w = bpy.context.window_manager.windows[0]
    a = next(a for a in w.screen.areas if a.type == 'VIEW_3D')
    r = next(r for r in a.regions if r.type == 'WINDOW')
    return w, a, r

def fx_kind(o):
    if o.type == 'LIGHT': return "light" if o.name.endswith("_Glow") else "skip"
    if o.type != 'MESH': return None
    if o.get("fx"): return "flame"
    for m in o.data.materials:
        if m and (m.name.startswith("FX_Smoke")): return "smoke"
        if m and m.name.startswith("FX_Ember"): return "ember"
        if m and m.name.startswith("FX_Fire"): return "flame"
    return None

def ensure_coll():
    c = bpy.data.collections.get("AR_Export")
    if not c:
        c = bpy.data.collections.new("AR_Export"); bpy.context.scene.collection.children.link(c)
    lc = bpy.context.view_layer.layer_collection.children.get("AR_Export"); lc.exclude = False
    return c

def gather(root):
    geo, fx = [], {}
    for o in root.children_recursive:
        if o.type == 'EMPTY': continue
        k = fx_kind(o)
        if k == "skip": continue
        if k is None and o.type == 'MESH': geo.append(o)
        elif k in ("flame", "smoke", "ember", "light"):
            grp = o.name.rsplit("_", 1)[0] if k != "ember" else o.name
            if k == "light": grp = o.name[:-5] if o.name.endswith("_Glow") else o.name
            fx.setdefault(grp, {"kind": None, "objs": [], "light": None})
            if k == "light": fx[grp]["light"] = o
            else: fx[grp]["kind"] = k; fx[grp]["objs"].append(o)
    return geo, fx

def make_ar_mesh(key, root, geo, target_faces):
    C = ensure_coll()
    old = bpy.data.objects.get("AR_" + key)
    if old:
        for ch in list(old.children): bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(old, do_unlink=True)
    # make sure source collections evaluate
    for lc in bpy.context.view_layer.layer_collection.children:
        if not lc.name.startswith("Preview_"):
            def un(l):
                l.exclude = False
                for ch in l.children: un(ch)
            un(lc)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    inv = root.matrix_world.inverted()
    import bmesh
    bm = bmesh.new(); mats = []; ranges = []; parts = [None]
    for o in geo:
        pname = o.get("ar_part")
        if pname and pname not in [p[0] for p in parts[1:]]:
            parts.append((pname, (inv @ o.matrix_world).translation.copy()))
        pidx = [p[0] for p in parts[1:]].index(pname) + 1 if pname else 0
        n0 = len(bm.faces)
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(inv @ o.matrix_world)
        remap = []
        for m in me.materials:
            if m not in mats: mats.append(m)
            remap.append(mats.index(m))
        for p in me.polygons:
            p.material_index = remap[p.material_index] if remap else 0
        bm.from_mesh(me); bpy.data.meshes.remove(me)
        ranges.append((n0, len(bm.faces), pidx))
    me = bpy.data.meshes.new("AR_" + key); bm.to_mesh(me); bm.free()
    at = me.attributes.new("ar_part", 'INT', 'FACE')
    vals = [0] * len(me.polygons)
    for a0, a1, pi in ranges:
        for i in range(a0, a1): vals[i] = pi
    at.data.foreach_set("value", vals)
    # material copies (so originals stay untouched); glass -> dark glossy
    for m in mats:
        mc = m.copy(); mc.name = "BK_" + m.name
        me.materials.append(mc)
    o = bpy.data.objects.new("AR_" + key, me); C.objects.link(o)
    o["parts"] = [[p[0], list(p[1])] for p in parts[1:]]
    o.location = (0, 0, 0)
    for p in me.polygons: p.use_smooth = True
    nf = len(me.polygons)
    if nf > target_faces:
        d = o.modifiers.new("Dec", 'DECIMATE'); d.ratio = target_faces / nf; d.use_collapse_triangulate = True
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); o.modifiers.clear()
        oldme = o.data; o.data = me2; bpy.data.meshes.remove(oldme)
    return o

def uv_unwrap(o):
    w, a, r = ctx()
    bpy.ops.object.select_all(action='DESELECT') if False else None
    for ob in bpy.context.view_layer.objects: ob.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(window=w, area=a, region=r, active_object=o, object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0015, area_weight=0.6, scale_to_bounds=True)
        bpy.ops.object.mode_set(mode='OBJECT')

def new_img(name, res, noncolor):
    im = bpy.data.images.get(name)
    if im: bpy.data.images.remove(im)
    im = bpy.data.images.new(name, res, res, alpha=False, float_buffer=False)
    if noncolor: im.colorspace_settings.name = 'Non-Color'
    return im

def set_target(o, img):
    for m in o.data.materials:
        nt = m.node_tree
        n = nt.nodes.get("BAKE_TARGET") or nt.nodes.new('ShaderNodeTexImage')
        n.name = "BAKE_TARGET"; n.image = img; nt.nodes.active = n; n.select = True

def bake(o, btype, img, **kw):
    set_target(o, img)
    w, a, r = ctx()
    with bpy.context.temp_override(window=w, area=a, region=r, active_object=o, object=o, selected_objects=[o], selected_editable_objects=[o]):
        bpy.ops.object.bake(type=btype, margin=12, margin_type='EXTEND', use_clear=True, **kw)

def metallic_mode(o, on, saved, channel='Metallic'):
    for m in o.data.materials:
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None) or next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out is None: continue
        if on:
            saved[m.name] = [l.from_socket for l in out.inputs['Surface'].links]
            p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            e = nt.nodes.new('ShaderNodeEmission'); e.name = "MET_EMIT"
            if p:
                mi = p.inputs[channel]
                if mi.links: nt.links.new(mi.links[0].from_socket, e.inputs['Color'])
                else:
                    v = mi.default_value
                    e.inputs['Color'].default_value = tuple(v) if hasattr(v, '__len__') else (v, v, v, 1)
            else:
                e.inputs['Color'].default_value = (0, 0, 0, 1)
            nt.links.new(e.outputs[0], out.inputs['Surface'])
        else:
            e = nt.nodes.get("MET_EMIT")
            if e: nt.nodes.remove(e)
            for s in saved.get(m.name, []): nt.links.new(s, out.inputs['Surface'])

def has_metal(o):
    for m in o.data.materials:
        p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p and (p.inputs['Metallic'].links or p.inputs['Metallic'].default_value > 0.05): return True
    return False

def img_max(img):
    a = np.empty(len(img.pixels), dtype=np.float32); img.pixels.foreach_get(a)
    return float(a.reshape(-1, 4)[:, :3].max())

def fill_background(img, value=None):
    a = np.empty(len(img.pixels), np.float32); img.pixels.foreach_get(a); a = a.reshape(-1, 4)
    empty = a[:, :3].max(axis=1) < 1e-4
    if empty.all() or not empty.any(): return
    if value is None: value = a[~empty, :3].mean(axis=0)
    a[empty, :3] = value; a[:, 3] = 1.0
    img.pixels.foreach_set(a.ravel()); img.update()

def save(img, key, kind):
    os.makedirs(TEX, exist_ok=True)
    p = os.path.join(TEX, f"{key}_{kind}.jpg")
    img.filepath_raw = p; img.file_format = 'JPEG'
    bpy.context.scene.render.image_settings.quality = 90
    img.save()
    return p

def glassify(o):
    for m in o.data.materials:
        p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p and p.inputs['Transmission Weight'].default_value > 0.5 and "Lens" not in m.name and "Beacon" not in m.name:
            p.inputs['Transmission Weight'].default_value = 0.0
            p.inputs['Base Color'].default_value = (0.015, 0.018, 0.02, 1)
            p.inputs['Roughness'].default_value = 0.05

def baked_material(key, imgs, double):
    name = "AR_" + key
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes.get('Principled BSDF'); L = nt.links.new
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = imgs["basecolor"]; L(t.outputs[0], p.inputs['Base Color'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = imgs["roughness"]; L(t.outputs[0], p.inputs['Roughness'])
    if "metallic" in imgs:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = imgs["metallic"]; L(t.outputs[0], p.inputs['Metallic'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = imgs["normal"]
    nm = nt.nodes.new('ShaderNodeNormalMap'); L(t.outputs[0], nm.inputs['Color']); L(nm.outputs[0], p.inputs['Normal'])
    if "emission" in imgs:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = imgs["emission"]; L(t.outputs[0], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = 2.0
    m.use_backface_culling = not double
    return m

def fx_empties(key, o, root, fx):
    inv = root.matrix_world.inverted(); meta = []
    for grp, d in fx.items():
        objs = d["objs"]
        if not objs and d["light"] is None: continue
        kind = d["kind"] or "flame"
        if objs:
            pts = [inv @ ob.matrix_world.translation for ob in objs]
        else:
            pts = [inv @ d["light"].matrix_world.translation]
        cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
        zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)
        if kind == "flame":
            r = max([math.hypot(p.x - cx, p.y - cy) for p in pts] + [0.1])
            h = max(ob.dimensions.z for ob in objs) if objs else 1.0
            nm = f"FX_fire_r{int(r*100)}_h{int(h*100)}"
            loc = (cx, cy, zmin)
        elif kind == "smoke":
            w = max(max(ob.scale) for ob in objs)
            nm = f"FX_smoke_w{int(w*100)}_h{int((zmax - zmin)*100)}"
            loc = (pts[0].x, pts[0].y, zmin)
        else:
            bb = [ob.matrix_world @ Vector(c) for ob in objs for c in ob.bound_box]
            bb = [inv @ v for v in bb]
            xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
            r = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
            nm = f"FX_embers_r{int(r*100)}_h{int((max(zs)-min(zs))*100)}"
            loc = ((max(xs)+min(xs))/2, (max(ys)+min(ys))/2, min(zs))
        e = bpy.data.objects.new(nm, None); e.location = loc; e.empty_display_size = 0.3
        o.users_collection[0].objects.link(e); e.parent = o
        meta.append({"name": nm, "group": grp, "loc": [round(v, 3) for v in loc]})
    return meta

def split_parts(o):
    import bmesh
    parts = o.get("parts") or []
    for i, (pname, piv) in enumerate(parts, start=1):
        piv = Vector(piv)
        me = o.data.copy(); me.name = pname
        bm = bmesh.new(); bm.from_mesh(me)
        lay = bm.faces.layers.int.get("ar_part")
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != i], context='FACES')
        bmesh.ops.translate(bm, vec=-piv, verts=bm.verts)
        bm.to_mesh(me); bm.free()
        po = bpy.data.objects.new(pname, me); o.users_collection[0].objects.link(po)
        po.parent = o; po.location = piv
    if parts:
        bm = bmesh.new(); bm.from_mesh(o.data); lay = bm.faces.layers.int.get("ar_part")
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != 0], context='FACES')
        bm.to_mesh(o.data); bm.free()

def copy_nodes(o, root):
    inv = root.matrix_world.inverted()
    for e in root.children_recursive:
        if e.type == 'EMPTY' and (e.name.startswith("NODE_") or e.name.startswith("FX_")):
            n = bpy.data.objects.new(e.name.split(".")[0], None); n.empty_display_size = 0.2
            n.location = (inv @ e.matrix_world).translation
            o.users_collection[0].objects.link(n); n.parent = o

def export_asset(key):
    import time; t0 = time.time()
    rname, res, target, double = ASSETS[key]
    root = bpy.data.objects[rname]
    geo, fx = gather(root)
    o = make_ar_mesh(key, root, geo, target)
    glassify(o)
    for lc in bpy.context.view_layer.layer_collection.children:
        lc.exclude = lc.name != "AR_Export"
    for ob in o.users_collection[0].objects:
        ob.hide_render = ob is not o and ob.parent is not o and ob.type == 'MESH'
    o.hide_render = False
    uv_unwrap(o)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.use_denoising = False
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
        for dv in cp.devices: dv.use = dv.type == 'OPTIX'
        sc.cycles.device = 'GPU'
    except Exception: pass
    imgs = {}
    imgs["basecolor"] = new_img(f"{key}_basecolor", res, False)
    saved = {}; metallic_mode(o, True, saved, 'Base Color'); bake(o, 'EMIT', imgs["basecolor"]); metallic_mode(o, False, saved)
    imgs["roughness"] = new_img(f"{key}_roughness", res, True); bake(o, 'ROUGHNESS', imgs["roughness"])
    imgs["normal"] = new_img(f"{key}_normal", res, True); bake(o, 'NORMAL', imgs["normal"], normal_space='TANGENT')
    em = new_img(f"{key}_emission", res, False); bake(o, 'EMIT', em)
    if img_max(em) > 0.02: imgs["emission"] = em
    else: bpy.data.images.remove(em)
    if has_metal(o):
        saved = {}; metallic_mode(o, True, saved)
        imgs["metallic"] = new_img(f"{key}_metallic", res, True); bake(o, 'EMIT', imgs["metallic"])
        metallic_mode(o, False, saved)
        if img_max(imgs["metallic"]) < 0.02: bpy.data.images.remove(imgs.pop("metallic"))
    fill_background(imgs["basecolor"]); fill_background(imgs["roughness"])
    fill_background(imgs["normal"], (0.5, 0.5, 1.0))
    for k, im in imgs.items(): save(im, key, k)
    # swap to single baked material
    bm = baked_material(key, imgs, double)
    old = [m for m in o.data.materials]
    o.data.materials.clear(); o.data.materials.append(bm)
    for p in o.data.polygons: p.material_index = 0
    for m in old:
        if m and m.users == 0: bpy.data.materials.remove(m)
    split_parts(o)
    copy_nodes(o, root)
    meta = fx_empties(key, o, root, fx)
    # export GLB
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, f"{key}.glb")
    w, a, r = ctx()
    for ob in bpy.context.view_layer.objects: ob.select_set(False)
    sel = [o] + list(o.children)
    for ob in sel: ob.select_set(True)
    bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(window=w, area=a, region=r, active_object=o, selected_objects=sel):
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                                  export_apply=False, export_image_format='AUTO', export_lights=False, export_cameras=False)
    info = {"key": key, "faces": len(o.data.polygons), "maps": list(imgs.keys()), "fx": meta,
            "glb_mb": round(os.path.getsize(path) / 1e6, 2), "secs": round(time.time() - t0, 1)}
    with open(os.path.join(OUTDIR, f"{key}.json"), "w") as f: json.dump(info, f, indent=1)
    return info
