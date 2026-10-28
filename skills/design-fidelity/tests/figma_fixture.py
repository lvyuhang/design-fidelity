"""A synthetic /v1/files/:key/nodes response shaped like real Figma REST output."""

FRAME_X, FRAME_Y = 1000.0, -200.0


def box(x, y, w, h):
    return {'x': FRAME_X + x, 'y': FRAME_Y + y, 'width': w, 'height': h}


def solid(r, g, b, a=1.0, opacity=None, visible=True):
    paint = {'blendMode': 'NORMAL', 'type': 'SOLID', 'color': {'r': r / 255, 'g': g / 255, 'b': b / 255, 'a': a}}
    if opacity is not None:
        paint['opacity'] = opacity
    if not visible:
        paint['visible'] = False
    return paint


def text(node_id, name, x, y, w, h, chars, size=14, weight=400, line=20, color=(34, 36, 42), align='LEFT',
         auto='WIDTH_AND_HEIGHT', overrides=None, table=None, family='PingFang SC', postscript=None):
    postscript = postscript or {400: 'PingFangSC-Regular', 600: 'PingFangSC-Semibold'}[weight]
    node = {'id': node_id, 'name': name, 'type': 'TEXT', 'blendMode': 'PASS_THROUGH',
            'absoluteBoundingBox': box(x, y, w, h), 'absoluteRenderBounds': box(x, y, w, h),
            'fills': [solid(*color)], 'strokes': [], 'strokeWeight': 1, 'strokeAlign': 'OUTSIDE',
            'effects': [], 'characters': chars,
            'style': {'fontFamily': family, 'fontPostScriptName': postscript, 'fontWeight': weight,
                      'fontSize': size, 'textAlignHorizontal': align, 'textAlignVertical': 'TOP',
                      'letterSpacing': 0, 'lineHeightPx': line, 'lineHeightPercentFontSize': line / size * 100,
                      'lineHeightUnit': 'PIXELS', 'textAutoResize': auto},
            'characterStyleOverrides': overrides or [], 'styleOverrideTable': table or {}}
    return node


def rect(node_id, name, x, y, w, h, fills, radius=0, strokes=None, weight=1, align='INSIDE', effects=None, **extra):
    node = {'id': node_id, 'name': name, 'type': 'RECTANGLE', 'blendMode': 'PASS_THROUGH',
            'absoluteBoundingBox': box(x, y, w, h), 'absoluteRenderBounds': box(x, y, w, h),
            'fills': fills, 'strokes': strokes or [], 'strokeWeight': weight, 'strokeAlign': align,
            'effects': effects or [], 'cornerRadius': radius}
    node.update(extra)
    return node


