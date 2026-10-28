package design.fidelity

import android.graphics.BlurMaskFilter
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.ClipOp
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.PaintingStyle
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.PathFillType
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import kotlin.math.abs
import kotlin.math.max

/** Everything a source shape layer paints; also exposed to the scene checks. */
data class SourceBoxParams(
    val shape: SourceShape = SourceRectShape(),
    val fills: List<SourceFill> = emptyList(),
    val borders: List<SourceBorder> = emptyList(),
    val shadows: List<SourceShadow> = emptyList(),
    val opacity: Float = 1f,
)

/**
 * A source shape layer: outer shadows, fills, inner shadows, borders. Fills its box.
 *
 * * inside / center / outside borders keep the fill geometry unchanged;
 * * outer shadows are knocked out under the shape (not tinted through translucent fills);
 * * shadow spread grows the casting outline before blurring;
 * * layer opacity applies to the composited layer, not per paint, and does not clip shadows.
 */
@Composable
fun SourceBox(
    modifier: Modifier = Modifier,
    shape: SourceShape = SourceRectShape(),
    fills: List<SourceFill> = emptyList(),
    borders: List<SourceBorder> = emptyList(),
    shadows: List<SourceShadow> = emptyList(),
    opacity: Float = 1f,
) {
    val params = SourceBoxParams(shape, fills, borders, shadows, opacity)
    Spacer(
        modifier
            .fillMaxSize()
            .fidelityBinding(params.attributes(), params)
            .drawBehind { drawSourceBox(params) },
    )
}

internal fun SourceBoxParams.attributes(): Map<String, String> = mapOf(
    "data-df-box" to when (shape) {
        is SourceRectShape -> "rect"
        SourceOvalShape -> "oval"
        is SourcePathShape -> "path"
    },
    "data-df-fills" to fills.size.toString(),
    "data-df-shadows" to shadows.size.toString(),
    "data-df-borders" to borders.joinToString(" ") {
        val position = if (shape.isClosed) it.position else SourceBorderPosition.Center
        "${fidelityNumber(it.thickness)}:${position.name.lowercase()}"
    },
)

fun DrawScope.drawSourceBox(params: SourceBoxParams) {
    if (params.opacity <= 0f) return
    val rect = size.toRect()
    val d = density
    val outline = params.shape.outline(rect, d)
    drawIntoCanvas { canvas ->
        val grouped = params.opacity < 1f
        if (grouped) {
            canvas.saveLayer(rect.inflate(paintExtent(params) * d), Paint().apply { alpha = params.opacity })
        }
        for (shadow in params.shadows) if (!shadow.inner) outerShadow(canvas, rect, outline, params.shape, shadow, d)
        for (fill in params.fills) {
            val paint = Paint().apply { isAntiAlias = true }
            fill.brush(rect).applyTo(size, paint, 1f)
            canvas.drawPath(outline, paint)
        }
        for (shadow in params.shadows) if (shadow.inner) innerShadow(canvas, rect, outline, params.shape, shadow, d)
        for (border in params.borders) border(canvas, rect, outline, params.shape, border, d, size)
        if (grouped) canvas.restore()
    }
}

private fun paintExtent(params: SourceBoxParams): Float {
    var extent = 0f
    for (s in params.shadows) if (!s.inner) {
        extent = max(extent, FidelityEffectMapping.shadowExtent(s.blurRadius, s.spread) + max(abs(s.offset.x), abs(s.offset.y)))
    }
    for (b in params.borders) extent = max(extent, b.thickness)
    return extent + 2f
}

private fun blurPaint(shadow: SourceShadow, d: Float): Paint = Paint().apply {
    isAntiAlias = true
    color = shadow.color
    val sigma = FidelityEffectMapping.shadowSigma(shadow.blurRadius) * d
    val radius = FidelityEffectMapping.frameworkRadius(sigma)
    if (radius > 0f) asFrameworkPaint().maskFilter = BlurMaskFilter(radius, BlurMaskFilter.Blur.NORMAL)
}

