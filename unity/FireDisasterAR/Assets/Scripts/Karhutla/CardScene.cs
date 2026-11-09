using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public enum CardCategory { Pemicu, Dampak, Mitigasi }

/// Root of one card's AR content. Owns the fire "level" of everything inside it.
public class CardScene : MonoBehaviour
{
    public string cardId;            // reference image name, e.g. card_120
    public CardCategory category;
    public string title;             // e.g. "Pembakaran Lahan"
    [TextArea] public string info;   // short educational text
    public float targetSize = 0.12f; // metres the content should span on the table
    public Transform content;        // child that holds the models (scaled)
    public float startLevel = 1f;

    [HideInInspector] public float level = 1f;
    [HideInInspector] public Material steamMat;
    readonly List<(ParticleSystem ps, float rate)> systems = new List<(ParticleSystem, float)>();
    readonly List<(Light l, float i)> lights = new List<(Light, float)>();
    readonly List<Transform> firePoints = new List<Transform>();
    Coroutine fade;
    bool built;

    public void BuildFX()
    {
        if (built) return; built = true;
        Fit();
        foreach (var f in GetComponentsInChildren<FireFX>(true)) f.Build();
        foreach (var ps in GetComponentsInChildren<ParticleSystem>(true))
        {
            if (ps.GetComponentInParent<Stream>() != null) continue;
            systems.Add((ps, ps.emission.rateOverTimeMultiplier));
        }
        foreach (var l in GetComponentsInChildren<Light>(true)) if (l.type == LightType.Point) lights.Add((l, l.intensity));
        foreach (var t in GetComponentsInChildren<Transform>(true)) if (t.name.StartsWith("FX_fire")) firePoints.Add(t);
        SetLevel(startLevel);
    }

    void Start() { BuildFX(); }

    public void Fit()
    {
        if (!content) return;
        content.localScale = Vector3.one;
        var rs = content.GetComponentsInChildren<MeshRenderer>();
        if (rs.Length == 0) return;
        var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
        var lossy = transform.lossyScale.x;
        float span = Mathf.Max(b.size.x, b.size.z) / Mathf.Max(lossy, 1e-6f);
        content.localScale = Vector3.one * (targetSize / Mathf.Max(span, 0.01f));
    }

    public float ContentScale => content ? content.lossyScale.x : 1f;

    public Vector3 FirePoint
    {
        get
        {
            if (firePoints.Count == 0) return content ? content.position + transform.up * 0.02f : transform.position;
            var p = Vector3.zero; foreach (var t in firePoints) p += t.position;
            return p / firePoints.Count + transform.up * 0.01f;
        }
    }

    public void SetLevel(float v)
    {
        level = Mathf.Clamp01(v);
        foreach (var (ps, rate) in systems)
        {
            if (!ps) continue;
            var em = ps.emission; em.rateOverTimeMultiplier = rate * level;
            if (level > 0.01f && !ps.isPlaying) ps.Play();
        }
        foreach (var (l, i) in lights) if (l) l.intensity = i * level;
    }

    public void FadeTo(float target, float seconds)
    {
        if (fade != null) StopCoroutine(fade);
        fade = StartCoroutine(FadeCo(target, seconds));
    }
    IEnumerator FadeCo(float target, float seconds)
    {
        float a = level;
        for (float t = 0; t < seconds; t += Time.deltaTime) { SetLevel(Mathf.Lerp(a, target, t / seconds)); yield return null; }
        SetLevel(target);
    }

    /// white steam puff where water hits the fire
    public void Steam(float seconds = 4f)
    {
        if (!steamMat) return;
        var go = new GameObject("Steam"); go.transform.SetParent(transform, false);
        go.transform.position = FirePoint;
        var ps = go.AddComponent<ParticleSystem>(); ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var m = ps.main; m.duration = seconds; m.loop = false; m.startLifetime = new ParticleSystem.MinMaxCurve(1.5f, 3f);
        float s = targetSize;
        m.startSpeed = new ParticleSystem.MinMaxCurve(s * 0.2f, s * 0.5f); m.startSize = new ParticleSystem.MinMaxCurve(s * 0.15f, s * 0.35f);
        m.startColor = new Color(0.95f, 0.95f, 0.97f, 0.6f); m.simulationSpace = ParticleSystemSimulationSpace.World;
        var em = ps.emission; em.rateOverTime = 25;
        var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 30; sh.radius = s * 0.25f; sh.rotation = new Vector3(-90, 0, 0);
        var col = ps.colorOverLifetime; col.enabled = true;
        var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
            new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(0.7f, 0.15f), new GradientAlphaKey(0, 1) }); col.color = g;
        var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1, AnimationCurve.Linear(0, 0.6f, 1, 2.2f));
        var r = go.GetComponent<ParticleSystemRenderer>(); r.sharedMaterial = steamMat;
        ps.Play();
        Destroy(go, seconds + 4f);
    }
}
