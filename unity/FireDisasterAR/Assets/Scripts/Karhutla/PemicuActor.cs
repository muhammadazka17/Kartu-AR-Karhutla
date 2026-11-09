using System;
using System.Collections;
using UnityEngine;

/// PEMICU: flamethrower man (jet) or extreme weather (heat wave from the sun)
public class PemicuActor : CardActor
{
    public enum Kind { Flamethrower, Sun }
    public Kind kind;
    Transform nozzle, aimer, sun, ownTarget; Vector3 localFwd;
    Stream jet;
    Quaternion aimerHome;

    public override void Init(CardScene s, KarhutlaManager m)
    {
        base.Init(s, m);
        float k = s.ContentScale;
        if (kind == Kind.Flamethrower)
        {
            nozzle = Find(s.content, "NODE_jet"); var dir = Find(s.content, "NODE_jetdir");
            aimer = Find(s.content, "Person"); ownTarget = Find(s.content, "TreeTarget");
            if (aimer && nozzle && dir) localFwd = aimer.InverseTransformDirection(dir.position - nozzle.position);
            jet = Stream.Create(transform, "FlameJet", m.fireMat, Grad(new Color(1f, 0.85f, 0.4f), new Color(0.9f, 0.15f, 0.02f), 1f, 0f), 0.35f * k, 260, 0.0f, 0.35f, false);
            jet.source = nozzle;
            if (aimer) aimerHome = aimer.localRotation;
        }
        else
        {
            sun = Find(s.content, "SUN");
            jet = Stream.Create(transform, "HeatWave", m.fireMat, Grad(new Color(1f, 0.9f, 0.5f), new Color(1f, 0.35f, 0.05f), 0.8f, 0f), 0.5f * k, 160, 0.0f, 0.8f, false);
            jet.source = sun;
        }
        ResetIdle();
    }

    public override void ResetIdle()
    {
        if (kind == Kind.Flamethrower)
        {
            if (aimer) aimer.localRotation = aimerHome;
            jet.target = ownTarget ? ownTarget.position : scene.FirePoint; jet.Play(true);   // keeps burning its own tree
        }
        else jet.Play(false);
    }

    void Update()
    {
        if (sun) sun.Rotate(scene.transform.up, 25f * Time.deltaTime, Space.World);
        if (kind == Kind.Flamethrower && jet && !attacking && ownTarget) jet.target = ownTarget.position;
    }

    bool attacking;
    public IEnumerator Attack(CardScene target, float seconds, Action onReach)
    {
        attacking = true;
        if (kind == Kind.Flamethrower && aimer) yield return TurnTo(aimer, localFwd, target.FirePoint, 0.6f);
        jet.target = target.FirePoint; jet.Play(true);
        float t = 0; bool fired = false;
        while (t < seconds)
        {
            jet.target = target.FirePoint; t += Time.deltaTime;
            if (!fired && t > 0.7f) { fired = true; onReach?.Invoke(); }
            yield return null;
        }
        attacking = false;
        if (kind == Kind.Sun) jet.Play(false);
        else if (aimer) { yield return TurnTo(aimer, localFwd, ownTarget ? ownTarget.position : scene.FirePoint, 0.6f); }
    }

    public void StopAll() { attacking = false; if (jet) jet.Play(false); }
    public void PreviewAttack(CardScene t)
    {
        if (kind == Kind.Flamethrower && aimer) FaceNow(aimer, localFwd, t.FirePoint);
        jet.target = t.FirePoint; jet.Play(true); jet.Aim();
    }
}

