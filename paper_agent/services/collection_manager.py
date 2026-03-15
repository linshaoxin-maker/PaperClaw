"""Collection service: orchestrate paper ingestion from multiple sources.

Collection strategy (six-way concurrent):
  - arXiv       → ArxivAdapter per-category (preprints, daily freshness)
  - DBLP        → DBLPAdapter per-venue (conference proceedings, complete index)
  - S2          → SemanticScholarAdapter.discover() (keyword search + citation network)
  - OpenReview  → OpenReviewAdapter (NeurIPS/ICML/ICLR accepted papers with reviews)
  - ACL Anth.   → ACLAnthologyAdapter (ACL/EMNLP/NAACL/COLING full text + metadata)
  - OpenAlex    → OpenAlexAdapter (250M+ works, free academic graph)

All tracks run concurrently via ThreadPoolExecutor.
Results are merged and deduplicated by canonical_key.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from paper_agent.app.config_manager import ConfigProfile
from paper_agent.domain.models.collection import CollectionRecord
from paper_agent.domain.models.paper import Paper
from paper_agent.infra.sources.acl_anthology_adapter import ACLAnthologyAdapter
from paper_agent.infra.sources.arxiv_adapter import ArxivAdapter
from paper_agent.infra.sources.dblp_adapter import DBLPAdapter
from paper_agent.infra.sources.openalex_adapter import OpenAlexAdapter
from paper_agent.infra.sources.openreview_adapter import OpenReviewAdapter
from paper_agent.infra.sources.semantic_scholar_adapter import SemanticScholarAdapter
from paper_agent.infra.sources.source_registry import SourceDefinition
from paper_agent.infra.storage.sqlite_storage import SQLiteStorage
from paper_agent.services.source_collector import SourceCollector


class CollectionManager:
    def __init__(
        self,
        storage: SQLiteStorage,
        source_collector: SourceCollector | None = None,
        s2_adapter: SemanticScholarAdapter | None = None,
        dblp_adapter: DBLPAdapter | None = None,
        openreview_adapter: OpenReviewAdapter | None = None,
        acl_adapter: ACLAnthologyAdapter | None = None,
        openalex_adapter: OpenAlexAdapter | None = None,
        debug: bool = False,
        debug_log: Callable[[str], None] | None = None,
        progress_log: Callable[[str], None] | None = None,
    ) -> None:
        self._storage = storage
        self._debug = debug
        self._debug_log = debug_log
        self._progress_log = progress_log
        adapter_kwargs = {
            "debug": debug, "debug_log": debug_log, "progress_log": progress_log,
        }
        self._source_collector = source_collector
        self._s2 = s2_adapter or SemanticScholarAdapter(**adapter_kwargs)
        self._dblp = dblp_adapter or DBLPAdapter(**adapter_kwargs)
        self._arxiv = ArxivAdapter(**adapter_kwargs)
        self._openreview = openreview_adapter or OpenReviewAdapter(**adapter_kwargs)
        self._acl = acl_adapter or ACLAnthologyAdapter(**adapter_kwargs)
        self._openalex = openalex_adapter or OpenAlexAdapter(**adapter_kwargs)

    def _log(self, message: str) -> None:
        if self._debug and self._debug_log is not None:
            self._debug_log(message)

    def _progress(self, message: str) -> None:
        if self._progress_log is not None:
            self._progress_log(message)
        elif self._debug and self._debug_log is not None:
            self._debug_log(message)

    # ── Smart multi-source collection (six-way) ──

    def collect_from_sources(
        self,
        sources: list[SourceDefinition],
        profile: ConfigProfile | None = None,
        days_back: int = 7,
        max_results: int = 200,
    ) -> CollectionRecord:
        """Collect papers from all enabled sources concurrently.

        Six parallel tracks (each runs only if matching sources exist):
          1. arXiv     → per-category preprint search
          2. OpenReview → NeurIPS/ICML/ICLR accepted papers
          3. ACL Anth. → ACL/EMNLP/NAACL proceedings
          4. DBLP      → all other conference proceedings
          5. S2        → keyword discovery across citation network
          6. OpenAlex  → broad academic graph search
        """
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
        record = CollectionRecord(source_name="multi", trigger_type="manual")

        arxiv_sources = [s for s in sources if s.api_type == "arxiv" and s.enabled]
        conf_sources = [s for s in sources if s.type == "conference" and s.enabled]

        openreview_sources = [s for s in conf_sources if s.api_type == "openreview"]
        acl_sources = [s for s in conf_sources if s.api_type == "acl_anthology"]
        dblp_sources = [s for s in conf_sources if s.api_type == "dblp"]
        # Conferences without a native adapter also go through DBLP
        other_conf = [s for s in conf_sources if s.api_type not in ("openreview", "acl_anthology", "dblp")]
        dblp_sources = dblp_sources + other_conf

        tracks = []
        if arxiv_sources:
            tracks.append(f"arXiv({len(arxiv_sources)})")
        if openreview_sources:
            tracks.append(f"OpenReview({len(openreview_sources)})")
        if acl_sources:
            tracks.append(f"ACL({len(acl_sources)})")
        if dblp_sources:
            tracks.append(f"DBLP({len(dblp_sources)})")
        if conf_sources and profile:
            tracks.append("S2(关键词)")
        if profile and (profile.topics or profile.keywords):
            tracks.append("OpenAlex(关键词)")

        self._progress(f"开始采集: {' + '.join(tracks)} 并行 ...")
        self._log(
            f"Multi-source collection: {len(arxiv_sources)} arXiv, "
            f"{len(openreview_sources)} OpenReview, {len(acl_sources)} ACL, "
            f"{len(dblp_sources)} DBLP, S2+OpenAlex(关键词), "
            f"days_back={days_back}, since={since.isoformat()}"
        )

        all_papers: list[Paper] = []
        errors: dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures: dict = {}

            if arxiv_sources:
                futures[executor.submit(
                    self._collect_arxiv, arxiv_sources, since, max_results
                )] = "arxiv"

            if openreview_sources:
                futures[executor.submit(
                    self._collect_openreview, openreview_sources, since, max_results
                )] = "openreview"

            if acl_sources:
                futures[executor.submit(
                    self._collect_acl, acl_sources, since, max_results
                )] = "acl_anthology"

            if dblp_sources:
                futures[executor.submit(
                    self._collect_dblp, dblp_sources, since, max_results
                )] = "dblp"

            if conf_sources and profile and (profile.topics or profile.keywords):
                venue_names = [s.display_name for s in conf_sources]
                keywords = (profile.topics or []) + (profile.keywords or [])
                futures[executor.submit(
                    self._collect_s2, keywords, venue_names, since, max_results
                )] = "semantic_scholar"

            if profile and (profile.topics or profile.keywords):
                keywords = (profile.topics or []) + (profile.keywords or [])
                venue_names = [s.display_name for s in conf_sources] if conf_sources else []
                futures[executor.submit(
                    self._collect_openalex, keywords, venue_names, since, max_results
                )] = "openalex"

            for future in as_completed(futures):
                source_type = futures[future]
                try:
                    papers = future.result()
                    all_papers.extend(papers)
                    self._progress(f"✓ {source_type}: {len(papers)} 篇")
                except Exception as e:
                    self._progress(f"✗ {source_type}: 失败 ({e})")
                    self._log(f"{source_type} failed: {e}")
                    errors[source_type] = str(e)

        all_papers = self._deduplicate(all_papers)
        record.collected_count = len(all_papers)
        self._progress(f"去重后: {record.collected_count} 篇唯一论文")

        self._progress(f"保存 {len(all_papers)} 篇论文 ...")
        try:
            new_count, dup_count = self._storage.save_papers(all_papers)
            record.new_count = new_count
            record.duplicate_count = dup_count
            record.status = "completed"
            self._progress(f"完成: {new_count} 新增, {dup_count} 重复")
        except Exception as e:
            record.status = "failed"
            errors["save"] = str(e)
            self._progress(f"保存失败: {e}")

        if errors:
            record.error_summary = {"partial_errors": errors}
            if record.status != "failed":
                record.error_summary["note"] = "Some sources failed but collection completed."

        record.finished_at = datetime.utcnow()
        self._storage.save_collection(record)
        return record

    # ── Survey mode: retrospective research over N years ──

    def survey_topic(
        self,
        keywords: list[str],
        venues: list[str] | None = None,
        years_back: int = 5,
        max_results: int = 500,
    ) -> CollectionRecord:
        """Retrospective survey: collect papers on a topic over multiple years.

        Four-way concurrent search optimized for breadth:
          - S2: keyword search across years (semantic relevance + citations)
          - OpenAlex: broad academic graph search (250M+ works)
          - DBLP: full venue proceedings for the period (completeness)
          - arXiv: keyword search across years (preprints)

        Args:
            keywords: Research keywords/topics to search for.
            venues: Conference short names to include (e.g. ["DAC", "NeurIPS"]).
            years_back: How many years to look back (default 5).
            max_results: Max total papers to return.
        """
        since = datetime.now(timezone.utc) - timedelta(days=years_back * 365)
        record = CollectionRecord(source_name="survey", trigger_type="manual")

        self._progress(
            f"Survey: {', '.join(keywords[:5])}, "
            f"venues={venues or 'all'}, 过去 {years_back} 年"
        )
        self._log(
            f"Survey: keywords={keywords}, venues={venues}, "
            f"years_back={years_back}, since={since.year}"
        )

        all_papers: list[Paper] = []
        errors: dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures: dict = {}

            futures[executor.submit(
                self._collect_s2, keywords, venues or [], since, max_results
            )] = "semantic_scholar"

            futures[executor.submit(
                self._collect_openalex, keywords, venues or [], since, max_results
            )] = "openalex"

            if venues:
                from paper_agent.infra.sources.source_registry import SourceRegistry
                registry = SourceRegistry()
                dblp_sources = []
                for src in registry.list_sources():
                    if src.type == "conference" and src.display_name in venues:
                        dblp_sources.append(src)
                if dblp_sources:
                    futures[executor.submit(
                        self._collect_dblp, dblp_sources, since, max_results
                    )] = "dblp"

            query_str = "+AND+".join(f"all:{kw}" for kw in keywords[:5])
            futures[executor.submit(
                self._search_arxiv, query_str, since, min(max_results, 200)
            )] = "arxiv"

            for future in as_completed(futures):
                source_type = futures[future]
                try:
                    papers = future.result()
                    all_papers.extend(papers)
                    self._progress(f"✓ survey/{source_type}: {len(papers)} 篇")
                except Exception as e:
                    self._progress(f"✗ survey/{source_type}: 失败 ({e})")
                    self._log(f"Survey {source_type} failed: {e}")
                    errors[source_type] = str(e)

        all_papers = self._deduplicate(all_papers)
        record.collected_count = len(all_papers)
        self._progress(f"Survey 去重后: {record.collected_count} 篇唯一论文")

        try:
            new_count, dup_count = self._storage.save_papers(all_papers)
            record.new_count = new_count
            record.duplicate_count = dup_count
            record.status = "completed"
        except Exception as e:
            record.status = "failed"
            errors["save"] = str(e)

        if errors:
            record.error_summary = {"partial_errors": errors}

        record.finished_at = datetime.utcnow()
        self._storage.save_collection(record)
        return record

    # ── Internal collection methods ──

    def _collect_arxiv(
        self, sources: list[SourceDefinition], since: datetime, max_results: int
    ) -> list[Paper]:
        if self._source_collector:
            result = self._source_collector.collect_all(
                sources=sources, since=since, max_results=max_results,
            )
            return result.papers
        categories = [
            s.api_config.get("category", "")
            for s in sources if s.api_config
        ]
        return self._arxiv.collect_papers(
            categories=[c for c in categories if c],
            since=since, max_results=max_results,
        )

    # DBLP venue_key for conferences that don't have one in api_config
    _DBLP_VENUE_MAP: dict[str, str] = {
        "neurips": "conf/nips",
        "icml": "conf/icml",
        "iclr": "conf/iclr",
        "acl": "conf/acl",
        "emnlp": "conf/emnlp",
        "naacl": "conf/naacl",
        "coling": "conf/coling",
        "eacl": "conf/eacl",
        "findings": "conf/acl",
        "icse": "conf/icse",
        "fse": "conf/sigsoft",
        "ase": "conf/kbse",
        "issta": "conf/issta",
        "msr": "conf/msr",
        "saner": "conf/wcre",
        "issre": "conf/issre",
        "sigir": "conf/sigir",
        "kdd": "conf/kdd",
        "www": "conf/www",
        "wsdm": "conf/wsdm",
        "cikm": "conf/cikm",
        "recsys": "conf/recsys",
        "osdi": "conf/osdi",
        "sosp": "conf/sosp",
        "sigmod": "conf/sigmod",
        "vldb": "conf/vldb",
        "aamas": "conf/atal",
    }

    def _resolve_dblp_venue_key(self, src: SourceDefinition) -> str:
        """Get DBLP venue_key from api_config or by conference name lookup."""
        cfg = src.api_config or {}
        venue_key = cfg.get("venue_key", "")
        if venue_key:
            return venue_key
        # Try to infer from source id (e.g. "conf:neurips" → "conf/nips")
        conf_id = src.id.split(":")[-1] if ":" in src.id else ""
        return self._DBLP_VENUE_MAP.get(conf_id, "")

    def _collect_openreview(
        self, sources: list[SourceDefinition], since: datetime, max_results: int
    ) -> list[Paper]:
        """Collect from OpenReview venues (NeurIPS, ICML, ICLR)."""
        import time

        papers: list[Paper] = []
        for i, src in enumerate(sources):
            if len(papers) >= max_results:
                break
            api_config = src.api_config or {}
            venue_id = api_config.get("venue_id", "")
            if not venue_id:
                self._log(f"OpenReview: no venue_id for {src.display_name}, skipping")
                continue
            self._progress(f"OpenReview: 抓取 {src.display_name} ({venue_id}) ...")
            try:
                batch = self._openreview.collect(
                    api_config=api_config,
                    since=since,
                    max_results=max_results - len(papers),
                )
                papers.extend(batch)
                self._log(f"OpenReview {src.display_name}: {len(batch)} papers")
            except Exception as e:
                self._log(f"OpenReview {src.display_name} failed: {e}")
            if i < len(sources) - 1:
                time.sleep(self._openreview.rate_limit_delay)
        return papers

    def _collect_acl(
        self, sources: list[SourceDefinition], since: datetime, max_results: int
    ) -> list[Paper]:
        """Collect from ACL Anthology venues (ACL, EMNLP, NAACL, etc.)."""
        import time

        papers: list[Paper] = []
        for i, src in enumerate(sources):
            if len(papers) >= max_results:
                break
            api_config = src.api_config or {}
            venue_key = api_config.get("venue_key", "")
            if not venue_key:
                self._log(f"ACL: no venue_key for {src.display_name}, skipping")
                continue
            self._progress(f"ACL Anthology: 抓取 {src.display_name} ({venue_key}) ...")
            try:
                batch = self._acl.collect(
                    api_config=api_config,
                    since=since,
                    max_results=max_results - len(papers),
                )
                papers.extend(batch)
                self._log(f"ACL {src.display_name}: {len(batch)} papers")
            except Exception as e:
                self._log(f"ACL {src.display_name} failed: {e}")
            if i < len(sources) - 1:
                time.sleep(self._acl.rate_limit_delay)
        return papers

    def _collect_dblp(
        self, sources: list[SourceDefinition], since: datetime, max_results: int
    ) -> list[Paper]:
        """Collect from DBLP venues serially (rate limit friendly)."""
        import time

        papers: list[Paper] = []
        for i, src in enumerate(sources):
            if len(papers) >= max_results:
                break
            venue_key = self._resolve_dblp_venue_key(src)
            if not venue_key:
                self._log(f"DBLP: no venue_key for {src.display_name}, skipping")
                continue
            self._progress(f"DBLP: 抓取 {src.display_name} ({venue_key}) ...")
            self._log(f"DBLP: collecting {src.display_name} ({venue_key})")
            try:
                batch = self._dblp.collect(
                    api_config={"venue_key": venue_key},
                    since=since,
                    max_results=max_results - len(papers),
                )
                papers.extend(batch)
                self._log(f"DBLP {src.display_name}: {len(batch)} papers")
            except Exception as e:
                self._log(f"DBLP {src.display_name} failed: {e}")
            if i < len(sources) - 1:
                time.sleep(self._dblp.rate_limit_delay)
        return papers

    def _collect_s2(
        self,
        keywords: list[str],
        venues: list[str],
        since: datetime,
        max_results: int,
    ) -> list[Paper]:
        return self._s2.discover(
            keywords=keywords, venues=venues,
            since=since, max_results=max_results,
        )

    def _collect_openalex(
        self,
        keywords: list[str],
        venues: list[str],
        since: datetime,
        max_results: int,
    ) -> list[Paper]:
        return self._openalex.discover(
            keywords=keywords, venues=venues or None,
            since=since, max_results=max_results,
        )

    def _search_arxiv(
        self, query: str, since: datetime, max_results: int
    ) -> list[Paper]:
        """arXiv keyword search (for survey mode)."""
        from paper_agent.infra.sources.arxiv_adapter import ARXIV_API_URL

        import httpx

        url = (
            f"{ARXIV_API_URL}?search_query={query}"
            f"&start=0&max_results={max_results}"
            f"&sortBy=relevance&sortOrder=descending"
        )
        try:
            client = httpx.Client(timeout=30.0, follow_redirects=True, trust_env=True)
            resp = client.get(url)
            client.close()
            if resp.status_code != 200:
                return []
            papers = self._arxiv._parse_response(resp.text)
            if since:
                papers = [p for p in papers if p.published_at and p.published_at >= since]
            return papers
        except Exception as e:
            self._log(f"arXiv search failed: {e}")
            return []

    def _deduplicate(self, papers: list[Paper]) -> list[Paper]:
        """Remove duplicates by canonical_key, preferring papers with abstracts."""
        seen: dict[str, Paper] = {}
        for p in papers:
            existing = seen.get(p.canonical_key)
            if existing is None:
                seen[p.canonical_key] = p
            elif not existing.abstract and p.abstract:
                # Prefer the version with an abstract (S2 > DBLP)
                seen[p.canonical_key] = p
        return list(seen.values())

    # ── Legacy arXiv-only collection ──

    def collect_from_arxiv(
        self,
        categories: list[str],
        days_back: int = 7,
        max_results: int = 200,
    ) -> CollectionRecord:
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
        record = CollectionRecord(source_name="arxiv", trigger_type="manual")

        self._progress(f"arXiv: 采集 {len(categories)} 个分类, 过去 {days_back} 天 ...")
        self._log(
            f"arXiv-only collection: categories={categories}, "
            f"days_back={days_back}, since={since.isoformat()}"
        )

        try:
            papers = self._arxiv.collect_papers(
                categories=categories, since=since, max_results=max_results
            )
            record.collected_count = len(papers)
            self._progress(f"arXiv: 获取 {len(papers)} 篇, 保存中 ...")
            new_count, dup_count = self._storage.save_papers(papers)
            record.new_count = new_count
            record.duplicate_count = dup_count
            record.status = "completed"
            self._progress(f"arXiv: 完成 ({new_count} 新增, {dup_count} 重复)")
        except Exception as e:
            record.status = "failed"
            record.error_summary = {"error": str(e)}
            self._progress(f"arXiv: 采集失败 ({e})")
            self._log(f"Collection failed: {e}")

        record.finished_at = datetime.utcnow()
        self._storage.save_collection(record)
        return record

    def add_paper_by_id(self, arxiv_id: str) -> Paper | None:
        paper = self._arxiv.get_paper_metadata(arxiv_id)
        if paper:
            self._storage.save_paper(paper)
        return paper
