using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using Vuforia;
using Image = UnityEngine.UI.Image;

/// Free placement on the floor with Vuforia Ground Plane.
/// Ground Plane needs ARCore or Vuforia VISLAM; on phones without either we show a clear message.
public class VuPlacer : MonoBehaviour
{
    [System.Serializable] public class Item { public string label; public GameObject prefab; public float miniSize = 0.6f; }
    public List<Item> items = new List<Item>();
    public PlaneFinderBehaviour planeFinder;
    public Camera arCamera;
    public Text hint, scaleLabel, selectedLabel;
    public GameObject unsupportedPanel; public Text unsupportedText;
    public List<Image> itemButtons = new List<Image>();
    public Color normalColor = new Color(0.1f, 0.1f, 0.12f, 0.85f), activeColor = new Color(0.85f, 0.25f, 0.05f, 0.95f);
    public float detectTimeout = 12f;

    int selected; bool miniature = true; int anchorCount;
    readonly List<GameObject> placed = new List<GameObject>();
    GameObject current;
    bool tracking, decided, unsupported;
    float startTime; float prevPinch, prevAngle;

    void Start()
    {
        Application.targetFrameRate = 60; Screen.sleepTimeout = SleepTimeout.NeverSleep;
        Select(0); UpdateScaleLabel();
        if (unsupportedPanel) unsupportedPanel.SetActive(false);
        planeFinder.HitTestMode = HitTestMode.INTERACTIVE;
        if (planeFinder.OnInteractiveHitTest != null) planeFinder.OnInteractiveHitTest.AddListener(OnHit);
        else Debug.LogError("[VuPlacer] OnInteractiveHitTest is null");
        VuforiaApplication.Instance.OnVuforiaInitialized += e => { if (e != VuforiaInitError.NONE) ShowUnsupported("Kamera AR tidak bisa dimulai (" + e + ")."); };
        if (VuforiaApplication.Instance.IsRunning) OnStarted(); else VuforiaApplication.Instance.OnVuforiaStarted += OnStarted;
    }

    void OnStarted()
    {
        startTime = Time.time;
        var fusion = VuforiaRuntimeUtilities.GetActiveFusionProvider().ToString();
        Debug.Log("[VuPlacer] fusion provider = " + fusion);
        if (fusion.Contains("VISION_ONLY") || fusion.Contains("NONE"))
            ShowUnsupported("HP ini belum mendukung pelacakan lantai (Ground Plane) karena tidak memiliki ARCore maupun sensor yang terkalibrasi untuk Vuforia.");
        var dp = VuforiaBehaviour.Instance.DevicePoseBehaviour;
        if (dp) dp.OnTargetStatusChanged += (b, s) => { if (s.Status == Status.TRACKED) { tracking = true; decided = true; } };
    }

    void ShowUnsupported(string why)
    {
        unsupported = true; decided = true;
        if (unsupportedPanel) unsupportedPanel.SetActive(true);
        if (unsupportedText) unsupportedText.text = why + "\n\nMode Taruh Bebas hanya berjalan di HP yang mendukung pelacakan lantai. Silakan gunakan MODE KARTU — semua fitur kartu tetap bisa dipakai di HP ini.";
    }

    public void BackToCards() { SceneManager.LoadScene("KartuAR"); }
    public void HideMessage() { if (unsupportedPanel) unsupportedPanel.SetActive(false); }

    public void Select(int i)
    {
        selected = Mathf.Clamp(i, 0, items.Count - 1);
        for (int k = 0; k < itemButtons.Count; k++) if (itemButtons[k]) itemButtons[k].color = k == selected ? activeColor : normalColor;
        if (selectedLabel) selectedLabel.text = "Dipilih: " + items[selected].label;
    }
    public void ToggleScale() { miniature = !miniature; UpdateScaleLabel(); if (current) ApplyScale(current, items[current.GetComponent<PlacedTag>().index]); }
    void UpdateScaleLabel() { if (scaleLabel) scaleLabel.text = miniature ? "Skala: Miniatur" : "Skala: Asli (1:1)"; }
    public void ClearAll() { foreach (var g in placed) if (g) Destroy(g.transform.parent ? g.transform.parent.gameObject : g); placed.Clear(); current = null; }
    public void DeleteLast()
    {
        if (placed.Count == 0) return;
        var g = placed[placed.Count - 1]; placed.RemoveAt(placed.Count - 1);
        if (g) Destroy(g.transform.parent ? g.transform.parent.gameObject : g);
        current = placed.Count > 0 ? placed[placed.Count - 1] : null;
    }

