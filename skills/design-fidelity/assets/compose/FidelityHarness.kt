// Fidelity render harness for Jetpack Compose (tool code; copied next to the page's
// render test by `page generate` and kept in sync). Robolectric + Compose UI test:
//
//   ./gradlew :app:testDebugUnitTest --tests '*<Page>FidelityTest'
//
// Writes <output> (PNG at the test's density), <output>.geometry.json (schema 1) and
// <output>.variants.json (schema 2) in the same format as the Flutter and web
// harnesses, so the same gate checks all three. `checkScene` runs the scene
// obligations listed in scene.g.json.
//
// Requires (app module, test scope): robolectric, androidx.compose.ui:ui-test-junit4,
// androidx.compose.ui:ui-test-manifest, and
// android.testOptions.unitTests.isIncludeAndroidResources = true.
package fidelity.support

import android.graphics.Bitmap
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsNode
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import design.fidelity.FidelityAttributes
import design.fidelity.FidelityBoxParams
import design.fidelity.LocalSourceInsets
import design.fidelity.SourceBox
import design.fidelity.SourceFonts
import design.fidelity.SourceInsets
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import kotlin.math.abs
import kotlin.math.floor

data class FidelityDevice(val name: String, val width: Float, val height: Float, val top: Float, val bottom: Float)

val fidelityDefaultDevices = listOf(
    FidelityDevice("iphone_se", 375f, 667f, 20f, 0f),
    FidelityDevice("iphone_15", 393f, 852f, 59f, 34f),
    FidelityDevice("iphone_15_pro_max", 430f, 932f, 59f, 34f),
    FidelityDevice("android_compact", 360f, 800f, 24f, 0f),
    FidelityDevice("android_large", 412f, 915f, 24f, 24f),
)

/** Robolectric qualifiers large enough for every device frame, at [scale] px per dp. */
fun fidelityQualifiers(scale: Int): String = "w430dp-h932dp-" + when (scale) {
    1 -> "mdpi"; 2 -> "xhdpi"; 3 -> "xxhdpi"; else -> "xxxhdpi"
}

private const val ROOT = "fidelity-root"

private class Frame(
    val width: Float, val height: Float, val top: Float, val bottom: Float, val fontScale: Float,
    val content: @Composable () -> Unit,
)

object FidelityHarness {
    private var frame by mutableStateOf<Frame?>(null)
    private var installed: ComposeContentTestRule? = null

    fun outputPath(variable: String): String =
        System.getenv(variable) ?: System.getProperty(variable)
            ?: File.createTempFile("design-fidelity-", ".png").path

    /** Registers every design font of the font map under its runtime family. */
    fun loadSourceFontMap(path: String) {
        SourceFonts.useDesignFonts = true
        val file = File(path)
        val fonts = JSONObject(file.readText()).optJSONObject("fonts") ?: return
        val families = mutableMapOf<String, MutableList<Font>>()
        for (label in fonts.keys()) {
            val entry = fonts.getJSONObject(label)
            val family = entry.optString("runtime_family")
            var fontPath = entry.optString("path")
            if (family.isEmpty() || fontPath.isEmpty()) continue
            if (fontPath.startsWith("~/")) fontPath = System.getProperty("user.home") + fontPath.substring(1)
            val resolved = File(fontPath).let { if (it.isAbsolute) it else File(file.parentFile, fontPath) }
            val weight = label.substringAfterLast('@').toIntOrNull() ?: 400
            families.getOrPut(family) { mutableListOf() }.add(Font(resolved, FontWeight(weight)))
        }
        for ((family, list) in families) SourceFonts.register(family, FontFamily(list))
    }

    private fun install(rule: ComposeContentTestRule) {
        if (installed === rule) return
        rule.setContent { Host() }
        installed = rule
    }

    @Composable
    private fun Host() {
        val f = frame ?: return
        val base = LocalDensity.current
        CompositionLocalProvider(
            LocalDensity provides Density(base.density, f.fontScale),
            LocalSourceInsets provides SourceInsets(f.top, f.bottom),
        ) {
            Box(Modifier.testTag(ROOT).requiredSize(f.width.dp, f.height.dp)) { f.content() }
        }
    }

    private fun show(rule: ComposeContentTestRule, next: Frame): Throwable? {
        install(rule)
        frame = next
        return try {
            rule.waitForIdle(); null
        } catch (error: Throwable) {
            error
        }
    }

    private fun density(rule: ComposeContentTestRule): Float = rule.density.density

    private fun capture(rule: ComposeContentTestRule): Bitmap =
        rule.onNodeWithTag(ROOT, useUnmergedTree = true).captureToImage().asAndroidBitmap()

    private fun root(rule: ComposeContentTestRule): SemanticsNode =
        rule.onNodeWithTag(ROOT, useUnmergedTree = true).fetchSemanticsNode()

    private fun tagged(rule: ComposeContentTestRule): List<SemanticsNode> = rule.onAllNodes(
        SemanticsMatcher("fidelity node") { it.config.getOrNull(SemanticsProperties.TestTag)?.startsWith("fidelity:") == true },
        useUnmergedTree = true,
    ).fetchSemanticsNodes()

