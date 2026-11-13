#!/usr/bin/env python3
"""Verified CI-only source repairs for the two Dayflow Android projects."""
from pathlib import Path
import shutil
import sys

def edit(path, old, new, label, required=True):
    path = Path(path)
    if not path.is_file():
        raise SystemExit(f"[{label}] Missing file: {path}")
    s = path.read_text(encoding="utf-8")
    if new in s:
        return
    if old not in s:
        if required:
            raise SystemExit(f"[{label}] Expected source fragment not found: {path}")
        return
    path.write_text(s.replace(old, new), encoding="utf-8")
    print(f"[{label}] Patched {path.name}")

def add_import(path, line, anchor, label):
    path = Path(path)
    s = path.read_text(encoding="utf-8")
    if line not in s:
        if anchor not in s:
            raise SystemExit(f"[{label}] Import anchor missing: {path}")
        path.write_text(s.replace(anchor, anchor + line + "\n", 1), encoding="utf-8")

def migrate(p):
    b = p / "app/src/main/java/app/dayflow/android"
    tag = "migrate"
    edit(b/"time/TimeFmt.kt",
         'fun num(n: Number | String, lang: String): String =\n        if (lang == "ar") toArabicDigits(n.toString()) else n.toString()',
         'fun num(n: Any, lang: String): String =\n        if (lang == "ar") toArabicDigits(n.toString()) else n.toString()', tag)
    u = b/"ui/UiKit.kt"
    add_import(u, "import androidx.compose.foundation.layout.heightIn", "import androidx.compose.foundation.layout.height\n", tag)
    add_import(u, "import androidx.compose.ui.graphics.compositeOver", "import androidx.compose.ui.graphics.Color\n", tag)
    s = u.read_text(encoding="utf-8")
    if "fun Chip(text: String, selected: Boolean, modifier: Modifier = Modifier, action: () -> Unit)" not in s:
        marker = "@Composable\nfun ScreenHeader("
        adapters = """/**
 * Trailing-lambda adapters keep the original positional APIs while making the
 * callback the last parameter for idiomatic Compose call sites.
 */
@Composable
fun Chip(text: String, selected: Boolean, modifier: Modifier = Modifier, action: () -> Unit) =
    Chip(text, selected, action, modifier)

@Composable
fun DFToggle(on: Boolean, label: String = "", change: (Boolean) -> Unit) =
    DFToggle(on, change, label)

@Composable
fun Segmented(options: List<Pair<String, String>>, value: String, modifier: Modifier = Modifier, change: (String) -> Unit) =
    Segmented(options, value, change, modifier)

"""
        if marker not in s: raise SystemExit("[migrate] UiKit ScreenHeader anchor missing")
        u.write_text(s.replace(marker, adapters+marker, 1), encoding="utf-8")
    edit(b/"ui/screens/MeScreen.kt",
         'Chip(if (lang == "ar") c.second else c.first, cat == c.first) { cat = c.first }',
         'Chip(if (lang == "ar") c.second.second else c.second.first, cat == c.first) { cat = c.first }', tag)
    t = b/"ui/theme/Themes.kt"
    add_import(t, "import androidx.compose.ui.graphics.compositeOver", "import androidx.compose.ui.graphics.Color\n", tag)
    edit(t, 'Math.pow(((v + 0.055f) / 1.055f), 2.4)',
         'Math.pow(((v + 0.055f) / 1.055f).toDouble(), 2.4)', tag)
    edit(b/"ui/shell/AppShell.kt",
         '.widthIn(max = 640.dp).align(Alignment.CenterHorizontally).padding(horizontal = 16.dp)',
         '.widthIn(max = 640.dp).padding(horizontal = 16.dp)', tag)
    add_import(b/"ui/screens/TodayScreen.kt",
               "import androidx.compose.foundation.layout.size",
               "import androidx.compose.foundation.layout.padding\n", tag)
    w = b/"widget/WidgetPainter.kt"
    s = w.read_text(encoding="utf-8")
    for a, z in [("0x331A1814)", "0x331A1814.toInt())"),
                 ("0x14FFFFFF,", "0x14FFFFFF.toInt(),"),
                 ("0x99FFFFFF,", "0x99FFFFFF.toInt(),"),
                 ("0x99F5F5F5,", "0x99F5F5F5.toInt(),")]:
        s = s.replace(a, z)
    s = s.replace("color = it; style = Paint.Style.STROKE; strokeWidth = 1.5f",
                  "color = it; this.style = Paint.Style.STROKE; strokeWidth = 1.5f")
    w.write_text(s, encoding="utf-8")
    print("[migrate] Patched widget painter constants/receiver")

