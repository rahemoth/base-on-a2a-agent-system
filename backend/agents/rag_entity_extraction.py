"""
LLM-based entity and relation extraction for the RAG memory system.

Replaces the old capitalized-word heuristic (which missed Chinese entirely)
with a single LLM call per chunk that returns structured JSON:
  - entities: [{name, type}]
  - relations: [{subject, predicate, object}]  (semantic triples)

The OpenAI-compatible client is injected after construction (see
RAGMemorySystem.set_llm_client) so this module never builds its own client
and naturally supports whatever provider the agent is configured with.
"""
import json
import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


ENTITY_TYPES = ["person", "organization", "location", "concept", "event", "other"]

_SYSTEM_PROMPT = """你是一个信息抽取助手。从给定的中文文本中抽取实体和实体之间的语义关系，以 JSON 格式返回。

要求：
1. entities 是一个数组，每个元素是 {"name": 实体名, "type": 实体类型}。type 必须是以下之一：person（人/角色）、organization（组织/机构/公司）、location（地点/位置）、concept（概念/技术/产品）、event（事件）、other（其他）。
2. relations 是一个数组，每个元素是 {"subject": 主实体名, "predicate": 关系（用简短中文动词或短语）, "object": 客实体名}。只抽取文本中明确体现的关系，不要臆测。
3. 实体名保留原文（中文就用中文）。人名、地名、机构名、技术名都要抽。
4. 如果文本中没有明确的实体或关系，返回空数组。
5. 只返回 JSON，不要任何解释文字。JSON 顶层键必须是 "entities" 和 "relations"。

示例输入："张三在北京大学研究人工智能，他和李四合作发表了论文"
示例输出：{"entities":[{"name":"张三","type":"person"},{"name":"北京大学","type":"organization"},{"name":"人工智能","type":"concept"},{"name":"李四","type":"person"}],"relations":[{"subject":"张三","predicate":"研究","object":"人工智能"},{"subject":"张三","predicate":"位于","object":"北京大学"},{"subject":"张三","predicate":"合作","object":"李四"}]}"""


class LLMEntityRelationExtractor:
    """Extract entities and semantic relations from text using an injected LLM client."""

    def __init__(
        self,
        client: Optional[Any] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 800,
        temperature: float = 0.2,
    ):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def set_client(self, client: Any) -> None:
        """Inject an AsyncOpenAI-compatible client after construction."""
        self.client = client

    @property
    def available(self) -> bool:
        return self.client is not None

    async def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract entities and relations from text.

        Returns {"entities": [{"name", "type"}], "relations": [{"subject", "predicate", "object"}]}.
        On any failure (no client, LLM error, unparseable JSON) returns empty
        lists so the caller can fall back to co-occurrence.
        """
        if not self.client or not text or not text.strip():
            return {"entities": [], "relations": []}

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            return self._parse(content)
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {e}")
            return {"entities": [], "relations": []}

    @staticmethod
    def _parse(content: str) -> Dict[str, Any]:
        """Parse LLM JSON output with fallbacks for malformed responses."""
        if not content:
            return {"entities": [], "relations": []}

        # Try direct JSON parse first
        try:
            data = json.loads(content)
            return LLMEntityRelationExtractor._normalize(data)
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: extract the first {...} block and retry
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return LLMEntityRelationExtractor._normalize(data)
            except (json.JSONDecodeError, TypeError):
                pass

        logger.warning(f"Could not parse LLM extraction output: {content[:200]}")
        return {"entities": [], "relations": []}

    @staticmethod
    def _normalize(data: Any) -> Dict[str, Any]:
        """Validate and normalize the parsed structure."""
        if not isinstance(data, dict):
            return {"entities": [], "relations": []}

        entities = []
        raw_entities = data.get("entities", []) or []
        if isinstance(raw_entities, str):
            raw_entities = [raw_entities] if raw_entities else []
        for e in raw_entities:
            if isinstance(e, dict) and e.get("name"):
                etype = e.get("type", "other")
                if etype not in ENTITY_TYPES:
                    etype = "other"
                entities.append({"name": str(e["name"]), "type": etype})
            elif isinstance(e, str) and e:
                entities.append({"name": e, "type": "other"})

        relations = []
        for r in data.get("relations", []) or []:
            if not isinstance(r, dict):
                continue
            subj = r.get("subject")
            pred = r.get("predicate")
            obj = r.get("object")
            if subj and pred and obj:
                relations.append({
                    "subject": str(subj),
                    "predicate": str(pred),
                    "object": str(obj),
                })

        return {"entities": entities, "relations": relations}
