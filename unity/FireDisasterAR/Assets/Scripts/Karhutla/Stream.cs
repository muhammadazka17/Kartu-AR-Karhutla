using UnityEngine;

/// A ballistic particle stream from a source transform to a world-space target (water jet, flame jet, heat wave).
public class Stream : MonoBehaviour
{
    public Transform source;
    public Vector3 target;
    public float flightTime = 0.6f;
    public float gravity = 0.6f;      // m/s^2 in world space (already scaled for table-top)
    public float size = 0.006f;
    public float rate = 220f;
    public Gradient color;
    public bool stretch = true;
    ParticleSystem ps;

    public static Stream Create(Transform parent, string name, Material mat, Gradient g, float size, float rate, float gravity, float flight, bool stretch = true)
    {
        var go = new GameObject(name); go.transform.SetParent(parent, false);
        var s = go.AddComponent<Stream>(); s.color = g; s.size = size; s.rate = rate; s.gravity = gravity; s.flightTime = flight; s.stretch = stretch;
        s.ps = go.AddComponent<ParticleSystem>(); s.ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var m = s.ps.main; m.simulationSpace = ParticleSystemSimulationSpace.World; m.loop = true; m.playOnAwake = false;
        m.startSize = new ParticleSystem.MinMaxCurve(size * 0.6f, size * 1.4f); m.maxParticles = 1500;
        var sh = s.ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 2.5f; sh.radius = size * 0.3f;
        var col = s.ps.colorOverLifetime; col.enabled = true; col.color = g;
        var sz = s.ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1, AnimationCurve.Linear(0, 0.7f, 1, 2.0f));
        var nz = s.ps.noise; nz.enabled = true; nz.strength = size * 2f; nz.frequency = 2f;
        var r = go.GetComponent<ParticleSystemRenderer>(); r.sharedMaterial = mat;
        if (stretch) { r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.08f; r.lengthScale = 1.5f; }
        var em = s.ps.emission; em.rateOverTime = 0;
        return s;
    }

    public void Play(bool on)
    {
        if (!ps) ps = GetComponent<ParticleSystem>();
        var em = ps.emission; em.rateOverTime = on ? rate : 0;
        if (on && !ps.isPlaying) ps.Play();
    }

    void LateUpdate() { Aim(); }

    public void Aim()
    {
        if (!ps || !source) return;
        transform.position = source.position;
        var d = target - source.position;
        float T = Mathf.Clamp(flightTime * Mathf.Sqrt(d.magnitude / 0.15f), 0.25f, 1.6f);
        var g = new Vector3(0, -gravity, 0);
        var v = (d - 0.5f * g * T * T) / T;
        if (v.sqrMagnitude < 1e-8f) return;
        transform.rotation = Quaternion.LookRotation(v.normalized);
        var m = ps.main; m.startSpeed = v.magnitude; m.startLifetime = T * 1.02f; m.gravityModifier = gravity / 9.81f;
    }
}
