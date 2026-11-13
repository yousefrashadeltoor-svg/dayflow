#!/usr/bin/env python3
"""Verified CI-only source repairs for the two Dayflow Android projects."""
from pathlib import Path
import shutil
import sys

def edit(path, old, new, label, required=True):
    path = Path(path)
    if not path.is_file():
        raise SystemExit(f"[{label}] Missing file: {path}")
    source = path.read_text(encoding="utf-8")
    if old not in source:
        if new and new in source:
            return
        if required:
            raise SystemExit(f"[{label}] Expected source fragment not found: {path}")
        return
    path.write_text(source.replace(old, new), encoding="utf-8")
    print(f"[{label}] Patched {path.name}")

def add_import(path, line, anchor, label):
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    if line in lines:
        return
    anchor_text = anchor.strip()
    try:
        index = next(i for i, item in enumerate(lines) if item.strip() == anchor_text)
    except StopIteration:
        raise SystemExit(f"[{label}] Import anchor missing: {path}")
    lines.insert(index + 1, line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def remove_import(path, line):
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    lines = [item for item in source.splitlines() if item.strip() != line.strip()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

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


    # Alarm/calendar/robot model compile fixes.
    add_import(b/"alarm/AlarmScheduler.kt", "import app.dayflow.android.notify.Reminders",
               "import app.dayflow.android.data.Store\n", tag)
    edit(b/"calendar/Calendars.kt",
         "return CalParts(h.get(java.time.temporal.ChronoField.YEAR_OF_ERA), h.monthValue, h.dayOfMonth)",
         "return CalParts(h.get(java.time.temporal.ChronoField.YEAR_OF_ERA), h.get(java.time.temporal.ChronoField.MONTH_OF_YEAR), h.get(java.time.temporal.ChronoField.DAY_OF_MONTH))", tag)
    edit(b/"companion/RobotModel.kt",
         "class Chain(anchorX: Float, anchorY: Float, segs: Int, len: Float, val kx: Float = 0f, val ky: Float = 0f) {",
         "class Chain(anchorX: Float, anchorY: Float, segs: Int, len: Float, val kx: Float = 0f, val ky: Float = 0f) {\n        private val segmentLength = len", tag)
    edit(b/"companion/RobotModel.kt", "private fun i(n: Int) = n * len",
         "private fun i(n: Int) = n.toFloat() * segmentLength", tag)
    overlay = b/"companion/RobotOverlayService.kt"
    add_import(overlay, "import androidx.compose.ui.graphics.drawscope.scale",
               "import androidx.compose.ui.graphics.Color\n", tag)
    edit(overlay, "val h0 = histPos.peekFirst()", "val h0 = histPos.firstOrNull()", tag)
    edit(overlay, "androidx.compose.ui.graphics.drawscope.scale(scale, scale, pivot = androidx.compose.ui.geometry.Offset.Zero)",
         "scale(scale, scale, pivot = androidx.compose.ui.geometry.Offset.Zero)", tag)
    edit(overlay, "val scale = size.width / (120f * 0.9f)",
         "val robotScale = size.width / (120f * 0.9f)", tag)
    edit(overlay, "scale(scale, scale, pivot = androidx.compose.ui.geometry.Offset.Zero)",
         "scale(robotScale, robotScale, pivot = androidx.compose.ui.geometry.Offset.Zero)", tag)

    # Replace the invalid canvas transform setup; Compose transforms require nested draw blocks.
    canvas = b/"decor/DecorCanvas.kt"
    cs = canvas.read_text(encoding="utf-8")
    begin = cs.find("    private fun DrawScope.drawParticle(")
    finish = cs.find("    private fun DrawScope.drawShape(", begin)
    if begin < 0 or finish < 0:
        raise SystemExit("[migrate] DecorCanvas drawParticle boundaries not found")
    draw_particle = """    private fun DrawScope.drawParticle(f: Family, p: Seed, ms: Long) {
        val t = ((ms / 1000f + p.delay) % p.dur + p.dur) % p.dur / p.dur
        val alpha = when {
            t < 0.08f -> t / 0.08f
            t > 0.9f -> (1f - t) / 0.1f
            else -> 1f
        } * p.o
        val st = Patterns.FAMILY[f] ?: return
        val x0 = size.width * (if (f == Family.autumn) 0.55f + p.x * 0.0045f else p.x / 100f)
        val s = p.size
        when (MOTION[f] ?: Motion.FLOAT) {
            Motion.FALL -> {
                val tr = Track.fall(p.dx)
                val pos = tr.offset(t, p.dx, size.height, 0f)
                val flip = abs(cos(t * 4f * PI.toFloat()))
                translate(x0 + pos.x, pos.y * size.height) {
                    rotate(tr.angle(t), Offset.Zero) {
                        scale(scaleX = 0.35f + 0.65f * flip, scaleY = 1f, pivot = Offset.Zero) {
                            drawShape(f, s, alpha, st, p.variant, t)
                        }
                    }
                }
            }
            Motion.FLOAT -> {
                val tr = Track.floatUp(p.dx)
                val pos = tr.offset(t, p.dx, size.height, 0f)
                translate(x0 + pos.x, size.height + 60f + pos.y * size.height / 100f) {
                    drawShape(f, s, alpha, st, p.variant, t)
                }
            }
            Motion.DRIFT -> {
                val x = x0 - size.width * 0.1f + t * (size.width * 0.1f + p.dx * 3f)
                val y = size.height * 0.5f * t + sin(t * PI.toFloat() * 2f) * 26f
                translate(x, y + s) {
                    rotate(sin(t * 6f) * 18f - 10f, Offset.Zero) {
                        drawShape(f, s, alpha, st, p.variant, t)
                    }
                }
            }
            Motion.RAIN -> translate(x0 + t * p.dx * 0.25f, size.height * -0.1f + size.height * 1.2f * t) {
                drawShape(f, s, alpha, st, p.variant, t)
            }
            Motion.FIREFLY -> translate(
                x0 + sin(t * 4f * PI.toFloat()) * 30f,
                size.height * (0.25f + 0.6f * ((p.delay % 1f + 1f) % 1f)) + cos(t * 2f * PI.toFloat()) * 30f,
            ) {
                drawShape(f, s, alpha, st, p.variant, t)
            }
        }
    }

"""
    canvas.write_text(cs[:begin] + draw_particle + cs[finish:], encoding="utf-8")
    remove_import(canvas, "import androidx.compose.ui.graphics.withSave")
    edit(canvas,
         """                    rotate(t * 720f, Offset.Zero)
                    drawRect(col, topLeft = Offset(-s * 0.14f, -s * 0.05f), size = androidx.compose.ui.geometry.Size(s * 0.28f, s * 0.1f), alpha = alpha)""",
         """                    rotate(t * 720f, Offset.Zero) {
                        drawRect(col, topLeft = Offset(-s * 0.14f, -s * 0.05f), size = androidx.compose.ui.geometry.Size(s * 0.28f, s * 0.1f), alpha = alpha)
                    }""", tag)
    edit(canvas,
         """                    rotate(t * 540f, Offset.Zero)
                    scale(scaleX = 0.4f + 0.6f * abs(cos(t * 8 * PI.toFloat())), scaleY = 1f, pivot = Offset.Zero) {
                        drawRect(c, topLeft = Offset(-s * 0.16f, -s * 0.06f), size = androidx.compose.ui.geometry.Size(s * 0.32f, s * 0.12f), alpha = alpha)
                    }""",
         """                    rotate(t * 540f, Offset.Zero) {
                        scale(scaleX = 0.4f + 0.6f * abs(cos(t * 8 * PI.toFloat())), scaleY = 1f, pivot = Offset.Zero) {
                            drawRect(c, topLeft = Offset(-s * 0.16f, -s * 0.06f), size = androidx.compose.ui.geometry.Size(s * 0.32f, s * 0.12f), alpha = alpha)
                        }
                    }""", tag)
    edit(b/"patterns/Patterns.kt", "wave(s, s * 0.05f, 2, 0f,",
         "wave(s, s * 0.05f, 2f, 0f,", tag)

    # Respect nullable OkHttp response bodies and coroutine cancellation state.
    dl = b/"download/DownloadService.kt"
    ds = dl.read_text(encoding="utf-8")
    ds = ds.replace("val body = r.body", 'val body = r.body ?: throw IllegalStateException("استجابة التنزيل بدون محتوى")')
    ds = ds.replace("r.body.string()", 'r.body?.string() ?: throw IllegalStateException("استجابة HLS فارغة")')
    ds = ds.replace("r.body.bytes()", 'r.body?.bytes() ?: throw IllegalStateException("مقطع HLS فارغ")')
    dl.write_text(ds, encoding="utf-8")
    add_import(dl, "import kotlinx.coroutines.isActive", "import kotlinx.coroutines.launch\n", tag)
    edit(dl, "private fun isActive(scope: CoroutineScope) = true",
         "private fun isActive(scope: CoroutineScope) = scope.isActive", tag)
    la = b/"download/LinkAnalyzer.kt"
    ls = la.read_text(encoding="utf-8")
    ls = ls.replace("}.distinct()", "}.distinct().toList()", 1)
    ls = ls.replace("r.body.string()", 'r.body?.string() ?: throw IllegalStateException("استجابة فارغة")')
    ls = ls.replace("r.body.byteStream()", '(r.body ?: throw IllegalStateException("استجابة فارغة")).byteStream()')
    ls = ls.replace("r.body.contentType()", "r.body?.contentType()")
    la.write_text(ls, encoding="utf-8")

    # Reminders is declared in notify package, not alarm package.
    remove_import(b/"notify/Notifications.kt", "import app.dayflow.android.alarm.Reminders")

    # Stable seeded PRNG without JavaScript-only runtime APIs.
    pat = b/"patterns/Patterns.kt"
    ps = pat.read_text(encoding="utf-8")
    a = ps.find("    /** Deterministic PRNG")
    z = ps.find("    fun star(", a)
    if a < 0 or z < 0: raise SystemExit("[migrate] PRNG function boundaries not found")
    ps = ps[:a] + """    /** Deterministic seeded PRNG for decoration placement. */
    fun mulberry32(seed0: Int): () -> Float {
        val random = java.util.Random(seed0.toLong())
        return { random.nextFloat() }
    }

""" + ps[z:]
    ps = ps.replace("cx - s / 2", "cx - s / 2f")
    ps = ps.replace("val st = FAMILY[f]", "val st = FAMILY[f] ?: return")
    pat.write_text(ps, encoding="utf-8")

    alarms = b/"ui/screens/AlarmsScreen.kt"
    add_import(alarms, "import androidx.compose.foundation.layout.size",
               "import androidx.compose.foundation.layout.padding\n", tag)
    add_import(alarms, "import androidx.compose.foundation.layout.heightIn",
               "import androidx.compose.foundation.layout.height\n", tag)
    caltools = b/"ui/screens/CalendarTools.kt"
    remove_import(caltools, "import androidx.compose.material.icons.filled.Countdown")
    edit(caltools, "Icons.Filled.Countdown", "Icons.Filled.Timer", tag)
    remove_import(b/"ui/screens/MeScreen.kt", "import app.dayflow.android.widget.WidgetCatalogView")
    wp = b/"widget/WidgetPainter.kt"
    wp.write_text(wp.read_text(encoding="utf-8").replace("0xCCFFFFFF", "0xCCFFFFFF.toInt()"), encoding="utf-8")
    ui = b/"ui/UiKit.kt"
    add_import(ui, "import androidx.compose.material3.ExperimentalMaterial3Api",
               "import androidx.compose.material3.Text", tag)
    ui_lines = ui.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(ui_lines):
        if line.strip() == "fun Honest(text: String) {":
            if index == 0 or ui_lines[index - 1].strip() != "@Composable":
                raise SystemExit("[migrate] Honest() must retain its @Composable annotation")
            if index < 2 or "ExperimentalMaterial3Api" not in ui_lines[index - 2]:
                ui_lines.insert(index - 1, "@OptIn(ExperimentalMaterial3Api::class)")
            break
    else:
        raise SystemExit("[migrate] Honest() declaration not found")
    ui.write_text("\n".join(ui_lines) + "\n", encoding="utf-8")
    print("[migrate] Applied calendar, robot, downloader, notification, icon, layout and opt-in fixes")

def refactor(p):
    tag = "refactor"
    styles = p/"app/src/main/res/values/styles.xml"
    styles_lines = styles.read_text(encoding="utf-8").splitlines()
    styles_lines = [line for line in styles_lines if 'name="android:windowLightNavigationBar"' not in line]
    styles.write_text("\n".join(styles_lines) + "\n", encoding="utf-8")
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