    private fun descendants(node: SemanticsNode): List<SemanticsNode> =
        node.children.flatMap { listOf(it) + descendants(it) }

    private fun rect(r: Rect, origin: Rect, d: Float) =
        JSONArray(listOf((r.left - origin.left) / d, (r.top - origin.top) / d, r.width / d, r.height / d).map { it.toDouble() })

    private fun geometry(rule: ComposeContentTestRule): Triple<JSONObject, JSONObject, Boolean> {
        val d = density(rule)
        val origin = root(rule).boundsInRoot
        val nodes = JSONObject()
        val text = JSONObject()
        for (node in tagged(rule)) {
            val id = node.config[SemanticsProperties.TestTag].removePrefix("fidelity:")
            nodes.put(id, rect(node.boundsInRoot, origin, d))
            val paragraphs = (listOf(node) + descendants(node)).filter {
                it.config.getOrNull(FidelityAttributes)?.containsKey("data-df-text") == true ||
                    it.config.getOrNull(SemanticsProperties.Text) != null
            }
            if (paragraphs.isNotEmpty()) {
                val union = paragraphs.map { it.boundsInRoot }.reduce { a, b ->
                    Rect(minOf(a.left, b.left), minOf(a.top, b.top), maxOf(a.right, b.right), maxOf(a.bottom, b.bottom))
                }
                text.put(id, rect(union, origin, d))
            }
        }
        val scrollable = (listOf(root(rule)) + descendants(root(rule))).any {
            val range = it.config.getOrNull(SemanticsProperties.VerticalScrollAxisRange)
            range != null && range.maxValue() > 0.5f
        }
        return Triple(nodes, text, scrollable)
    }

    private fun writeJson(path: String, value: JSONObject) {
        File(path).apply { parentFile?.mkdirs() }.writeText(value.toString(1))
    }

    /** Renders [page] at the design size and safe area; writes the PNG and geometry. */
    fun capturePage(
        rule: ComposeContentTestRule, output: String, width: Float, height: Float, top: Float, bottom: Float,
        page: @Composable () -> Unit,
    ) {
        show(rule, Frame(width, height, top, bottom, 1f, page))?.let { throw it }
        val (nodes, text, _) = geometry(rule)
        if (nodes.length() > 0) {
            writeJson("$output.geometry.json", JSONObject().put("schema", 1)
                .put("canvas", JSONArray(listOf(width.toDouble(), height.toDouble())))
                .put("nodes", nodes).put("text_nodes", text))
        }
        File(output).apply { parentFile?.mkdirs() }.outputStream().use { capture(rule).compress(Bitmap.CompressFormat.PNG, 100, it) }
    }

    /** Lays the page out on each device frame at each text scale (fontScale). */
    fun captureVariants(
        rule: ComposeContentTestRule, output: String, devices: List<FidelityDevice> = fidelityDefaultDevices,
        textScales: List<Float> = listOf(1.0f, 1.3f), page: @Composable () -> Unit,
    ) {
        val variants = JSONArray()
        for (device in devices) for (scale in textScales) {
            val error = show(rule, Frame(device.width, device.height, device.top, device.bottom, scale, page))
            val (nodes, text, scrollable) = if (error == null) geometry(rule) else Triple(JSONObject(), JSONObject(), false)
            variants.put(JSONObject().put("device", device.name).put("width", device.width.toDouble())
                .put("height", device.height.toDouble())
                .put("padding", JSONObject().put("top", device.top.toDouble()).put("bottom", device.bottom.toDouble()))
                .put("text_scale", scale.toDouble()).put("exception", error?.toString() ?: JSONObject.NULL)
                .put("scrollable", scrollable).put("nodes", nodes).put("text_nodes", text))
        }
        writeJson("$output.variants.json", JSONObject().put("schema", 2).put("variants", variants))
    }

    // -----------------------------------------------------------------------
    // Scene obligations (scene.g.json, shared with the web harness).

    fun checkScene(rule: ComposeContentTestRule, specPath: String, top: Float, bottom: Float, scene: @Composable () -> Unit) {
        val spec = JSONObject(File(specPath).readText())
        val canvas = spec.getJSONArray("canvas")
        val width = canvas.getDouble(0).toFloat()
        val height = canvas.getDouble(1).toFloat()
        val failures = mutableListOf<String>()
        fun showScene() = show(rule, Frame(width, height, top, bottom, 1f, scene))?.let { throw it }
        showScene()
        var scenePixels: Bitmap? = null
        val checks = spec.getJSONArray("checks")
        for (i in 0 until checks.length()) {
            val check = checks.getJSONObject(i)
            val label = "${check.getString("kind")}: ${check.getString("id")}"
            check.optJSONArray("bound")?.let { list ->
                for (j in 0 until list.length()) bound(rule, list.getJSONObject(j))?.let { failures += "$label: $it" }
            }
            check.optJSONArray("clipped")?.let { list ->
                for (j in 0 until list.length()) {
                    val id = list.getString(j)
                    if (!clipped(rule, id)) failures += "$label: $id is not clipped by its mask shape"
                }
            }
            check.optJSONObject("pixel")?.let { pixel ->
                val image = scenePixels ?: capture(rule).also { scenePixels = it }
                val d = density(rule)
                val at = pixel.getJSONArray("at")
                val x = floor(at.getDouble(0) * d + d / 2).toInt()
                val y = floor(at.getDouble(1) * d + d / 2).toInt()
                val got = rgb(image, x, y)
                val want = (0 until 3).map { pixel.getJSONArray("rgb").getInt(it) }
                if (diff(got, want) > pixel.getInt("tolerance")) failures += "$label: composited fills $got, source $want"
            }
            check.optJSONObject("band")?.let { band ->
                borderBand(rule, band)?.let { failures += "$label: $it" }
                showScene()
                scenePixels = null
            }
        }
        if (failures.isNotEmpty()) throw AssertionError("Scene obligations failed:\n" + failures.joinToString("\n"))
    }