def response():
    status = {'id': '1:10', 'name': 'Status Bar', 'type': 'INSTANCE', 'componentId': '9:1',
              'absoluteBoundingBox': box(0, 0, 375, 44), 'fills': [], 'strokes': [], 'effects': [],
              'clipsContent': False,
              'children': [text('1:11', '9:41', 21, 14, 54, 18, '9:41', size=15, weight=600, line=18)]}
    card = {'id': '1:20', 'name': 'Card', 'type': 'FRAME', 'blendMode': 'PASS_THROUGH',
            'absoluteBoundingBox': box(16, 100, 343, 146), 'absoluteRenderBounds': box(6, 91, 363, 166),
            'fills': [solid(255, 253, 249, 0.85)],
            'strokes': [solid(238, 220, 196)], 'strokeWeight': 1, 'strokeAlign': 'INSIDE',
            'cornerRadius': 12, 'clipsContent': True,
            'effects': [{'type': 'DROP_SHADOW', 'visible': True, 'radius': 10, 'spread': 0,
                         'color': {'r': 216 / 255, 'g': 155 / 255, 'b': 71 / 255, 'a': 0.08},
                         'offset': {'x': 0, 'y': 1}, 'blendMode': 'NORMAL', 'showShadowBehindNode': False}],
            'layoutMode': 'VERTICAL', 'paddingLeft': 16, 'paddingTop': 20, 'itemSpacing': 8,
            'children': [
                text('1:21', 'Label', 32, 120, 56, 20, '提现金额'),
                text('1:22', 'Amount', 32, 150, 80, 28, '¥280', size=20, weight=600, line=28,
                     overrides=[1, 0, 0, 0], table={'1': {'fontSize': 14, 'lineHeightPx': 28}}),
                rect('1:23', 'Divider bg', 32, 190, 311, 40, [solid(250, 246, 238)], radius=8),
            ]}
    dot = {'id': '1:30', 'name': 'Dot', 'type': 'ELLIPSE', 'blendMode': 'PASS_THROUGH',
           'absoluteBoundingBox': box(32, 515, 6, 6), 'absoluteRenderBounds': box(32, 515, 6, 6),
           'fills': [solid(218, 200, 163)], 'strokes': [], 'strokeWeight': 1, 'strokeAlign': 'INSIDE',
           'effects': []}
    triangle = {'id': '1:31', 'name': 'Play', 'type': 'VECTOR', 'blendMode': 'PASS_THROUGH',
                'absoluteBoundingBox': box(60, 510, 12, 14), 'absoluteRenderBounds': box(60, 510, 12, 14),
                'fills': [solid(0, 0, 0)], 'strokes': [], 'strokeWeight': 1, 'strokeAlign': 'CENTER',
                'effects': [], 'fillGeometry': [{'path': 'M0 0L12 7L0 14L0 0Z', 'windingRule': 'NONZERO'}]}
    icon = {'id': '1:40', 'name': 'icon/chevron', 'type': 'INSTANCE', 'componentId': '9:2',
            'absoluteBoundingBox': box(331, 128, 16, 16), 'absoluteRenderBounds': box(331, 128, 16, 16),
            'fills': [], 'strokes': [], 'effects': [], 'clipsContent': True,
            'children': [{'id': '1:41', 'name': 'Vector', 'type': 'VECTOR', 'blendMode': 'PASS_THROUGH',
                          'absoluteBoundingBox': box(336, 131, 6, 10), 'fills': [],
                          'strokes': [solid(188, 145, 74)], 'strokeWeight': 1.5, 'strokeAlign': 'CENTER',
                          'strokeCap': 'ROUND', 'effects': [], 'fillGeometry': [],
                          'strokeGeometry': [{'path': 'M0 0L6 5L0 10', 'windingRule': 'NONZERO'}]}]}
    photo = rect('1:50', 'Avatar', 300, 300, 48, 48, [{'type': 'IMAGE', 'scaleMode': 'FILL', 'imageRef': 'abc'}],
                 radius=24)
    line = {'id': '1:60', 'name': 'Line', 'type': 'LINE', 'blendMode': 'PASS_THROUGH',
            'absoluteBoundingBox': box(16, 600, 343, 0), 'absoluteRenderBounds': box(16, 599.5, 343, 1),
            'fills': [], 'strokes': [solid(241, 237, 225)], 'strokeWeight': 1, 'strokeAlign': 'CENTER',
            'effects': []}
    glass = rect('1:70', 'Glass', 14, 700, 347, 56, [solid(255, 255, 255, 0.7)], radius=16,
                 effects=[{'type': 'BACKGROUND_BLUR', 'visible': True, 'radius': 20}])
    hidden = rect('1:80', 'Old badge', 0, 300, 10, 10, [solid(255, 0, 0)], visible=False)
    gradient = rect('1:90', 'Button', 28, 640, 320, 50, [{
        'type': 'GRADIENT_LINEAR', 'blendMode': 'NORMAL',
        'gradientHandlePositions': [{'x': 0, 'y': 0.5}, {'x': 1, 'y': 0.5}, {'x': 0, 'y': 1}],
        'gradientStops': [{'position': 0, 'color': {'r': 230 / 255, 'g': 181 / 255, 'b': 94 / 255, 'a': 1}},
                          {'position': 1, 'color': {'r': 214 / 255, 'g': 164 / 255, 'b': 74 / 255, 'a': 1}}]}],
        radius=25)
    tabbar = rect('1:95', 'Tab bar', 0, 762, 375, 50, [solid(255, 255, 255)])
    home = {'id': '1:99', 'name': 'Home Indicator', 'type': 'FRAME', 'absoluteBoundingBox': box(0, 778, 375, 34),
            'fills': [], 'strokes': [], 'effects': [], 'clipsContent': False,
            'children': [rect('1:100', 'bar', 121, 799, 134, 5, [solid(0, 0, 0)], radius=2.5)]}
    frame = {'id': '1:2', 'name': 'Withdraw', 'type': 'FRAME', 'blendMode': 'PASS_THROUGH',
             'absoluteBoundingBox': box(0, 0, 375, 812), 'absoluteRenderBounds': box(0, 0, 375, 812),
             'fills': [solid(255, 254, 250)], 'strokes': [], 'effects': [], 'clipsContent': True,
             'children': [status, card, dot, triangle, icon, photo, line, glass, hidden, gradient, tabbar, home]}
    return {'name': 'Fixture file', 'lastModified': '2026-10-01T00:00:00Z', 'version': '4242',
            'nodes': {'1:2': {'document': frame, 'components': {}, 'styles': {}}}}
