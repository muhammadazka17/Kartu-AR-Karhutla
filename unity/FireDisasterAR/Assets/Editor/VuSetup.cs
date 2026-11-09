using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Rendering;
using UnityEngine.UI;
using Vuforia;
using Image = UnityEngine.UI.Image;

public static class VuSetup
{
    const string LICENSE = "PASTE_YOUR_VUFORIA_LICENSE_KEY_HERE";
    const string CARD_SCENE = "Assets/Scenes/KartuAR.unity", FREE_SCENE = "Assets/Scenes/FireAR.unity";
    static readonly (string id, string file)[] Cards = {
        ("card_120", "kartu_120_pembakaran"), ("card_121", "kartu_121_cuaca"), ("card_122", "kartu_122_kabutasap"),
        ("card_123", "kartu_123_ekosistem"), ("card_124", "kartu_124_waterbomb"), ("card_125", "kartu_125_satgas") };
    static readonly (string path, string label, float mini)[] FreeItems = {
        ("Assets/Prefabs/truck.prefab", "Truk Damkar", 0.6f), ("Assets/Prefabs/heli.prefab", "Helikopter", 0.6f),
        ("Assets/Prefabs/house.prefab", "Rumah Terbakar", 0.6f), ("Assets/Prefabs/ruin.prefab", "Reruntuhan", 0.6f),
        ("Assets/Prefabs/person.prefab", "Penyembur Api", 0.35f), ("Assets/Prefabs/weather.prefab", "Cuaca Ekstrem", 0.6f),
        ("Assets/Prefabs/tree.prefab", "Pohon Terbakar", 0.45f), ("Assets/Prefabs/deadtree.prefab", "Pohon Mati", 0.45f),
        ("Assets/Prefabs/brush.prefab", "Semak Terbakar", 0.4f), ("Assets/Prefabs/rocks.prefab", "Batu", 0.3f),
        ("Assets/Prefabs/log.prefab", "Kayu Gelondong", 0.35f), ("Assets/Prefabs/ground.prefab", "Bara Api", 0.35f),
        ("Assets/Prefabs/fire_only.prefab", "Api Saja", 0.3f) };
    static Font font;
    static Material fire, smoke, ember, water, steam;

