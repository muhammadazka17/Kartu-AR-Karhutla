using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using Vuforia;
using Image = UnityEngine.UI.Image;

/// Vuforia version: 6 cards are turned into instant Image Targets from their pictures at startup,
/// then the Pemicu -> Dampak -> Mitigasi interactions are played depending on which cards are in view.
public class KarhutlaManager : MonoBehaviour
{
    [System.Serializable] public class CardEntry { public string id; public Texture2D image; public GameObject prefab; }
    public List<CardEntry> cards = new List<CardEntry>();
    public float cardWidth = 0.063f;
    public Material fireMat, waterMat, steamMat;
    public Text status, caption, stageTitle, detected;
    public Image captionPanel;

    readonly Dictionary<string, ImageTargetBehaviour> targets = new Dictionary<string, ImageTargetBehaviour>();
    readonly Dictionary<string, CardScene> spawned = new Dictionary<string, CardScene>();
    readonly Dictionary<string, float> lastSeen = new Dictionary<string, float>();
    string combo = "";
    Coroutine seq;
    CardScene P, D, M;
    string initError;

    static readonly Color cP = new Color(0.85f, 0.25f, 0.05f, 0.92f), cD = new Color(0.45f, 0.12f, 0.1f, 0.92f), cM = new Color(0.08f, 0.4f, 0.65f, 0.92f), cN = new Color(0, 0, 0, 0.7f), cOK = new Color(0.1f, 0.45f, 0.2f, 0.92f);

    void Start()
    {
        Application.targetFrameRate = 60; Screen.sleepTimeout = SleepTimeout.NeverSleep;
        Caption("", "Menyiapkan kamera AR...", cN);
        VuforiaApplication.Instance.OnVuforiaInitialized += OnInit;
        if (VuforiaApplication.Instance.IsRunning) CreateTargets();
        else VuforiaApplication.Instance.OnVuforiaStarted += CreateTargets;
    }

    void OnDestroy()
    {
        if (VuforiaApplication.Instance == null) return;
        VuforiaApplication.Instance.OnVuforiaStarted -= CreateTargets;
        VuforiaApplication.Instance.OnVuforiaInitialized -= OnInit;
    }

    void OnInit(VuforiaInitError err)
    {
        if (err == VuforiaInitError.NONE) return;
        initError = err.ToString();
        string msg = err switch
        {
            VuforiaInitError.PERMISSION_ERROR => "Izin kamera ditolak. Aktifkan izin Kamera untuk aplikasi ini di Pengaturan HP.",
            VuforiaInitError.DEVICE_NOT_SUPPORTED => "HP ini tidak didukung oleh Vuforia Engine.",
            VuforiaInitError.LICENSE_CONFIG_NO_NETWORK_TRANSIENT => "Butuh internet sekali saat pertama dibuka untuk validasi lisensi. Nyalakan data/Wi-Fi lalu buka ulang.",
            VuforiaInitError.LICENSE_CONFIG_NO_NETWORK_PERMANENT => "Butuh internet sekali saat pertama dibuka untuk validasi lisensi. Nyalakan data/Wi-Fi lalu buka ulang.",
            _ => "Vuforia gagal mulai: " + err
        };
        Caption("KAMERA AR TIDAK BISA DIMULAI", msg, new Color(0.5f, 0.05f, 0.05f, 0.92f));
    }

    void CreateTargets()
    {
        VuforiaApplication.Instance.OnVuforiaStarted -= CreateTargets;
        if (targets.Count > 0) return;
        VuforiaBehaviour.Instance.SetMaximumSimultaneousTrackedImages(Mathf.Min(cards.Count, 6));
        foreach (var c in cards)
        {
            try
            {
                var t = VuforiaBehaviour.Instance.ObserverFactory.CreateImageTarget(c.image, cardWidth, c.id);
                if (t != null) targets[c.id] = t;
            }
            catch (System.Exception e) { Debug.LogError("[Karhutla] target " + c.id + " failed: " + e.Message); }
        }
        Debug.Log("[Karhutla] image targets created: " + targets.Count);
        Caption("", "Arahkan kamera ke kartu AR Karhutla. Coba gabungkan kartu PEMICU, DAMPAK, dan MITIGASI!", cN);
    }

    CardScene Spawn(string id, ImageTargetBehaviour t)
    {
        var entry = cards.FirstOrDefault(c => c.id == id);
        if (entry == null || !entry.prefab) return null;
        var go = Instantiate(entry.prefab, t.transform);
        go.transform.localPosition = Vector3.zero; go.transform.localRotation = Quaternion.identity;
        float s = Mathf.Max(t.transform.lossyScale.x, 1e-5f);
        go.transform.localScale = Vector3.one / s;      // work in metres regardless of the target's own scale
        var cs = go.GetComponent<CardScene>(); cs.steamMat = steamMat; cs.BuildFX();
        foreach (var a in go.GetComponents<CardActor>()) a.Init(cs, this);
        return cs;
    }

