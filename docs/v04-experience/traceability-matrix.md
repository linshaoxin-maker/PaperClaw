# v04-experience 追溯矩阵（终版）

| Story ID | UC ID | NFR ID | FEAT-ID | 粒度 | Sprint | 文件 | 函数 | 验证状态 |
|---|---|---|---|---|---|---|---|---|
| US-V4-01 | UC-V4-01 | | FEAT-V4-02 | 粗 | S1 | services/digest_generator.py | _format_paper | ✅ |
| US-V4-02 | UC-V4-01 | NFR-V4-04 | FEAT-V4-01,02 | 粗 | S1 | domain/models/paper.py, services/digest_generator.py | to_summary_dict, to_detail_dict, _format_paper | ✅ |
| US-V4-03 | UC-V4-01 | | FEAT-V4-07 | 粗 | S1 | cli/_skill_content.py | ROUTER_SKILL | ✅ |
| US-V4-04 | UC-V4-02 | NFR-V4-01 | FEAT-V4-03 | 细 | S1 | services/filtering_manager.py, infra/llm/llm_provider.py | _score_batch, score_relevance_batch | ✅ |
| US-V4-04 | UC-V4-03 | NFR-V4-02 | FEAT-V4-04 | 粗 | S1 | services/filtering_manager.py | _pre_filter | ✅ |
| US-V4-05 | UC-V4-04 | | FEAT-V4-05 | 细 | S2 | services/filtering_manager.py, app/context.py | _apply_feedback_offset | ✅ |
| US-V4-06 | UC-V4-05 | NFR-V4-06 | FEAT-V4-06 | 粗 | S2 | mcp/tools.py | paper_download, paper_find_and_download | ✅ |
| US-V4-07 | UC-V4-01 | | FEAT-V4-08 | 粗 | S2 | cli/_skill_content.py | DEEP_DIVE_SKILL | ✅ |
| US-V4-15 | UC-V4-06 | | FEAT-V4-07 | 粗 | S1 | cli/_skill_content.py | ROUTER_SKILL | ✅ |
| US-V4-19 | UC-V4-06 | | FEAT-V4-07 | 粗 | S1 | cli/_skill_content.py | ROUTER_SKILL | ✅ |