    public static void Run()
    {
        try
        {
            font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            fire = Mat("M_Fire"); smoke = Mat("M_Smoke"); ember = Mat("M_Ember"); water = Mat("M_Water"); steam = Mat("M_Steam");
            ConfigureVuforia();
            CardTextures();
            ExtraPrefabs();
            BuildCardScene();
            BuildFreeScene();
            ConfigurePlayer();
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(CARD_SCENE, true), new EditorBuildSettingsScene(FREE_SCENE, true) };
            AssetDatabase.SaveAssets();
            Debug.Log("[VU] SETUP_OK");
            EditorApplication.Exit(0);
        }
        catch (System.Exception e) { Debug.LogError("[VU] SETUP_FAIL " + e); EditorApplication.Exit(1); }
    }

    static Material Mat(string n) => AssetDatabase.LoadAssetAtPath<Material>($"Assets/FX/Materials/{n}.mat");

    // ---------------------------------------------------------------- Vuforia configuration (license, targets, ARCore optional)
    static void ConfigureVuforia()
    {
        var cfg = VuforiaConfiguration.Instance;
        var gen = cfg.Vuforia;
        var t = gen.GetType();
        var names = t.GetProperties(BindingFlags.Public | BindingFlags.Instance).Select(p => p.Name + ":" + p.PropertyType.Name).ToList();
        Debug.Log("[VU] GenericVuforiaConfiguration props: " + string.Join(", ", names));
        void Set(string prop, System.Func<System.Type, object> value)
        {
            var p = t.GetProperty(prop, BindingFlags.Public | BindingFlags.Instance);
            if (p == null || !p.CanWrite) { Debug.Log("[VU] no property " + prop); return; }
            p.SetValue(gen, value(p.PropertyType)); Debug.Log($"[VU] set {prop} = {p.GetValue(gen)}");
        }
        Set("LicenseKey", _ => LICENSE);
        Set("MaxSimultaneousImageTargets", _ => 6);
        Set("ARCoreRequirement", pt => System.Enum.GetNames(pt).Contains("OPTIONAL") ? System.Enum.Parse(pt, "OPTIONAL") : System.Enum.GetValues(pt).GetValue(0));
        // every other config section: report + make ARCore optional wherever such a setting exists
        foreach (var sp in cfg.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            object sec; try { sec = sp.GetValue(cfg); } catch { continue; }
            if (sec == null || sp.PropertyType.IsPrimitive) continue;
            var props = sec.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance);
            Debug.Log($"[VU] section {sp.Name}: " + string.Join(", ", props.Select(p => p.Name + ":" + p.PropertyType.Name)));
            foreach (var p in props.Where(p => p.CanWrite && p.Name.IndexOf("ARCore", System.StringComparison.OrdinalIgnoreCase) >= 0))
            {
                if (p.PropertyType.IsEnum && System.Enum.GetNames(p.PropertyType).Contains("OPTIONAL")) p.SetValue(sec, System.Enum.Parse(p.PropertyType, "OPTIONAL"));
                if (p.PropertyType == typeof(bool) && p.Name.IndexOf("Include", System.StringComparison.OrdinalIgnoreCase) >= 0) p.SetValue(sec, true);
                Debug.Log($"[VU]   {sp.Name}.{p.Name} = {p.GetValue(sec)}");
            }
        }
        if (string.IsNullOrEmpty(AssetDatabase.GetAssetPath(cfg)))
        {
            Directory.CreateDirectory("Assets/Resources");
            var existing = AssetDatabase.LoadAssetAtPath<VuforiaConfiguration>("Assets/Resources/VuforiaConfiguration.asset");
            if (existing) { EditorUtility.CopySerialized(cfg, existing); cfg = existing; }
            else AssetDatabase.CreateAsset(cfg, "Assets/Resources/VuforiaConfiguration.asset");
        }
        EditorUtility.SetDirty(cfg); AssetDatabase.SaveAssets();
        var check = Resources.Load<VuforiaConfiguration>("VuforiaConfiguration");
        Debug.Log("[VU] config asset: " + AssetDatabase.GetAssetPath(cfg) + " license len in resources=" + (check ? check.Vuforia.LicenseKey.Length : -1));
    }

    static void CardTextures()
    {
        foreach (var c in Cards)
        {
            var p = $"Assets/Cards/{c.file}.png";
            var imp = (TextureImporter)AssetImporter.GetAtPath(p);
            imp.isReadable = true; imp.mipmapEnabled = false; imp.npotScale = TextureImporterNPOTScale.None; imp.maxTextureSize = 2048;
            imp.textureCompression = TextureImporterCompression.Uncompressed;
            var a = imp.GetPlatformTextureSettings("Android"); a.overridden = true; a.format = TextureImporterFormat.RGB24; a.maxTextureSize = 2048; imp.SetPlatformTextureSettings(a);
            var d = imp.GetDefaultPlatformTextureSettings(); d.format = TextureImporterFormat.RGB24; imp.SetPlatformTextureSettings(d);
            imp.SaveAndReimport();
        }
    }

    static void ExtraPrefabs()
    {
        void Make(string key, bool fx)
        {
            var path = $"Assets/Prefabs/{key}.prefab";
            var model = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Models/{key}.glb");
            var root = new GameObject(key);
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(model); inst.transform.SetParent(root.transform, false);
            if (fx) { var f = root.AddComponent<FireFX>(); f.fireMat = fire; f.smokeMat = smoke; f.emberMat = ember; }
            PrefabUtility.SaveAsPrefabAsset(root, path); Object.DestroyImmediate(root);
        }
        Make("heli", false); Make("person", false); Make("weather", true);
    }

    // ---------------------------------------------------------------- AR camera
    static GameObject ARCamera(bool devicePose)
    {
        bool ok = false;
        try { ok = EditorApplication.ExecuteMenuItem("GameObject/Vuforia Engine/AR Camera"); } catch { }
        var vb = Object.FindFirstObjectByType<VuforiaBehaviour>();
        GameObject cam;
        if (vb) cam = vb.gameObject;
        else
        {
            cam = new GameObject("ARCamera"); cam.AddComponent<Camera>(); cam.AddComponent<VuforiaBehaviour>(); cam.AddComponent<DefaultInitializationErrorHandler>();
        }
        cam.tag = "MainCamera";
        var c = cam.GetComponent<Camera>(); c.nearClipPlane = 0.01f; c.farClipPlane = 100f;
        var dp = cam.GetComponent<DevicePoseBehaviour>();
        if (!dp && devicePose) dp = cam.AddComponent<DevicePoseBehaviour>();
        if (dp) dp.enabled = devicePose;
        Debug.Log($"[VU] ARCamera menu={ok} comps={string.Join(",", cam.GetComponents<Component>().Select(x => x.GetType().Name))} devicePose={(dp ? dp.enabled.ToString() : "none")}");
        return cam;
    }

    static void Lighting()
    {
        var l = new GameObject("Directional Light").AddComponent<Light>();
        l.type = LightType.Directional; l.intensity = 1.1f; l.shadows = LightShadows.Soft; l.transform.rotation = Quaternion.Euler(55, -35, 0);
        RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = new Color(0.55f, 0.55f, 0.6f);
        RenderSettings.skybox = AssetDatabase.GetBuiltinExtraResource<Material>("Default-Skybox.mat");
    }

    // ---------------------------------------------------------------- UI helpers
    static Text MakeText(Transform parent, string name, string txt, int size, TextAnchor anchor, Color color)
    {
        var go = new GameObject(name, typeof(RectTransform)); go.transform.SetParent(parent, false);
        var t = go.AddComponent<Text>(); t.font = font; t.text = txt; t.fontSize = size; t.alignment = anchor; t.color = color;
        t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Overflow;
        var sh = go.AddComponent<Shadow>(); sh.effectColor = new Color(0, 0, 0, 0.8f); sh.effectDistance = new Vector2(2, -2);
        return t;
    }
    static RectTransform Rect(GameObject go, Vector2 aMin, Vector2 aMax, Vector2 offMin, Vector2 offMax)
    {
        var r = go.GetComponent<RectTransform>() ?? go.AddComponent<RectTransform>();
        r.anchorMin = aMin; r.anchorMax = aMax; r.offsetMin = offMin; r.offsetMax = offMax; return r;
    }
    static (Button, Image, Text) MakeButton(Transform parent, string label, Color bg, int fontSize = 32)
    {
        var go = new GameObject("Btn_" + label, typeof(RectTransform)); go.transform.SetParent(parent, false);
        var img = go.AddComponent<Image>(); img.color = bg;
        var b = go.AddComponent<Button>(); var cb = b.colors; cb.pressedColor = new Color(1f, 0.7f, 0.4f); b.colors = cb;
        var t = MakeText(go.transform, "Label", label, fontSize, TextAnchor.MiddleCenter, Color.white);
        Rect(t.gameObject, Vector2.zero, Vector2.one, new Vector2(8, 4), new Vector2(-8, -4));
        return (b, img, t);
    }
    static Transform Canvas()
    {
        var es = new GameObject("EventSystem"); es.AddComponent<EventSystem>();
        var uiModule = System.Type.GetType("UnityEngine.InputSystem.UI.InputSystemUIInputModule, Unity.InputSystem");
        if (uiModule != null) es.AddComponent(uiModule); else es.AddComponent<StandaloneInputModule>();
        var canvasGO = new GameObject("Canvas", typeof(RectTransform));
        var canvas = canvasGO.AddComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = canvasGO.AddComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1080, 1920); scaler.matchWidthOrHeight = 0.5f;
        canvasGO.AddComponent<GraphicRaycaster>();
        return canvasGO.transform;
    }

    // ---------------------------------------------------------------- card scene
    static void BuildCardScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        Lighting(); ARCamera(false);
        var mgr = new GameObject("KarhutlaManager").AddComponent<KarhutlaManager>();
        mgr.fireMat = fire; mgr.waterMat = water; mgr.steamMat = steam; mgr.cardWidth = 0.063f;
        foreach (var c in Cards)
            mgr.cards.Add(new KarhutlaManager.CardEntry { id = c.id, image = AssetDatabase.LoadAssetAtPath<Texture2D>($"Assets/Cards/{c.file}.png"),
                prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Prefabs/Cards/{c.id}.prefab") });
        Debug.Log("[VU] card entries ok=" + mgr.cards.Count(c => c.image && c.prefab));
        var cv = Canvas();
        var top = new GameObject("TopBar", typeof(RectTransform)); top.transform.SetParent(cv, false);
        Rect(top, new Vector2(0, 1), new Vector2(1, 1), new Vector2(0, -300), Vector2.zero); top.AddComponent<Image>().color = new Color(0, 0, 0, 0.5f);
        var title = MakeText(top.transform, "Title", "KARTU AR KARHUTLA", 54, TextAnchor.UpperCenter, new Color(1f, 0.75f, 0.25f)); title.fontStyle = FontStyle.Bold;
        Rect(title.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(20, -125), new Vector2(-20, -55));
        var status = MakeText(top.transform, "Status", "", 30, TextAnchor.UpperCenter, Color.white);
        Rect(status.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(20, -170), new Vector2(-20, -128));
        var det = MakeText(top.transform, "Detected", "", 28, TextAnchor.UpperCenter, new Color(1f, 0.85f, 0.6f));
        Rect(det.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(20, -290), new Vector2(-20, -172));
        var bot = new GameObject("CaptionPanel", typeof(RectTransform)); bot.transform.SetParent(cv, false);
        Rect(bot, new Vector2(0, 0), new Vector2(1, 0), new Vector2(20, 150), new Vector2(-20, 520));
        var capImg = bot.AddComponent<Image>(); capImg.color = new Color(0, 0, 0, 0.7f);
        var st = MakeText(bot.transform, "StageTitle", "", 42, TextAnchor.UpperLeft, Color.white); st.fontStyle = FontStyle.Bold;
        Rect(st.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(30, -80), new Vector2(-30, -20));
        var cap = MakeText(bot.transform, "Caption", "", 34, TextAnchor.UpperLeft, Color.white);
        Rect(cap.gameObject, new Vector2(0, 0), new Vector2(1, 1), new Vector2(30, 20), new Vector2(-30, -90));
        var row = new GameObject("Buttons", typeof(RectTransform)); row.transform.SetParent(cv, false);
        Rect(row, new Vector2(0, 0), new Vector2(1, 0), new Vector2(20, 25), new Vector2(-20, 130));
        var hl = row.AddComponent<HorizontalLayoutGroup>(); hl.spacing = 16; hl.childForceExpandWidth = true; hl.childControlWidth = true; hl.childControlHeight = true;
        var (bRe, _, _) = MakeButton(row.transform, "Ulangi Animasi", new Color(0.55f, 0.2f, 0.05f, 0.92f), 34);
        var (bFree, _, _) = MakeButton(row.transform, "Mode Taruh Bebas", new Color(0.12f, 0.12f, 0.14f, 0.92f), 34);
        UnityEventTools.AddPersistentListener(bRe.onClick, mgr.Restart);
        UnityEventTools.AddPersistentListener(bFree.onClick, mgr.LoadFreeMode);
        mgr.status = status; mgr.detected = det; mgr.caption = cap; mgr.stageTitle = st; mgr.captionPanel = capImg;
        EditorSceneManager.SaveScene(scene, CARD_SCENE);
    }

    // ---------------------------------------------------------------- free placement scene (Ground Plane)
    static void BuildFreeScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        Lighting(); var cam = ARCamera(true);
        var pfGO = new GameObject("Plane Finder");
        var pf = pfGO.AddComponent<PlaneFinderBehaviour>();
        foreach (var extra in pfGO.GetComponents<Component>().Where(c => c is AnchorInputListenerBehaviour || c is ContentPositioningBehaviour)) Object.DestroyImmediate(extra);
        // reticle shown where the floor is found
        var ret = GameObject.CreatePrimitive(PrimitiveType.Cylinder); Object.DestroyImmediate(ret.GetComponent<Collider>());
        ret.name = "PlaneIndicator"; ret.transform.SetParent(pfGO.transform, false); ret.transform.localScale = new Vector3(0.12f, 0.001f, 0.12f);
        var rm = new Material(Shader.Find("Sprites/Default")) { color = new Color(1f, 0.55f, 0.15f, 0.5f) };
        AssetDatabase.CreateAsset(rm, "Assets/FX/Materials/M_Reticle.mat"); ret.GetComponent<Renderer>().sharedMaterial = rm;
        pf.PlaneIndicator = ret;
        foreach (var fn in new[] { "OnInteractiveHitTest", "OnAutomaticHitTest" })
        {
            var f = typeof(PlaneFinderBehaviour).GetField(fn);
            if (f != null && f.GetValue(pf) == null) f.SetValue(pf, System.Activator.CreateInstance(f.FieldType));
        }
        EditorUtility.SetDirty(pf);
        Debug.Log("[VU] PlaneFinder comps=" + string.Join(",", pfGO.GetComponents<Component>().Select(c => c.GetType().Name)) + " hitEvent=" + (pf.OnInteractiveHitTest != null));

        var placer = new GameObject("VuPlacer").AddComponent<VuPlacer>();
        placer.planeFinder = pf; placer.arCamera = cam.GetComponent<Camera>();
        var cv = Canvas();
        var top = new GameObject("TopBar", typeof(RectTransform)); top.transform.SetParent(cv, false);
        Rect(top, new Vector2(0, 1), new Vector2(1, 1), new Vector2(0, -330), Vector2.zero); top.AddComponent<Image>().color = new Color(0, 0, 0, 0.45f);
        var title = MakeText(top.transform, "Title", "MODE TARUH BEBAS", 52, TextAnchor.UpperCenter, new Color(1f, 0.65f, 0.2f)); title.fontStyle = FontStyle.Bold;
        Rect(title.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(20, -120), new Vector2(-20, -55));
        var hint = MakeText(top.transform, "Hint", "", 32, TextAnchor.UpperCenter, Color.white);
        Rect(hint.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(30, -200), new Vector2(-30, -125));
        var tools = new GameObject("Tools", typeof(RectTransform)); tools.transform.SetParent(top.transform, false);
        Rect(tools, new Vector2(0, 0), new Vector2(1, 0), new Vector2(20, 15), new Vector2(-20, 110));
        var hl = tools.AddComponent<HorizontalLayoutGroup>(); hl.spacing = 14; hl.childForceExpandWidth = true; hl.childControlWidth = true; hl.childControlHeight = true;
        var tool = new Color(0.12f, 0.12f, 0.14f, 0.9f);
        var (bCard, _, _) = MakeButton(tools.transform, "Mode Kartu", new Color(0.55f, 0.2f, 0.05f, 0.92f), 30);
        var (bScale, _, tScale) = MakeButton(tools.transform, "Skala: Miniatur", tool, 30);
        var (bUndo, _, _) = MakeButton(tools.transform, "Hapus Terakhir", tool, 30);
        var (bClear, _, _) = MakeButton(tools.transform, "Hapus Semua", new Color(0.55f, 0.08f, 0.05f, 0.9f), 30);
        UnityEventTools.AddPersistentListener(bCard.onClick, placer.BackToCards);
        UnityEventTools.AddPersistentListener(bScale.onClick, placer.ToggleScale);
        UnityEventTools.AddPersistentListener(bUndo.onClick, placer.DeleteLast);
        UnityEventTools.AddPersistentListener(bClear.onClick, placer.ClearAll);
        placer.hint = hint; placer.scaleLabel = tScale;

        var bottom = new GameObject("BottomBar", typeof(RectTransform)); bottom.transform.SetParent(cv, false);
        Rect(bottom, new Vector2(0, 0), new Vector2(1, 0), Vector2.zero, new Vector2(0, 300)); bottom.AddComponent<Image>().color = new Color(0, 0, 0, 0.45f);
        var sel = MakeText(bottom.transform, "Selected", "", 34, TextAnchor.MiddleCenter, new Color(1f, 0.8f, 0.5f));
        Rect(sel.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(20, -70), new Vector2(-20, -10)); placer.selectedLabel = sel;
        var view = new GameObject("Scroll", typeof(RectTransform)); view.transform.SetParent(bottom.transform, false);
        Rect(view, Vector2.zero, Vector2.one, new Vector2(10, 20), new Vector2(-10, -80));
        view.AddComponent<Image>().color = new Color(0, 0, 0, 0.01f); view.AddComponent<RectMask2D>();
        var sr = view.AddComponent<ScrollRect>(); sr.horizontal = true; sr.vertical = false; sr.movementType = ScrollRect.MovementType.Clamped;
        var content = new GameObject("Content", typeof(RectTransform)); content.transform.SetParent(view.transform, false);
        var crt = content.GetComponent<RectTransform>(); crt.anchorMin = new Vector2(0, 0); crt.anchorMax = new Vector2(0, 1); crt.pivot = new Vector2(0, 0.5f);
        crt.offsetMin = Vector2.zero; crt.offsetMax = Vector2.zero;
        var chl = content.AddComponent<HorizontalLayoutGroup>(); chl.spacing = 16; chl.padding = new RectOffset(10, 10, 6, 6);
        chl.childControlWidth = true; chl.childControlHeight = true; chl.childForceExpandWidth = false; chl.childForceExpandHeight = true;
        content.AddComponent<ContentSizeFitter>().horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
        sr.content = crt; sr.viewport = view.GetComponent<RectTransform>();
        int idx = 0;
        foreach (var it in FreeItems)
        {
            var pfab = AssetDatabase.LoadAssetAtPath<GameObject>(it.path);
            if (!pfab) { Debug.LogWarning("[VU] missing " + it.path); continue; }
            placer.items.Add(new VuPlacer.Item { label = it.label, prefab = pfab, miniSize = it.mini });
            var (b, img, _) = MakeButton(content.transform, it.label, placer.normalColor, 32);
            var le = b.gameObject.AddComponent<LayoutElement>(); le.preferredWidth = 250; le.minWidth = 250;
            placer.itemButtons.Add(img);
            UnityEventTools.AddIntPersistentListener(b.onClick, placer.Select, idx++);
        }
        // "not supported" message panel
        var panel = new GameObject("UnsupportedPanel", typeof(RectTransform)); panel.transform.SetParent(cv, false);
        Rect(panel, new Vector2(0, 0.3f), new Vector2(1, 0.72f), new Vector2(40, 0), new Vector2(-40, 0));
        panel.AddComponent<Image>().color = new Color(0.08f, 0.08f, 0.1f, 0.95f);
        var ph = MakeText(panel.transform, "Head", "MODE INI TIDAK DIDUKUNG DI HP INI", 40, TextAnchor.UpperCenter, new Color(1f, 0.6f, 0.2f)); ph.fontStyle = FontStyle.Bold;
        Rect(ph.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(30, -110), new Vector2(-30, -30));
        var pt = MakeText(panel.transform, "Body", "", 32, TextAnchor.UpperLeft, Color.white);
        Rect(pt.gameObject, new Vector2(0, 0), new Vector2(1, 1), new Vector2(40, 170), new Vector2(-40, -120));
        var prow = new GameObject("PanelButtons", typeof(RectTransform)); prow.transform.SetParent(panel.transform, false);
        Rect(prow, new Vector2(0, 0), new Vector2(1, 0), new Vector2(30, 30), new Vector2(-30, 140));
        var phl = prow.AddComponent<HorizontalLayoutGroup>(); phl.spacing = 16; phl.childForceExpandWidth = true; phl.childControlWidth = true; phl.childControlHeight = true;
        var (pb1, _, _) = MakeButton(prow.transform, "Ke Mode Kartu", new Color(0.55f, 0.2f, 0.05f, 0.95f), 34);
        var (pb2, _, _) = MakeButton(prow.transform, "Tutup", new Color(0.2f, 0.2f, 0.22f, 0.95f), 34);
        UnityEventTools.AddPersistentListener(pb1.onClick, placer.BackToCards);
        UnityEventTools.AddPersistentListener(pb2.onClick, placer.HideMessage);
        placer.unsupportedPanel = panel; placer.unsupportedText = pt;
        EditorSceneManager.SaveScene(scene, FREE_SCENE);
    }

    // ---------------------------------------------------------------- player + build
    static void ConfigurePlayer()
    {
        var nbt = NamedBuildTarget.Android;
        PlayerSettings.companyName = "Rosyid"; PlayerSettings.productName = "Fire Disaster AR";
        PlayerSettings.SetApplicationIdentifier(nbt, "com.rosyid.firedisasterar");
        PlayerSettings.bundleVersion = "2.0"; PlayerSettings.Android.bundleVersionCode = 2;
        PlayerSettings.SetScriptingBackend(nbt, ScriptingImplementation.IL2CPP);
        PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
        PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel29;
        PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
        PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.OpenGLES3 });
        PlayerSettings.defaultInterfaceOrientation = UIOrientation.Portrait;
    }

    public static void Build()
    {
        try
        {
            var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Builds")); Directory.CreateDirectory(dir);
            var opts = new BuildPlayerOptions
            {
                scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
                locationPathName = Path.Combine(dir, "FireDisasterAR_Vuforia.apk"),
                target = BuildTarget.Android, targetGroup = BuildTargetGroup.Android, options = BuildOptions.None
            };
            Debug.Log("[VU] BUILD_SCENES " + string.Join(", ", opts.scenes));
            var rep = BuildPipeline.BuildPlayer(opts);
            Debug.Log($"[VU] BUILD_RESULT {rep.summary.result} errors={rep.summary.totalErrors} time={rep.summary.totalTime}");
            EditorApplication.Exit(rep.summary.result == BuildResult.Succeeded ? 0 : 1);
        }
        catch (System.Exception e) { Debug.LogError("[VU] BUILD_FAIL " + e); EditorApplication.Exit(1); }
    }
}
