using UnityEngine;

/// Spawns animated particle fire / smoke / embers at child nodes named
/// FX_fire_r{cm}_h{cm}, FX_smoke_w{cm}_h{cm}, FX_embers_r{cm}_h{cm} (exported from Blender).
public class FireFX : MonoBehaviour
{
    public Material fireMat, smokeMat, emberMat;
    public bool spawnOnStart = true;
    [Range(0f, 2f)] public float intensity = 1f;

    void Start() { if (spawnOnStart) Build(); }

    public void Build()
    {
        foreach (var t in GetComponentsInChildren<Transform>(true))
        {
            var n = t.name;
            if (!n.StartsWith("FX_") || t.GetComponent<ParticleSystem>() != null) continue;
            var parts = n.Split('_');
            if (parts.Length < 4) continue;
            float a = Parse(parts[2]), b = Parse(parts[3]);
            if (parts[1] == "fire") { Fire(t, Mathf.Max(a, 0.12f), Mathf.Max(b, 0.3f)); }
            else if (parts[1] == "smoke") { Smoke(t, Mathf.Max(a, 0.3f), Mathf.Max(b, 1f)); }
            else if (parts[1] == "embers") { Embers(t, Mathf.Max(a, 0.3f), Mathf.Max(b, 0.5f)); }
            else if (parts[1] == "heat") { Heat(t, Mathf.Max(a, 0.3f), Mathf.Max(b, 0.5f)); }
            else if (parts[1] == "haze") { Haze(t, Mathf.Max(a, 1f), Mathf.Max(b, 1f)); }
        }
    }

    static float Parse(string s)
    {
        int i = 0; while (i < s.Length && !char.IsDigit(s[i])) i++;
        int j = i; while (j < s.Length && char.IsDigit(s[j])) j++;
        return j > i ? int.Parse(s.Substring(i, j - i)) / 100f : 1f;
    }

