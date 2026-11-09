import bpy, os, math
import importlib, fa_common; importlib.reload(fa_common)
from fa_common import *
OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "renders")

def clean_defaults():
    for n in ("Cube", "Camera", "Light"):
        o = bpy.data.objects.get(n)
        if o: bpy.data.objects.remove(o, do_unlink=True)

def rig(name, cam_loc, target, lens=50, key=None, floor=True, world=0.25, focus=None, floor_loc=(0, 0, 0), light=1.0):
    clean_defaults()
    C = collection("Preview_" + name)
    if floor:
        b = Builder("Floor_" + name)
        b.cyl(mat_noise("M_StudioFloor", (0.025, 0.025, 0.027), (0.05, 0.048, 0.046), 2.0, (0.45, 0.7), 0, 0.05), 30, 0.02, (0, 0, -0.01), seg=64)
        f = b.build(C, wn=False); f.location = floor_loc
    tgt = Vector(target)
    k = key or (tgt + Vector((6, -7, 7)))
    area_light("Key_" + name, C, k, tgt, 2500 * light, 6, (1.0, 0.95, 0.88))
    area_light("Fill_" + name, C, tgt + Vector((-8, -4, 3)), tgt, 700 * light, 8, (0.75, 0.85, 1.0))
    area_light("Rim_" + name, C, tgt + Vector((-3, 9, 6)), tgt, 1800 * light, 5, (1.0, 0.92, 0.85))
    cam = camera("Cam_" + name, C, cam_loc, target, lens)
    bpy.context.scene.camera = cam
    studio_env(world)
    return C

def studio_env(strength=0.25):
    """Dark backdrop for the camera, bright gradient studio for reflections."""
    sc = bpy.context.scene
    w = bpy.data.worlds.get("W_Studio") or bpy.data.worlds.new("W_Studio"); sc.world = w; w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputWorld')
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.03, 0.03, 0.035, 1)
    e[1].position = 1.0; e[1].color = (0.25, 0.28, 0.33, 1)
    x = e.new(0.48); x.color = (0.05, 0.05, 0.055, 1)
    x = e.new(0.53); x.color = (0.9, 0.88, 0.85, 1)
    x = e.new(0.6); x.color = (0.12, 0.12, 0.13, 1)
    x = e.new(0.85); x.color = (0.6, 0.62, 0.66, 1)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -1; mr.inputs['From Max'].default_value = 1
    env = nt.nodes.new('ShaderNodeBackground'); env.inputs[1].default_value = 1.2
    cam = nt.nodes.new('ShaderNodeBackground'); cam.inputs[0].default_value = (0.012, 0.013, 0.017, 1); cam.inputs[1].default_value = 1.0
    lp = nt.nodes.new('ShaderNodeLightPath'); mx = nt.nodes.new('ShaderNodeMixShader')
    L(tc.outputs['Generated'], sep.inputs[0]); L(sep.outputs['Z'], mr.inputs[0]); L(mr.outputs[0], cr.inputs[0])
    L(cr.outputs[0], env.inputs[0]); L(lp.outputs['Is Camera Ray'], mx.inputs[0])
    L(env.outputs[0], mx.inputs[1]); L(cam.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs[0])
    return w

def isolate(show_colls):
    """Only render given top-level collections (and all their children)."""
    def setall(lc, val):
        lc.exclude = val
        for ch in lc.children: setall(ch, val)
    for lc in bpy.context.view_layer.layer_collection.children:
        setall(lc, lc.name not in show_colls)

def render(fname, samples=128, res=(1600, 1000)):
    gpu_render(samples, res)
    import time; t=time.time()
    p = os.path.join(OUT, fname)
    bpy.context.scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    return {'path': p, 'secs': round(time.time()-t,1), 'device': bpy.context.scene.cycles.device}
