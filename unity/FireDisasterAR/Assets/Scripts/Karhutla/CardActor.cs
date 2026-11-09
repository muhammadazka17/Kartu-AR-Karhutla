using System;
using System.Collections;
using UnityEngine;

public abstract class CardActor : MonoBehaviour
{
    protected CardScene scene;
    protected KarhutlaManager mgr;
    public virtual void Init(CardScene s, KarhutlaManager m) { scene = s; mgr = m; }
    public virtual void ResetIdle() { }
    protected static Transform Find(Transform root, string prefix)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name.StartsWith(prefix)) return t;
        return null;
    }
    protected IEnumerator TurnTo(Transform pivot, Vector3 localForward, Vector3 worldTarget, float seconds)
    {
        var up = scene.transform.up;
        var to = Vector3.ProjectOnPlane(worldTarget - pivot.position, up);
        if (to.sqrMagnitude < 1e-8f) yield break;
        var fwd = Vector3.ProjectOnPlane(pivot.TransformDirection(localForward), up);
        var delta = Quaternion.AngleAxis(Vector3.SignedAngle(fwd.normalized, to.normalized, up), up);
        var a = pivot.rotation; var b = delta * pivot.rotation;
        for (float t = 0; t < seconds; t += Time.deltaTime) { pivot.rotation = Quaternion.Slerp(a, b, Mathf.SmoothStep(0, 1, t / seconds)); yield return null; }
        pivot.rotation = b;
    }
    protected void FaceNow(Transform pivot, Vector3 localForward, Vector3 worldTarget)
    {
        var up = scene.transform.up;
        var to = Vector3.ProjectOnPlane(worldTarget - pivot.position, up);
        var fwd = Vector3.ProjectOnPlane(pivot.TransformDirection(localForward), up);
        if (to.sqrMagnitude > 1e-8f && fwd.sqrMagnitude > 1e-8f) pivot.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(fwd.normalized, to.normalized, up), up) * pivot.rotation;
    }
    protected static Gradient Grad(Color a, Color b, float a0 = 1f, float a1 = 0f)
    {
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(a, 0), new GradientColorKey(b, 1) }, new[] { new GradientAlphaKey(a0, 0), new GradientAlphaKey(a0, 0.6f), new GradientAlphaKey(a1, 1) });
        return g;
    }
}

