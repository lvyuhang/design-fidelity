# MCP 取证适配

首次连接或分页/导出异常时查阅。按能力适配服务器名称：快照、节点区域检查、原始资源导出缺一时说明限制。旧版分析 HTML 不能替代，不伪造 snapshot_id，不自动改 MCP 配置。

## 调用顺序

1. design_id 未知时用 lanhu_get_designs 按指定画板定位。
2. lanhu_get_design_overview 传 design_id 和 URL 版本；仅明确请求最新时传 latest。保存 snapshot_id、resolved_version、画布、映射、参考图、索引。
3. lanhu_inspect_design_region 优先 node_ids；发现节点才用 region。完成分页，保存完整 nodes/ancestors/raw_style，与源 total_nodes 对照。
4. lanhu_export_design_assets 使用源资产 ID，优先 format_preference: original；SVG/回退明确记录。
5. 用客户端可用方式下载 bundle，按 manifest 安装，核对字节、SHA256、尺寸。URI/封装随服务适配，服务端路径不是本地文件。

## 证据字段

源 JSON 与派生产物分开；新版本另建基线。凭据、Cookie、鉴权 URL 不进入分发包/仓库。

- coordinate_space: source_canvas、coordinate_mapping.verified: true；参考图与画布同一缩放比，局部截图不拉伸为整页。
- bounds、父级层级/裁剪、类型、asset_id、导出结果；文字保存字体/字重/行高/颜色/对齐及混合 runs。
- 矢量保存路径、控制点、变换、填充规则、描边/端点/连接；保存阴影、渐变、透明、模糊、蒙版等原始字段与祖先样式。overview/CSS 不足以实现这些效果。

无 asset_id 继续查原矢量/效果，不能直接判缺图。定制素材缺失按用户策略保形占位；仅授权的单个静态素材可源渲染回退，不得裁图替代卡片/导航等业务代码。缺证据只阻塞受影响区域，正式验收前闭环。

完整页 expected_node_count 对照源总数；局部显式 provided_nodes 和原因。初始化器无法发现未拉取节点。参考图可见但清单没有时排查分页、父层烘焙、低透明层/蒙版，不在代码中仿画补洞。