    ParticleSystem MakePS(Transform parent, string name, Material m)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = ps.main;
        main.scalingMode = ParticleSystemScalingMode.Hierarchy;
        main.simulationSpace = ParticleSystemSimulationSpace.Local;
        main.playOnAwake = true; main.loop = true; main.prewarm = true;
        var r = go.GetComponent<ParticleSystemRenderer>();
        r.sharedMaterial = m; r.renderMode = ParticleSystemRenderMode.Billboard;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
        return ps;
    }

    void Fire(Transform t, float radius, float height)
    {
        // core flames
        var ps = MakePS(t, "Flames", fireMat);
        var main = ps.main;
        float life = Mathf.Clamp(0.45f + height * 0.18f, 0.5f, 1.2f);
        main.startLifetime = new ParticleSystem.MinMaxCurve(life * 0.6f, life);
        main.startSpeed = new ParticleSystem.MinMaxCurve(height * 0.6f / life, height * 1.0f / life);
        main.startSize = new ParticleSystem.MinMaxCurve(radius * 1.1f + height * 0.25f, radius * 1.8f + height * 0.4f);
        main.startRotation = new ParticleSystem.MinMaxCurve(-0.4f, 0.4f);
        main.maxParticles = 400;
        var em = ps.emission; em.rateOverTime = Mathf.Clamp(25f * (radius + height) * intensity, 12f, 160f);
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 4f; sh.radius = radius * 0.8f;
        sh.rotation = new Vector3(-90, 0, 0);
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(new Color(1f, 0.85f, 0.45f), 0f), new GradientColorKey(new Color(1f, 0.5f, 0.1f), 0.35f),
                          new GradientColorKey(new Color(0.9f, 0.18f, 0.03f), 0.75f), new GradientColorKey(new Color(0.3f, 0.05f, 0.02f), 1f) },
                  new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(0.95f, 0.12f), new GradientAlphaKey(0.6f, 0.6f), new GradientAlphaKey(0f, 1f) });
        col.color = g;
        var sz = ps.sizeOverLifetime; sz.enabled = true;
        sz.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0, 0.6f), new Keyframe(0.3f, 1f), new Keyframe(1, 0.15f)));
        var nz = ps.noise; nz.enabled = true; nz.strength = 0.35f * height; nz.frequency = 1.6f; nz.scrollSpeed = 1.2f; nz.octaveCount = 2;
        var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-1.2f, 1.2f);
        ps.Play();

        // glow light (only for bigger fires, to keep mobile cost low)
        if (height > 0.9f)
        {
            var lgo = new GameObject("FireGlow"); lgo.transform.SetParent(t, false);
            lgo.transform.localPosition = new Vector3(0, height * 0.4f, 0);
            var l = lgo.AddComponent<Light>(); l.type = LightType.Point; l.color = new Color(1f, 0.5f, 0.15f);
            l.range = height * 3f * t.lossyScale.x; l.intensity = 2.2f * intensity; l.shadows = LightShadows.None;
            lgo.AddComponent<Flicker>();
        }
    }

    void Smoke(Transform t, float width, float height)
    {
        var ps = MakePS(t, "Smoke", smokeMat);
        var main = ps.main;
        float life = Mathf.Clamp(height * 0.9f, 2.5f, 7f);
        main.startLifetime = new ParticleSystem.MinMaxCurve(life * 0.7f, life);
        main.startSpeed = new ParticleSystem.MinMaxCurve(height / life * 0.7f, height / life * 1.1f);
        main.startSize = new ParticleSystem.MinMaxCurve(width * 0.8f, width * 1.4f);
        main.startRotation = new ParticleSystem.MinMaxCurve(0, Mathf.PI * 2);
        main.startColor = new Color(0.12f, 0.11f, 0.1f, 0.55f);
        main.maxParticles = 220;
        var em = ps.emission; em.rateOverTime = Mathf.Clamp(8f * width * intensity, 4f, 40f);
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 10f; sh.radius = width * 0.35f; sh.rotation = new Vector3(-90, 0, 0);
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(new Color(0.35f, 0.3f, 0.27f), 0f), new GradientColorKey(Color.white, 1f) },
                  new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(0.75f, 0.15f), new GradientAlphaKey(0.4f, 0.65f), new GradientAlphaKey(0f, 1f) });
        col.color = g;
        var sz = ps.sizeOverLifetime; sz.enabled = true;
        sz.size = new ParticleSystem.MinMaxCurve(1f, new AnimationCurve(new Keyframe(0, 0.5f), new Keyframe(1, 2.6f)));
        var vel = ps.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
        vel.x = new ParticleSystem.MinMaxCurve(0.05f, 0.35f); vel.y = new ParticleSystem.MinMaxCurve(0f, 0f); vel.z = new ParticleSystem.MinMaxCurve(-0.1f, 0.1f);
        var nz = ps.noise; nz.enabled = true; nz.strength = 0.3f; nz.frequency = 0.4f; nz.scrollSpeed = 0.3f;
        var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-0.4f, 0.4f);
        ps.GetComponent<ParticleSystemRenderer>().sortingFudge = 10;
        ps.Play();
    }

    void Heat(Transform t, float radius, float height)
    {
        // rising warm shimmer / dust devils over dry ground
        var ps = MakePS(t, "Heat", fireMat);
        var main = ps.main;
        main.startLifetime = new ParticleSystem.MinMaxCurve(1.5f, 3f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(height * 0.2f, height * 0.45f);
        main.startSize = new ParticleSystem.MinMaxCurve(radius * 0.5f, radius * 1.1f);
        main.startColor = new Color(1f, 0.55f, 0.2f, 0.12f); main.maxParticles = 80;
        var em = ps.emission; em.rateOverTime = 10f * intensity;
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 10; sh.radius = radius; sh.rotation = new Vector3(-90, 0, 0);
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(new Color(1f, 0.6f, 0.25f), 0), new GradientColorKey(new Color(1f, 0.8f, 0.5f), 1) },
            new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(0.18f, 0.3f), new GradientAlphaKey(0, 1) }); col.color = g;
        var nz = ps.noise; nz.enabled = true; nz.strength = 0.4f; nz.frequency = 0.8f;
        ps.Play();
    }

    void Haze(Transform t, float width, float height)
    {
        // wide, slow, brownish smog layer (kabut asap)
        var ps = MakePS(t, "Haze", smokeMat);
        var main = ps.main;
        main.startLifetime = new ParticleSystem.MinMaxCurve(8f, 12f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(0.05f, 0.25f);
        main.startSize = new ParticleSystem.MinMaxCurve(width * 0.18f, width * 0.32f);
        main.startRotation = new ParticleSystem.MinMaxCurve(0, Mathf.PI * 2);
        main.startColor = new Color(0.55f, 0.47f, 0.38f, 0.45f); main.maxParticles = 160; main.prewarm = true;
        var em = ps.emission; em.rateOverTime = 14f * intensity;
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(width, height * 0.5f, width * 0.8f);
        sh.position = new Vector3(0, height * 0.35f, 0);
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
            new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(0.55f, 0.25f), new GradientAlphaKey(0.45f, 0.75f), new GradientAlphaKey(0, 1) }); col.color = g;
        var nz = ps.noise; nz.enabled = true; nz.strength = 0.3f; nz.frequency = 0.2f; nz.scrollSpeed = 0.1f;
        var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-0.1f, 0.1f);
        ps.Play();
    }

    void Embers(Transform t, float radius, float height)
    {
        var ps = MakePS(t, "Embers", emberMat);
        var main = ps.main;
        main.startLifetime = new ParticleSystem.MinMaxCurve(1.2f, 2.8f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(height * 0.25f, height * 0.6f);
        main.startSize = new ParticleSystem.MinMaxCurve(0.025f, 0.06f);
        main.startColor = new ParticleSystem.MinMaxGradient(new Color(1f, 0.75f, 0.3f), new Color(1f, 0.35f, 0.05f));
        main.maxParticles = 300;
        var em = ps.emission; em.rateOverTime = Mathf.Clamp(30f * radius * intensity, 10f, 90f);
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 25f; sh.radius = radius * 0.8f; sh.rotation = new Vector3(-90, 0, 0);
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                  new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(0.9f, 0.7f), new GradientAlphaKey(0f, 1f) });
        col.color = g;
        var nz = ps.noise; nz.enabled = true; nz.strength = 0.6f; nz.frequency = 1.5f; nz.scrollSpeed = 1f;
        var r = ps.GetComponent<ParticleSystemRenderer>();
        r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.06f; r.lengthScale = 1.2f;
        ps.Play();
    }
}

public class Flicker : MonoBehaviour
{
    Light l; float baseI; float seed;
    void Awake() { l = GetComponent<Light>(); baseI = l.intensity; seed = Random.value * 100f; }
    void Update() { l.intensity = baseI * (0.75f + 0.5f * Mathf.PerlinNoise(seed, Time.time * 6f)); }
}
