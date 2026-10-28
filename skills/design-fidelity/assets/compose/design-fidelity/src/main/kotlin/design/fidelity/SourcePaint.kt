package design.fidelity

import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.RoundRect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathFillType
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import kotlin.math.max
import kotlin.math.min

/**
 * Source shapes in design units (dp). Paths are built in pixels at draw time.
 * Semantics match the Flutter `design_fidelity` package and @design-fidelity/react.
 */
sealed interface SourceShape {
    /** Outline of [rect] grown by [grow] px (negative shrinks). */
    fun outline(rect: Rect, density: Float, grow: Float = 0f): Path

    val isClosed: Boolean get() = true

    /** Rect and oval grow exactly; free paths approximate growth with a stroke. */
    val supportsExactGrow: Boolean get() = true
}

data class SourceRectShape(
    /** Corner radii in dp: top-left, top-right, bottom-right, bottom-left. */
    val radii: List<Float> = listOf(0f, 0f, 0f, 0f),
) : SourceShape {
    constructor(all: Float) : this(listOf(all, all, all, all))

    override fun outline(rect: Rect, density: Float, grow: Float): Path {
        fun r(i: Int): CornerRadius {
            val source = min(radii.getOrElse(i) { 0f } * density, min(rect.width, rect.height) / 2f)
            // Radii are clamped on the source rect, then grown with it (concentric spread).
            val value = if (source > 0f || grow > 0f) max(0f, source + grow) else 0f
            return CornerRadius(value, value)
        }
        val grown = rect.inflate(grow)
        return Path().apply {
            addRoundRect(RoundRect(grown, r(0), r(1), r(2), r(3)))
        }
    }
}

object SourceOvalShape : SourceShape {
    override fun outline(rect: Rect, density: Float, grow: Float): Path =
        Path().apply { addOval(rect.inflate(grow)) }
}

/** One vertex in unit coordinates (0..1 of the layer box), Sketch/Figma style. */
data class SourcePathPoint(val point: Offset, val curveFrom: Offset? = null, val curveTo: Offset? = null)

data class SourcePathShape(
    val points: List<SourcePathPoint>,
    val closed: Boolean = true,
    val evenOdd: Boolean = false,
) : SourceShape {
    override val isClosed: Boolean get() = closed
    override val supportsExactGrow: Boolean get() = false

    override fun outline(rect: Rect, density: Float, grow: Float): Path {
        val path = Path().apply { fillType = if (evenOdd) PathFillType.EvenOdd else PathFillType.NonZero }
        if (points.isEmpty()) return path
        fun p(v: Offset) = Offset(rect.left + v.x * rect.width, rect.top + v.y * rect.height)
        val first = p(points.first().point)
        path.moveTo(first.x, first.y)
        val count = if (closed) points.size + 1 else points.size
        for (i in 1 until count) {
            val previous = points[(i - 1) % points.size]
            val current = points[i % points.size]
            val end = p(current.point)
            if (previous.curveFrom != null || current.curveTo != null) {
                val c1 = p(previous.curveFrom ?: previous.point)
                val c2 = p(current.curveTo ?: current.point)
                path.cubicTo(c1.x, c1.y, c2.x, c2.y, end.x, end.y)
            } else {
                path.lineTo(end.x, end.y)
            }
        }
        if (closed) path.close()
        return path
    }
}

data class SourceGradientStop(val position: Float, val color: Color)

/** Linear gradient between two unit points of the layer box. */
data class SourceLinearGradient(val from: Offset, val to: Offset, val stops: List<SourceGradientStop>)

sealed interface SourceFill {
    val opacity: Float

    fun brush(rect: Rect): Brush

    data class Solid(val color: Color, override val opacity: Float = 1f) : SourceFill {
        override fun brush(rect: Rect): Brush = androidx.compose.ui.graphics.SolidColor(scale(color, opacity))
    }

    data class Linear(val gradient: SourceLinearGradient, override val opacity: Float = 1f) : SourceFill {
        override fun brush(rect: Rect): Brush {
            fun p(v: Offset) = Offset(rect.left + v.x * rect.width, rect.top + v.y * rect.height)
            val stops = gradient.stops.map { it.position to scale(it.color, opacity) }.toTypedArray()
            return Brush.linearGradient(*stops, start = p(gradient.from), end = p(gradient.to))
        }
    }
}

internal fun scale(color: Color, opacity: Float): Color =
    if (opacity >= 1f) color else color.copy(alpha = color.alpha * opacity)

enum class SourceBorderPosition { Inside, Center, Outside }

data class SourceBorder(
    /** Stroke width in dp. */
    val thickness: Float,
    val fill: SourceFill,
    val position: SourceBorderPosition = SourceBorderPosition.Center,
    val cap: StrokeCap = StrokeCap.Butt,
    val join: StrokeJoin = StrokeJoin.Miter,
    /** Dash pattern in dp; empty = solid. */
    val dash: List<Float> = emptyList(),
)

data class SourceShadow(
    val color: Color,
    /** Offset in dp. */
    val offset: Offset = Offset.Zero,
    /** Source blur radius in dp; sigma = 0.5 x radius (FidelityEffectMapping). */
    val blurRadius: Float = 0f,
    val spread: Float = 0f,
    val inner: Boolean = false,
)

/**
 * The single place where design effect radii become Gaussian sigmas, and where
 * sigmas become Android framework blur radii.
 *
 * Android's BlurMaskFilter and RenderEffect take a "radius" that Skia converts
 * with sigma = 0.57735 * radius + 0.5; [frameworkRadius] inverts it. Recalibrate
 * here, once, if an on-device comparison shows a different factor.
 */
object FidelityEffectMapping {
    const val SHADOW_SIGMA_PER_RADIUS = 0.5f
    const val LAYER_BLUR_SIGMA_PER_RADIUS = 0.5f
    const val BACKGROUND_BLUR_SIGMA_PER_RADIUS = 0.5f

    fun shadowSigma(radius: Float): Float = if (radius <= 0f) 0f else radius * SHADOW_SIGMA_PER_RADIUS

    fun layerBlurSigma(radius: Float): Float = if (radius <= 0f) 0f else radius * LAYER_BLUR_SIGMA_PER_RADIUS

    fun frameworkRadius(sigma: Float): Float = if (sigma <= 0.5f) 0f else (sigma - 0.5f) / 0.57735f

    /** Visible extent of a Gaussian beyond the source edge (~3 sigma). */
    fun shadowExtent(radius: Float, spread: Float): Float = shadowSigma(radius) * 3f + kotlin.math.abs(spread)
}

internal fun Size.toRect(): Rect = Rect(Offset.Zero, this)