    void Update()
    {
        if (initError != null) return;
        var visible = new List<CardScene>();
        foreach (var kv in targets)
        {
            var id = kv.Key; var t = kv.Value; if (!t) continue;
            var st = t.TargetStatus.Status;
            bool on = st == Status.TRACKED || st == Status.EXTENDED_TRACKED;
            if (on && (!spawned.TryGetValue(id, out var existing) || !existing)) spawned[id] = Spawn(id, t);
            if (!spawned.TryGetValue(id, out var cs) || !cs) continue;
            if (on) lastSeen[id] = Time.time;
            bool show = lastSeen.TryGetValue(id, out var ls) && Time.time - ls < 0.6f;
            if (cs.gameObject.activeSelf != show) cs.gameObject.SetActive(show);
            if (show) visible.Add(cs);
        }
        CardScene pick(CardCategory c) => visible.Where(v => v.category == c).OrderByDescending(v => lastSeen[v.cardId]).FirstOrDefault();
        var p = pick(CardCategory.Pemicu); var d = pick(CardCategory.Dampak); var m = pick(CardCategory.Mitigasi);
        var key = (p ? p.cardId : "-") + "|" + (d ? d.cardId : "-") + "|" + (m ? m.cardId : "-");
        if (detected) detected.text = visible.Count == 0 ? "Belum ada kartu terdeteksi" :
            "Terdeteksi: " + string.Join("  •  ", visible.Select(v => $"{v.category.ToString().ToUpper()} – {v.title}"));
        if (status) status.text = targets.Count == 0 ? "Menyiapkan..." : visible.Count == 0 ? "Arahkan kamera ke kartu..." : $"{visible.Count} kartu aktif";
        if (key != combo) { combo = key; P = p; D = d; M = m; Restart(); }
    }

    public void Restart()
    {
        if (seq != null) StopCoroutine(seq);
        foreach (var cs in spawned.Values)
        {
            if (!cs) continue;
            foreach (var a in cs.GetComponents<CardActor>()) a.ResetIdle();
            cs.StopAllCoroutines();
            cs.SetLevel(1f);
        }
        if (targets.Count > 0 && initError == null) seq = StartCoroutine(Run());
    }

    public void LoadFreeMode() { SceneManager.LoadScene("FireAR"); }

    void Caption(string title, string text, Color c)
    {
        if (stageTitle) stageTitle.text = title;
        if (caption) caption.text = text;
        if (captionPanel) captionPanel.color = c;
    }

    IEnumerator Run()
    {
        var pa = P ? P.GetComponent<PemicuActor>() : null;
        var ma = M ? M.GetComponent<MitigasiActor>() : null;
        yield return null;
        if (P && D && M)
        {
            D.SetLevel(0f);
            Caption("1. PEMICU – " + P.title, P.info, cP);
            yield return new WaitForSeconds(2.5f);
            Caption("2. DAMPAK – " + D.title, "Api dari pemicu menjalar dan menyebabkan " + D.title.ToLower() + ". " + D.info, cD);
            yield return pa.Attack(D, 3f, () => D.FadeTo(1f, 3f));
            yield return new WaitForSeconds(2.5f);
            Caption("3. MITIGASI – " + M.title, M.info, cM);
            yield return ma.Mitigate(D, () => { D.FadeTo(0f, 3.5f); D.Steam(); P.FadeTo(0f, 3.5f); pa.StopAll(); });
            Caption("KEBAKARAN BERHASIL DIPADAMKAN", "Pemicu → Dampak → Mitigasi. Cegah pembakaran lahan, waspadai kemarau, dan dukung petugas pemadam!", cOK);
        }
        else if (P && D)
        {
            D.SetLevel(0f);
            Caption("PEMICU – " + P.title, P.info, cP);
            yield return new WaitForSeconds(1.5f);
            Caption("PEMICU → DAMPAK", $"{P.title} memicu kebakaran yang berdampak pada {D.title.ToLower()}. {D.info}", cD);
            yield return pa.Attack(D, 3f, () => D.FadeTo(1f, 3f));
        }
        else if (P && M)
        {
            Caption("PEMICU – " + P.title, P.info, cP);
            yield return new WaitForSeconds(1.5f);
            Caption("MITIGASI → PEMICU", $"{M.title} memadamkan api dari {P.title.ToLower()}. {M.info}", cM);
            yield return ma.Mitigate(P, () => { P.FadeTo(0f, 3.5f); P.Steam(); pa.StopAll(); });
            Caption("API PADAM", "Sumber api berhasil dipadamkan sebelum menjalar.", cOK);
        }
        else if (D && M)
        {
            Caption("DAMPAK – " + D.title, D.info, cD);
            yield return new WaitForSeconds(2f);
            Caption("MITIGASI → DAMPAK", $"{M.title} memadamkan kebakaran. {M.info}", cM);
            yield return ma.Mitigate(D, () => { D.FadeTo(0f, 3.5f); D.Steam(); });
            Caption("API PADAM", "Kebakaran berhasil dikendalikan.", cOK);
        }
        else if (P) Caption("PEMICU – " + P.title, P.info + "  (Tambahkan kartu DAMPAK atau MITIGASI)", cP);
        else if (D) Caption("DAMPAK – " + D.title, D.info + "  (Tambahkan kartu PEMICU atau MITIGASI)", cD);
        else if (M) Caption("MITIGASI – " + M.title, M.info + "  (Tambahkan kartu PEMICU atau DAMPAK)", cM);
        else Caption("", "Arahkan kamera ke kartu AR Karhutla. Coba gabungkan kartu PEMICU, DAMPAK, dan MITIGASI!", cN);
    }
}
