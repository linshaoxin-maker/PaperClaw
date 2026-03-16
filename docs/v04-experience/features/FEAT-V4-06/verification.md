## Feature 验证报告：FEAT-V4-06 PDF 下载增强 + Bug Fix

### 1. 四可检验验收
| 检验项 | 验收结论 | 说明 |
|---|---|---|
| 可感知 | ✅ | 非 arXiv 论文下载尝试多个 fallback URL |
| 可演示 | ✅ | paper_download(非 arXiv 论文) → fallback 到 S2 PDF |
| 可端到端 | ✅ | 搜索论文 → find_and_download → PDF 文件存在 |
| 可独立上线 | ✅ | 不依赖其他 FEAT |

### 2. Bug Fix 汇总

**paper_find_and_download**:
- `source=` → `source_name=`：修复 Paper 构造参数名，避免 TypeError
- 新增 `metadata` 参数传入 S2 返回的 pdf_url、doi、venue
- openAccessPdf URL 现在持久化到 Paper.metadata，后续 paper_download 可复用

**paper_download**:
- DOI fallback 现在检查 Content-Type 是否为 PDF
- HTML 响应（付费页面）不再被误存为 PDF
- 改为 fallback 链：arXiv → metadata.pdf_url → DOI (with Content-Type check)
- 失败原因区分："Publisher page (paywall)" vs "网络超时" vs "All download URLs failed"

### 3. 技术验证汇总
| 验证项 | 状态 | 说明 |
|---|---|---|
| 契约符合性 | ✅ | 与 FS-06, FS-07 一致 |
| 回归测试 | ⚠️ | 需实际网络请求验证 |
| 架构守护 | ✅ | 变更限于 mcp/tools.py |