private fun outerShadow(canvas: Canvas, rect: Rect, outline: Path, shape: SourceShape, shadow: SourceShadow, d: Float) {
    val offset = Offset(shadow.offset.x * d, shadow.offset.y * d)
    val spread = shadow.spread * d
    val extent = (FidelityEffectMapping.shadowExtent(shadow.blurRadius, shadow.spread) +
        max(abs(shadow.offset.x), abs(shadow.offset.y)) + 2f) * d
    canvas.save()
    // Knock out the shape interior: the shadow only exists outside the shape.
    canvas.clipPath(outline, ClipOp.Difference)
    val paint = blurPaint(shadow, d)
    if (shape.supportsExactGrow || spread == 0f) {
        canvas.drawPath(shape.outline(rect.translate(offset), d, spread), paint)
    } else {
        // Free paths grow with a round stroke; one layer keeps the alpha single.
        canvas.saveLayer(rect.inflate(extent), Paint().apply { alpha = shadow.color.alpha })
        val solid = blurPaint(shadow.copy(color = shadow.color.copy(alpha = 1f)), d)
        val moved = shape.outline(rect.translate(offset), d)
        canvas.drawPath(moved, solid)
        if (spread > 0f) {
            canvas.drawPath(moved, solid.apply {
                style = PaintingStyle.Stroke
                strokeWidth = spread * 2f
                strokeJoin = StrokeJoin.Round
                strokeCap = StrokeCap.Round
            })
        }
        canvas.restore()
    }
    canvas.restore()
}

private fun innerShadow(canvas: Canvas, rect: Rect, outline: Path, shape: SourceShape, shadow: SourceShadow, d: Float) {
    val offset = Offset(shadow.offset.x * d, shadow.offset.y * d)
    val extent = (FidelityEffectMapping.shadowExtent(shadow.blurRadius, shadow.spread) +
        max(abs(shadow.offset.x), abs(shadow.offset.y)) + 2f) * d
    val hole = shape.outline(rect.translate(offset), d, if (shape.supportsExactGrow) -shadow.spread * d else 0f)
    // Solid surround minus the offset (shrunk) shape, blurred, clipped to the shape.
    val ring = Path().apply {
        fillType = PathFillType.EvenOdd
        addRect(rect.inflate(extent))
        addPath(hole)
    }
    canvas.save()
    canvas.clipPath(outline)
    canvas.drawPath(ring, blurPaint(shadow, d))
    canvas.restore()
}

private fun border(
    canvas: Canvas, rect: Rect, outline: Path, shape: SourceShape, border: SourceBorder, d: Float,
    size: androidx.compose.ui.geometry.Size,
) {
    if (border.thickness <= 0f) return
    val position = if (shape.isClosed) border.position else SourceBorderPosition.Center
    val width = border.thickness * d * if (position == SourceBorderPosition.Center) 1f else 2f
    val paint = Paint().apply {
        isAntiAlias = true
        style = PaintingStyle.Stroke
        strokeWidth = width
        strokeCap = border.cap
        strokeJoin = border.join
        if (border.dash.isNotEmpty()) {
            pathEffect = PathEffect.dashPathEffect(border.dash.map { it * d }.toFloatArray(), 0f)
        }
    }
    border.fill.brush(rect).applyTo(size, paint, 1f)
    canvas.save()
    when (position) {
        SourceBorderPosition.Inside -> canvas.clipPath(outline)
        SourceBorderPosition.Outside -> canvas.clipPath(outline, ClipOp.Difference)
        SourceBorderPosition.Center -> Unit
    }
    canvas.drawPath(outline, paint)
    canvas.restore()
}

/** Same compact number format as the generators (`1`, `0.5`, `1.25`). */
internal fun fidelityNumber(value: Float): String {
    val text = String.format(java.util.Locale.ROOT, "%.4f", value).trimEnd('0').trimEnd('.')
    return if (text == "-0" || text.isEmpty()) "0" else text
}
