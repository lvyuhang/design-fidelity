package design.fidelity

import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.PlatformTextStyle
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.sp

/** A source text style in design units; production fonts are chosen per platform. */
data class SourceTextSpec(
    /** Design (fidelity) family, registered from the font map during fidelity renders. */
    val family: String,
    /** Production family per platform ("android"); null = system font, absent key = [family]. */
    val platforms: Map<String, String?> = emptyMap(),
    val size: Float,
    val weight: Int = 400,
    /** Absolute line height in design units; null = font default. */
    val lineHeight: Float? = null,
    val letterSpacing: Float = 0f,
    val color: Color,
    val decoration: TextDecoration? = null,
)

/**
 * Font families by name. The fidelity harness registers the design fonts from
 * the font map and sets [useDesignFonts]; the app registers any licensed
 * production family it maps in font-map.json (`"android": "AppNumber"`).
 */
object SourceFonts {
    @Volatile var useDesignFonts: Boolean = false
    private val families = mutableMapOf<String, FontFamily>()

    fun register(name: String, family: FontFamily) {
        synchronized(families) { families[name] = family }
    }

    fun family(spec: SourceTextSpec): FontFamily {
        val name = if (useDesignFonts || !spec.platforms.containsKey("android")) spec.family
        else spec.platforms["android"] ?: return FontFamily.Default
        return synchronized(families) { families[name] } ?: FontFamily.Default
    }
}

/**
 * Text style for a source text run: absolute line height with even leading
 * (half above, half below, as in Sketch/Figma), explicit letter spacing, no font
 * padding, no ambient style. sp units keep the system font scale; the fidelity
 * harness pins it to 1.0 for the reference render.
 */
fun sourceTextStyle(spec: SourceTextSpec, strut: SourceTextSpec = spec): TextStyle = TextStyle(
    fontFamily = SourceFonts.family(spec),
    fontSize = spec.size.sp,
    fontWeight = FontWeight(spec.weight),
    fontStyle = FontStyle.Normal,
    lineHeight = strut.lineHeight?.sp ?: TextUnit.Unspecified,
    letterSpacing = spec.letterSpacing.sp,
    color = spec.color,
    textDecoration = spec.decoration ?: TextDecoration.None,
    lineHeightStyle = LineHeightStyle(alignment = LineHeightStyle.Alignment.Center, trim = LineHeightStyle.Trim.None),
    platformStyle = PlatformTextStyle(includeFontPadding = false),
)

private fun spanStyle(spec: SourceTextSpec): SpanStyle = SpanStyle(
    fontFamily = SourceFonts.family(spec),
    fontSize = spec.size.sp,
    fontWeight = FontWeight(spec.weight),
    letterSpacing = spec.letterSpacing.sp,
    color = spec.color,
    textDecoration = spec.decoration ?: TextDecoration.None,
)

/**
 * Text that reproduces a source text box. Auto-width source text stays on one
 * line ([wrap] false); fixed-width boxes wrap. The paragraph line height (from
 * [style]) fixes every line box, also for mixed runs, like a forced strut.
 */
@Composable
fun SourceText(
    text: String,
    style: SourceTextSpec,
    modifier: Modifier = Modifier,
    align: TextAlign = TextAlign.Left,
    wrap: Boolean = false,
) {
    BasicText(
        text = text,
        modifier = modifier.fidelityBinding(mapOf("data-df-text" to "")),
        style = sourceTextStyle(style).copy(textAlign = align),
        softWrap = wrap,
        overflow = TextOverflow.Visible,
    )
}

@Composable
fun SourceText(
    runs: List<Pair<String, SourceTextSpec>>,
    style: SourceTextSpec,
    modifier: Modifier = Modifier,
    align: TextAlign = TextAlign.Left,
    wrap: Boolean = false,
) {
    val text: AnnotatedString = buildAnnotatedString {
        for ((chunk, spec) in runs) withStyle(spanStyle(spec)) { append(chunk) }
    }
    BasicText(
        text = text,
        modifier = modifier.fidelityBinding(mapOf("data-df-text" to "")),
        style = sourceTextStyle(style).copy(textAlign = align),
        softWrap = wrap,
        overflow = TextOverflow.Visible,
    )
}