    private fun nodeAndDescendants(rule: ComposeContentTestRule, id: String): List<SemanticsNode>? {
        val node = tagged(rule).firstOrNull { it.config[SemanticsProperties.TestTag] == "fidelity:$id" } ?: return null
        return listOf(node) + descendants(node)
    }

    private fun bound(rule: ComposeContentTestRule, spec: JSONObject): String? {
        val id = spec.getString("node")
        val attr = spec.getString("attr")
        val nodes = nodeAndDescendants(rule, id) ?: return "$id: node not rendered"
        val candidates = nodes.mapNotNull { it.config.getOrNull(FidelityAttributes) }.filter { it.containsKey(attr) }
        if (candidates.isEmpty()) return "$id: does not render through $attr"
        val equals = spec.optJSONObject("equals") ?: return null
        val wanted = equals.keys().asSequence().associateWith { equals.getString(it) }
        if (candidates.any { c -> wanted.all { (k, v) -> c[k] == v } }) return null
        return "$id: expected $wanted, found ${candidates.map { c -> wanted.keys.associateWith { c[it] } }}"
    }

    private fun clipped(rule: ComposeContentTestRule, id: String): Boolean {
        var node: SemanticsNode? = tagged(rule).firstOrNull { it.config[SemanticsProperties.TestTag] == "fidelity:$id" }
        while (node != null) {
            if (node.config.getOrNull(FidelityAttributes)?.containsKey("data-df-clip") == true) return true
            node = node.parent
        }
        return false
    }

    /** Renders the node's SourceBox on mid-grey with and without its border (same probe as Flutter). */
    private fun borderBand(rule: ComposeContentTestRule, band: JSONObject): String? {
        val id = band.getString("node")
        val params = nodeAndDescendants(rule, id)?.firstNotNullOfOrNull { it.config.getOrNull(FidelityBoxParams) }
            ?: return "$id: no SourceBox to probe"
        val t = band.getDouble("thickness").toFloat()
        val size = band.getJSONArray("size")
        val w = size.getDouble(0).toFloat()
        val h = size.getDouble(1).toFloat()
        val margin = t * 2 + 4
        fun probe(withBorder: Boolean): Bitmap {
            val box = if (withBorder) params else params.copy(borders = emptyList())
            show(rule, Frame(w + margin * 2, h + margin * 2, 0f, 0f, 1f) {
                Box(Modifier.background(Color(0xFF808080)).padding(margin.dp)) {
                    Box(Modifier.requiredSize(w.dp, h.dp)) {
                        SourceBox(shape = box.shape, fills = box.fills, borders = box.borders, opacity = box.opacity)
                    }
                }
            })?.let { throw it }
            return capture(rule)
        }
        val bordered = probe(true)
        val plain = probe(false)
        val ratio = density(rule)
        val y = floor((margin + h / 2) * ratio).toInt()
        fun px(x: Float) = floor(x * ratio).toInt()
        val position = band.getString("position")
        val at = when (position) { "inside" -> margin + t / 2; "center" -> margin; else -> margin - t / 2 }
        if (diff(rgb(bordered, px(at), y), rgb(plain, px(at), y)) <= 2) return "$id: border band must be painted at $at"
        val outsideEdge = when (position) { "inside" -> margin - 1.5f; "center" -> margin - t / 2 - 1.5f; else -> margin - t - 1.5f }
        val insideEdge = when (position) { "inside" -> margin + t + 1.5f; "center" -> margin + t / 2 + 1.5f; else -> margin + 1.5f }
        for (x in listOf(outsideEdge, insideEdge)) {
            if (diff(rgb(bordered, px(x), y), rgb(plain, px(x), y)) > 2) return "$id: border must not leak to $x"
        }
        return null
    }

    private fun rgb(image: Bitmap, x: Int, y: Int): List<Int> {
        val c = image.getPixel(x.coerceIn(0, image.width - 1), y.coerceIn(0, image.height - 1))
        return listOf((c shr 16) and 255, (c shr 8) and 255, c and 255)
    }

    private fun diff(a: List<Int>, b: List<Int>): Int = a.indices.maxOf { abs(a[it] - b[it]) }
}
