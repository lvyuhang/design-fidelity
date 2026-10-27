import 'package:flutter/widgets.dart';

/// Stable key for a widget that implements one Lanhu source node.
///
/// The geometry probe (`fidelity_geometry_probe.dart`) finds widgets by this
/// key and compares their laid-out rect with the source bounds, so keep the
/// key on the widget whose box equals the node's layout frame.
ValueKey<String> sourceKey(String nodeId) => ValueKey<String>('lanhu:$nodeId');

/// Extracts the node id from a key produced by [sourceKey], or null.
String? sourceNodeIdOf(Key? key) {
  if (key is ValueKey<String> && key.value.startsWith('lanhu:')) {
    return key.value.substring('lanhu:'.length);
  }
  return null;
}

/// Marks [child] as the implementation of [nodeId] without changing layout.
class SourceNode extends StatelessWidget {
  SourceNode({required this.nodeId, required this.child})
      : super(key: sourceKey(nodeId));

  final String nodeId;
  final Widget child;

  @override
  Widget build(BuildContext context) => child;
}