    void Update()
    {
        if (!decided && startTime > 0 && Time.time - startTime > detectTimeout && !tracking)
            ShowUnsupported("Pelacakan lantai tidak aktif setelah " + detectTimeout + " detik.");
        if (hint)
        {
            if (unsupported) hint.text = "Mode ini tidak didukung di HP ini.";
            else if (!tracking) hint.text = "Gerakkan HP perlahan ke arah lantai/meja...";
            else if (placed.Count == 0) hint.text = "Ketuk lantai untuk menaruh: " + items[selected].label;
            else hint.text = "2 jari: perbesar/putar  •  ketuk lantai: tambah aset";
        }
        if (unsupported) return;
        int n = Input.touchCount;
        if (n == 1)
        {
            var t = Input.GetTouch(0);
            if (EventSystem.current && EventSystem.current.IsPointerOverGameObject(t.fingerId)) return;
            if (t.phase == TouchPhase.Began) planeFinder.PerformHitTest(t.position);
        }
        else if (n >= 2 && current)
        {
            var a = Input.GetTouch(0); var b = Input.GetTouch(1);
            float pinch = Vector2.Distance(a.position, b.position);
            float ang = Mathf.Atan2(b.position.y - a.position.y, b.position.x - a.position.x) * Mathf.Rad2Deg;
            if (a.phase == TouchPhase.Began || b.phase == TouchPhase.Began) { prevPinch = pinch; prevAngle = ang; return; }
            if (prevPinch > 1f)
            {
                var s = current.transform.localScale * Mathf.Clamp(pinch / prevPinch, 0.9f, 1.1f);
                if (s.x > 0.001f && s.x < 5f) current.transform.localScale = s;
            }
            current.transform.Rotate(0f, -(ang - prevAngle), 0f, Space.World);
            prevPinch = pinch; prevAngle = ang;
        }
    }

    void OnHit(HitTestResult hit)
    {
        if (hit == null || unsupported) return;
        var anchor = VuforiaBehaviour.Instance.ObserverFactory.CreateAnchorBehaviour("Anchor_" + (anchorCount++), hit);
        var item = items[selected];
        var go = Instantiate(item.prefab, anchor.transform);
        go.transform.localPosition = Vector3.zero;
        go.AddComponent<PlacedTag>().index = selected;
        ApplyScale(go, item);
        var toCam = arCamera.transform.position - go.transform.position; toCam.y = 0;
        if (toCam.sqrMagnitude > 1e-4f) go.transform.rotation = Quaternion.LookRotation(-toCam.normalized, Vector3.up) * Quaternion.Euler(0, 200f, 0);
        placed.Add(go); current = go;
    }

    void ApplyScale(GameObject go, Item item)
    {
        var tag = go.GetComponent<PlacedTag>();
        if (tag.realSize <= 0f)
        {
            var q = go.transform.rotation; go.transform.rotation = Quaternion.identity; go.transform.localScale = Vector3.one;
            var rs = go.GetComponentsInChildren<MeshRenderer>();
            if (rs.Length > 0) { var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); tag.realSize = Mathf.Max(b.size.x, b.size.y, b.size.z); }
            else tag.realSize = 1f;
            go.transform.rotation = q;
        }
        float parentScale = go.transform.parent ? go.transform.parent.lossyScale.x : 1f;
        float s = (miniature ? item.miniSize / Mathf.Max(tag.realSize, 0.01f) : 1f) / Mathf.Max(parentScale, 1e-5f);
        go.transform.localScale = Vector3.one * s;
    }
}

public class PlacedTag : MonoBehaviour { public int index; public float realSize; }
