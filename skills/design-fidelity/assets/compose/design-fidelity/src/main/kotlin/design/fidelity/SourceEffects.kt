package design.fidelity

import android.graphics.BitmapFactory
import android.os.Build
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.BlurredEdgeTreatment
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.CompositingStrategy
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Outline
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** An export frame relative to the node, in design units. */
data class SourceRect(val left: Float, val top: Float, val width: Float, val height: Float)

/** Loads an exported asset from the app's `assets/` folder (no R class needed). */
@Composable
fun rememberSourceAsset(path: String): ImageBitmap {
    val context = LocalContext.current
    return remember(path) {
        context.assets.open(path).use { stream ->
            BitmapFactory.decodeStream(stream)?.asImageBitmap()
                ?: error("Design asset failed to decode: $path")
        }
    }
}

/** An exported source asset, drawn in its export frame (may exceed the node box). */
@Composable
fun SourceAsset(path: String, exportRect: SourceRect? = null, contentDescription: String? = null) {
    val bitmap = rememberSourceAsset(path)
    val attrs = mapOf("data-df-asset" to (exportRect?.let {
        listOf(it.left, it.top, it.width, it.height).joinToString(" ") { v -> fidelityNumber(v) }
    } ?: ""))
    // The generator verified the export rect has the bitmap's aspect at a single
    // density, so filling it is an exact uniform scale.
    val image = Modifier.fidelityBinding(attrs).let {
        if (exportRect == null) it.fillMaxSize()
        else it.sourcePlaced(left = exportRect.left, top = exportRect.top, width = exportRect.width, height = exportRect.height)
    }
    Box(Modifier.fillMaxSize()) {
        Image(bitmap, contentDescription, image, contentScale = ContentScale.FillBounds, filterQuality = FilterQuality.Medium)
    }
}

/** Missing exported asset: same frame, pink, labelled; never a drawn guess. */
@Composable
fun SourcePlaceholder(nodeId: String, label: String = "设计素材未切图") {
    Box(
        Modifier
            .fillMaxSize()
            .fidelityBinding(mapOf("data-df-placeholder" to nodeId))
            .background(Color(0xFFFFE5EA))
            .border(1.dp, Color(0xFFFF4D6D)),
        contentAlignment = Alignment.Center,
    ) {
        BasicText(label, style = TextStyle(fontSize = 10.sp, color = Color(0xFFC52245)))
    }
}

private fun Modifier.fillIf(fill: Boolean): Modifier = if (fill) fillMaxSize() else this

/** Layer opacity composited once (offscreen), like Sketch/Figma layer opacity. */
@Composable
fun SourceOpacity(value: Float, fill: Boolean = true, content: @Composable () -> Unit) {
    Box(
        Modifier.fillIf(fill)
            .fidelityBinding(mapOf("data-df-opacity" to fidelityNumber(value)))
            .graphicsLayer(alpha = value, compositingStrategy = CompositingStrategy.Offscreen),
    ) { content() }
}

@Composable
fun SourceFlip(x: Boolean = false, y: Boolean = false, fill: Boolean = true, content: @Composable () -> Unit) {
    Box(Modifier.fillIf(fill).graphicsLayer(scaleX = if (x) -1f else 1f, scaleY = if (y) -1f else 1f)) { content() }
}

/**
 * Gaussian layer blur (API 31+; older devices draw the layer sharp, which the
 * generator reports). sigma = 0.5 x source radius.
 */
@Composable
fun SourceLayerBlur(radius: Float, fill: Boolean = true, content: @Composable () -> Unit) {
    val density = LocalDensity.current.density
    val sigmaPx = FidelityEffectMapping.layerBlurSigma(radius) * density
    val blurred = if (sigmaPx > 0f && Build.VERSION.SDK_INT >= 31) {
        // Modifier.blur takes the framework radius (Skia: sigma = 0.57735 r + 0.5) in dp.
        Modifier.blur((FidelityEffectMapping.frameworkRadius(sigmaPx) / density).dp, BlurredEdgeTreatment.Unbounded)
    } else Modifier
    Box(Modifier.fillIf(fill).fidelityBinding(mapOf("data-df-layer-blur" to fidelityNumber(radius))).then(blurred)) {
        content()
    }
}

/**
 * Background blur. Compose cannot sample what is drawn behind a node, so this
 * draws the layer itself only; the generator reports the effect as unsupported
 * for Compose and the scene check does not bind it.
 */
@Composable
fun SourceBackdropBlur(radius: Float, shape: SourceShape = SourceRectShape(), saturation: Float = 1f,
                       content: @Composable () -> Unit) {
    Box(Modifier.fillMaxSize()) { content() }
}

/** Compose [Shape] for a source shape (clip to a mask layer). */
class SourceClipShape(private val shape: SourceShape) : Shape {
    override fun createOutline(size: Size, layoutDirection: LayoutDirection, density: Density): Outline =
        Outline.Generic(shape.outline(size.toRect(), density.density))
}

/** Clips the masked members to the mask layer's shape. */
@Composable
fun SourceClip(shape: SourceShape, content: @Composable () -> Unit) {
    val kind = when (shape) {
        is SourceRectShape -> "rect"
        SourceOvalShape -> "oval"
        is SourcePathShape -> "path"
    }
    Box(Modifier.fillMaxSize().fidelityBinding(mapOf("data-df-clip" to kind)).clip(SourceClipShape(shape))) { content() }
}
