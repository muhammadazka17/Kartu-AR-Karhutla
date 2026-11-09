using System;
using System.Collections;
using UnityEngine;

/// MITIGASI: fire truck water cannon, or water-bombing helicopter
public class MitigasiActor : CardActor
{
    public enum Kind { Truck, Helicopter }
    public Kind kind;
    Transform nozzle, body, rotorMain, rotorTail, heli; Vector3 localFwd; Vector3 heliHomeLocal; Quaternion bodyHome, heliHomeRot;
    Stream water; ParticleSystem drop;
    bool busy;

    public override void Init(CardScene s, KarhutlaManager m)
    {
        base.Init(s, m);
        float k = s.ContentScale;
        var wg = Grad(new Color(0.8f, 0.92f, 1f), new Color(0.6f, 0.8f, 1f), 0.9f, 0.1f);
        if (kind == Kind.Truck)
        {
            body = s.content.GetChild(0); bodyHome = body.localRotation;
            nozzle = Find(s.content, "NODE_water");
            localFwd = body.InverseTransformDirection(Vector3.ProjectOnPlane(nozzle.position - body.position, s.transform.up));
            water = Stream.Create(transform, "WaterJet", m.waterMat, wg, 0.22f * k, 320, 9.81f * k * 0.35f, 0.55f, true);
            water.source = nozzle;
        }
        else
        {
            heli = s.content.GetChild(0); heliHomeLocal = heli.localPosition; heliHomeRot = heli.localRotation;
            rotorMain = Find(heli, "ROTOR_main"); rotorTail = Find(heli, "ROTOR_tail");
            nozzle = Find(heli, "NODE_water_out");
            var tail = rotorTail ? rotorTail.position : heli.position - heli.right;
            localFwd = heli.InverseTransformDirection(Vector3.ProjectOnPlane(heli.position - tail, s.transform.up));
            var go = new GameObject("WaterDrop"); go.transform.SetParent(nozzle, false);
            go.transform.localRotation = Quaternion.identity;
            drop = go.AddComponent<ParticleSystem>(); drop.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var mm = drop.main; mm.simulationSpace = ParticleSystemSimulationSpace.World; mm.startSpeed = 0.02f;
            mm.startLifetime = 0.9f; mm.startSize = new ParticleSystem.MinMaxCurve(0.18f * k, 0.4f * k); mm.gravityModifier = 0.03f * k / 0.012f;
            mm.maxParticles = 2000; mm.loop = true;
            var sh = drop.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.5f * k;
            var col = drop.colorOverLifetime; col.enabled = true; col.color = wg;
            var sz = drop.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1, AnimationCurve.Linear(0, 0.7f, 1, 1.8f));
            var r = go.GetComponent<ParticleSystemRenderer>(); r.sharedMaterial = m.waterMat; r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.12f; r.lengthScale = 2f;
            var em = drop.emission; em.rateOverTime = 0; drop.Play();
        }
    }

    void Update()
    {
        if (rotorMain) rotorMain.Rotate(Vector3.up, 1100f * Time.deltaTime, Space.Self);
        if (rotorTail) rotorTail.Rotate(Vector3.forward, 1800f * Time.deltaTime, Space.Self);
        if (heli && !busy)
        {
            var home = heliHomeLocal + Vector3.up * Mathf.Sin(Time.time * 1.6f) * 0.25f;   // gentle hover bob (content units)
            heli.localPosition = Vector3.Lerp(heli.localPosition, home, Time.deltaTime * 2f);
            heli.localRotation = Quaternion.Slerp(heli.localRotation, heliHomeRot, Time.deltaTime * 2f);
        }
    }

    public override void ResetIdle()
    {
        StopAllCoroutines(); busy = false;
        if (water) water.Play(false);
        if (drop) { var em = drop.emission; em.rateOverTime = 0; }
        if (body) body.localRotation = bodyHome;
    }

    public void PreviewMitigate(CardScene t)
    {
        if (kind == Kind.Truck) { FaceNow(body, localFwd, t.FirePoint); water.target = t.FirePoint; water.Play(true); water.Aim(); }
        else
        {
            var up = scene.transform.up;
            float clear = Mathf.Max(Vector3.Dot(nozzle.position - scene.transform.position, up), 0.01f);
            FaceNow(heli, localFwd, t.FirePoint);
            heli.position = t.FirePoint + up * clear + (heli.position - nozzle.position);
            var mm = drop.main; mm.gravityModifier = (2f * clear / 0.64f) / 9.81f; mm.startLifetime = 0.85f;
            var em = drop.emission; em.rateOverTime = 1400;
        }
    }

    public IEnumerator Mitigate(CardScene target, Action onHit)
    {
        busy = true;
        if (kind == Kind.Truck)
        {
            yield return TurnTo(body, localFwd, target.FirePoint, 0.8f);
            water.target = target.FirePoint; water.Play(true);
            float t = 0; bool hit = false;
            while (t < 5f) { water.target = target.FirePoint; t += Time.deltaTime; if (!hit && t > 0.9f) { hit = true; onHit?.Invoke(); } yield return null; }
            water.Play(false);
            yield return new WaitForSeconds(0.6f);
            float r = 0; var a = body.localRotation;
            while (r < 1f) { r += Time.deltaTime / 0.8f; body.localRotation = Quaternion.Slerp(a, bodyHome, r); yield return null; }
        }
        else
        {
            // fly over the target, nose first, keeping the cruise height
            var startPos = heli.position; var startRot = heli.rotation;
            var up = scene.transform.up;
            float clear = Mathf.Max(Vector3.Dot(nozzle.position - scene.transform.position, up), 0.01f);
            var mm = drop.main; mm.gravityModifier = (2f * clear / 0.64f) / 9.81f; mm.startLifetime = 0.85f;
            Vector3 dest() => target.FirePoint + up * clear + (heli.position - nozzle.position);
            yield return TurnTo(heli, localFwd, target.FirePoint, 0.7f);
            var rotA = heli.rotation;
            for (float t = 0; t < 2.2f; t += Time.deltaTime)
            {
                float u = Mathf.SmoothStep(0, 1, t / 2.2f);
                heli.position = Vector3.Lerp(startPos, dest(), u);
                var tilt = Quaternion.AngleAxis(Mathf.Sin(u * Mathf.PI) * 12f, heli.TransformDirection(Vector3.Cross(localFwd.normalized, Vector3.up)));
                heli.rotation = tilt * rotA;
                yield return null;
            }
            var em = drop.emission; em.rateOverTime = 1400;
            float tt = 0; bool hit = false;
            while (tt < 3.5f) { heli.position = Vector3.Lerp(heli.position, dest(), Time.deltaTime * 3f); tt += Time.deltaTime; if (!hit && tt > 0.5f) { hit = true; onHit?.Invoke(); } yield return null; }
            em.rateOverTime = 0;
            yield return new WaitForSeconds(0.8f);
            var p0 = heli.position;
            for (float t = 0; t < 2.2f; t += Time.deltaTime)
            {
                float u = Mathf.SmoothStep(0, 1, t / 2.2f);
                heli.position = Vector3.Lerp(p0, heli.parent.TransformPoint(heliHomeLocal), u);
                heli.rotation = Quaternion.Slerp(heli.rotation, heli.parent.rotation * heliHomeRot, u);
                yield return null;
            }
        }
        busy = false;
    }
}
