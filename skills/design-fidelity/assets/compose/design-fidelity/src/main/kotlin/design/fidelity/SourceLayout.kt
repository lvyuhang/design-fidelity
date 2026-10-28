package design.fidelity

import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.layout.layout
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsPropertyKey
import androidx.compose.ui.semantics.SemanticsPropertyReceiver
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt

// ---------------------------------------------------------------------------
// Bindings read by the scene checks (same attribute names as the web primitives).

val FidelityAttributes = SemanticsPropertyKey<Map<String, String>>("FidelityAttributes") { parent, child ->
    (parent ?: emptyMap()) + child
}
val FidelityBoxParams = SemanticsPropertyKey<SourceBoxParams>("FidelityBoxParams")

var SemanticsPropertyReceiver.fidelityAttributes by FidelityAttributes
var SemanticsPropertyReceiver.fidelityBoxParams by FidelityBoxParams

fun Modifier.fidelityBinding(attributes: Map<String, String>, box: SourceBoxParams? = null): Modifier =
    semantics {
        fidelityAttributes = attributes
        if (box != null) fidelityBoxParams = box
    }

/** Test tag of a source layer: `fidelity:<node id>`. */
fun sourceTag(nodeId: String): String = "fidelity:$nodeId"

// ---------------------------------------------------------------------------
// Placement (Flutter Positioned semantics), in design units (dp).

/**
 * Places the child inside its (bounded) parent box: any of left/top/right/bottom,
 * explicit width/height, or left+right / top+bottom to stretch. Without a size on
 * an axis the child keeps its intrinsic size (auto-width text).
 */
fun Modifier.sourcePlaced(
    left: Float? = null, top: Float? = null, right: Float? = null, bottom: Float? = null,
    width: Float? = null, height: Float? = null,
): Modifier = layout { measurable, constraints ->
    val maxW = constraints.maxWidth
    val maxH = constraints.maxHeight
    fun px(v: Float): Float = v * density
    val w = when {
        width != null -> px(width).roundToInt()
        left != null && right != null && constraints.hasBoundedWidth -> (maxW - px(left) - px(right)).roundToInt().coerceAtLeast(0)
        else -> null
    }
    val h = when {
        height != null -> px(height).roundToInt()
        top != null && bottom != null && constraints.hasBoundedHeight -> (maxH - px(top) - px(bottom)).roundToInt().coerceAtLeast(0)
        else -> null
    }
    val child = measurable.measure(
        Constraints(
            minWidth = w ?: 0, maxWidth = w ?: Constraints.Infinity,
            minHeight = h ?: 0, maxHeight = h ?: Constraints.Infinity,
        ),
    )
    val x = when {
        left != null -> px(left)
        right != null -> maxW - px(right) - child.width
        else -> 0f
    }
    val y = when {
        top != null -> px(top)
        bottom != null -> maxH - px(bottom) - child.height
        else -> 0f
    }
    val reportW = if (constraints.hasBoundedWidth) maxW else child.width
    val reportH = if (constraints.hasBoundedHeight) maxH else child.height
    layout(reportW, reportH) { child.place(x.roundToInt(), y.roundToInt()) }
}

// ---------------------------------------------------------------------------
// Overrides, taps and safe area.

class SceneOverrides(
    val overrides: Map<String, @Composable () -> Unit> = emptyMap(),
    val onTap: Map<String, () -> Unit> = emptyMap(),
)

val LocalSceneOverrides = staticCompositionLocalOf { SceneOverrides() }

/** Safe-area insets in dp; the fidelity harness provides them, apps leave it null. */
data class SourceInsets(val top: Float, val bottom: Float)

val LocalSourceInsets = staticCompositionLocalOf<SourceInsets?> { null }

/** Run-time offsets of root layers: device inset minus design inset. */
data class SceneInsets(val dy: Float, val dyBottom: Float)

/**
 * One source layer. [fill] boxes fill the placed frame; text keeps its
 * intrinsic size. Overrides replace the content inside the same frame.
 */
@Composable
fun SourceNode(id: String, fill: Boolean = true, content: @Composable () -> Unit) {
    val scene = LocalSceneOverrides.current
    val tap = scene.onTap[id]
    var modifier = (if (fill) Modifier.fillMaxSize() else Modifier).testTag(sourceTag(id))
    if (tap != null) {
        modifier = modifier.clickable(
            interactionSource = remember { MutableInteractionSource() }, indication = null, onClick = tap,
        )
    }
    Box(modifier) {
        val override = scene.overrides[id]
        if (override != null) override() else content()
    }
}

/**
 * Full-screen page frame. Root layers move with the safe area, the body
 * scrolls when the screen is shorter than the design, footers stay pinned
 * above the bottom inset. Do not add system-bar padding around it.
 */
@Suppress("UNUSED_PARAMETER")
@Composable
fun SourceScene(
    designWidth: Float,
    designHeight: Float,
    designTop: Float,
    designBottom: Float,
    adaptSafeArea: Boolean = true,
    overrides: Map<String, @Composable () -> Unit> = emptyMap(),
    onTap: Map<String, () -> Unit> = emptyMap(),
    footer: @Composable BoxScope.(SceneInsets) -> Unit = {},
    content: @Composable BoxScope.(SceneInsets) -> Unit,
) {
    val density = LocalDensity.current
    val forced = LocalSourceInsets.current
    val safe = WindowInsets.safeDrawing
    val top = when {
        !adaptSafeArea -> designTop
        forced != null -> forced.top
        else -> safe.getTop(density) / density.density
    }
    val bottom = when {
        !adaptSafeArea -> designBottom
        forced != null -> forced.bottom
        else -> safe.getBottom(density) / density.density
    }
    val insets = SceneInsets(dy = top - designTop, dyBottom = bottom - designBottom)
    CompositionLocalProvider(LocalSceneOverrides provides SceneOverrides(overrides, onTap)) {
        BoxWithConstraints(Modifier.fillMaxSize().clipToBounds()) {
            val natural = designHeight + insets.dy + insets.dyBottom
            val available = if (constraints.hasBoundedHeight) maxHeight.value else natural
            val scrolls = available < natural - 0.5f
            val body = Modifier.fillMaxSize().let { if (scrolls) it.verticalScroll(rememberScrollState()) else it }
            Box(body) {
                Box(Modifier.fillMaxWidth().height((if (scrolls) natural else available).dp)) { content(insets) }
            }
            footer(insets)
        }
    }
}