def refactor(p):
    tag = "refactor"
    edit(p/"app/src/main/res/values/styles.xml",
         '        <item name="android:windowLightNavigationBar">true</item>\n', "", tag)
    v27 = p/"app/src/main/res/values-v27"
    v27.mkdir(parents=True, exist_ok=True)
    (v27/"styles.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Dayflow" parent="android:style/Theme.Material.Light.NoActionBar">
        <item name="android:fontFamily">sans</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:statusBarColor">#f7f5f0</item>
        <item name="android:navigationBarColor">#f7f5f0</item>
        <item name="android:windowLightNavigationBar">true</item>
        <item name="android:windowActionModeOverlay">true</item>
    </style>
</resources>
""", encoding="utf-8")
    r = p/"app/src/main/java/app/dayflow/android/alarm/AlarmScheduler.kt"
    old = """class RestoreReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        AlarmScheduler.restore(context)
        DayflowWidgetProvider.updateAll(context)
    }
}"""
    new = """class RestoreReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val allowedActions = setOf(
            "android.intent.action.BOOT_COMPLETED",
            "android.intent.action.TIME_SET",
            "android.intent.action.TIMEZONE_CHANGED",
            "android.app.action.SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED",
        )
        if (intent.action !in allowedActions) return
        AlarmScheduler.restore(context)
        DayflowWidgetProvider.updateAll(context)
    }
}"""
    edit(r, old, new, tag)
    # Restore missing Android resources from the genuine seasonal images bundled
    # beside the Android project in the same archive.
    source = p.parent/"public/seasonal"
    nodpi = p/"app/src/main/res/drawable-nodpi"
    draw = p/"app/src/main/res/drawable"
    nodpi.mkdir(parents=True, exist_ok=True)
    draw.mkdir(parents=True, exist_ok=True)
    for season in ("ramadan", "spring", "summer", "autumn", "winter"):
        src = source/f"real-{season}.png"
        if not src.is_file(): raise SystemExit(f"[refactor] Missing seasonal source asset: {src}")
        dst = nodpi/f"season_{season}.png"
        if not dst.exists(): shutil.copyfile(src, dst)
        alias = draw/f"decor_{season}.xml"
        if not alias.exists():
            alias.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<bitmap xmlns:android="http://schemas.android.com/apk/res/android" android:src="@drawable/season_{season}" android:gravity="center" />
''', encoding="utf-8")
    robot = draw/"robot_idle.xml"
    if not robot.exists():
        robot.write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="128dp" android:height="160dp" android:viewportWidth="128" android:viewportHeight="160">
    <path android:fillColor="#6B8FB5" android:pathData="M62,8h4v18h-4z" />
    <path android:fillColor="#E9F1F8" android:strokeColor="#8BA7C2" android:strokeWidth="3" android:pathData="M35,34h58a15,15 0,0 1 15,15v31a15,15 0,0 1 -15,15h-58a15,15 0,0 1 -15,-15v-31a15,15 0,0 1 15,-15z" />
    <path android:fillColor="#355B80" android:pathData="M43,57a7,7 0,1 0 14,0a7,7 0,1 0 -14,0M71,57a7,7 0,1 0 14,0a7,7 0,1 0 -14,0" />
    <path android:fillColor="#88B5D9" android:pathData="M52,76h24v5h-24z" />
    <path android:fillColor="#D9E7F3" android:strokeColor="#8BA7C2" android:strokeWidth="3" android:pathData="M40,101h48l9,39h-66z" />
    <path android:fillColor="#8BA7C2" android:pathData="M22,109h12v28h-12zM94,109h12v28h-12zM47,138h13v17h-13zM68,138h13v17h-13z" />
</vector>
""", encoding="utf-8")
        print("[refactor] Added neutral robot vector fallback; replace with original artwork before release")

if len(sys.argv) != 3:
    raise SystemExit("Usage: patch-android-sources.py <migrate|refactor> <android-project-dir>")
app, root = sys.argv[1], Path(sys.argv[2]).resolve()
if app == "migrate": migrate(root)
elif app == "refactor": refactor(root)
else: raise SystemExit(f"Unknown app: {app}")
