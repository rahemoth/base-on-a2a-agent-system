"""
Skill System for Agent Harness
Provides predefined skill loading (prompt + tool combinations)
Supports importing custom skills from JSON and Markdown files
"""
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

CUSTOM_SKILLS_PATH = Path("./data/custom_skills.json")


@dataclass
class Skill:
    """A predefined skill that can be loaded onto an agent"""
    id: str
    name: str
    description: str
    prompt: str                          # Injected into system prompt
    tools: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    enabled: bool = True
    is_custom: bool = False              # True for user-imported skills

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "category": self.category,
            "num_tools": len(self.tools),
            "is_custom": self.is_custom,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Full serialization including prompt and tools"""
        d = self.to_dict()
        d["prompt"] = self.prompt
        d["tools"] = self.tools
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create a Skill from a dictionary (e.g., parsed JSON)"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            prompt=data.get("prompt", ""),
            tools=data.get("tools", []),
            tags=data.get("tags", []),
            category=data.get("category", "custom"),
            enabled=data.get("enabled", True),
            is_custom=data.get("is_custom", True),
        )


# ── Built-in Skills ──────────────────────────────────────────────

BUILTIN_SKILLS = [
    Skill(
        id="code_review",
        name="代码审查",
        description="对代码进行审查，发现潜在问题并提供改进建议",
        category="development",
        tags=["code", "review", "development"],
        prompt="""## 代码审查模式
你现在处于代码审查模式。当用户提供代码时，请：
1. 检查代码的正确性、可读性和性能
2. 识别潜在的 bug 和安全漏洞
3. 提供具体的改进建议和优化方案
4. 使用中文回复，代码注释可以保留英文""",
    ),
    Skill(
        id="translate",
        name="翻译助手",
        description="高质量多语言翻译，支持中英日韩等主要语言",
        category="language",
        tags=["translate", "language", "i18n"],
        prompt="""## 翻译模式
你现在是一个专业翻译助手。请遵循以下原则：
1. 翻译要自然流畅，符合目标语言的表达习惯
2. 专业术语要准确，必要时保留原文并附注释
3. 保持原文的语气和风格
4. 如果用户没有指定目标语言，默认翻译为中文""",
    ),
    Skill(
        id="summarize",
        name="摘要生成",
        description="对长文本进行智能摘要，提取关键信息",
        category="text",
        tags=["summary", "text", "extraction"],
        prompt="""## 摘要模式
你现在处于摘要生成模式。处理长文本时请：
1. 提取核心观点和关键信息
2. 保持逻辑结构清晰
3. 使用简洁的语言，避免冗余
4. 根据文本长度自适应摘要比例（短文保留80%，长文压缩到20-30%）""",
    ),
    Skill(
        id="data_analysis",
        name="数据分析",
        description="分析数据并生成可视化建议和统计洞察",
        category="analysis",
        tags=["data", "analysis", "statistics"],
        prompt="""## 数据分析模式
你现在是一个数据分析专家。当用户提供数据时，请：
1. 识别数据的类型、分布和特征
2. 计算关键统计指标（均值、中位数、方差等）
3. 发现数据中的趋势、异常和关联
4. 提供可视化建议（图表类型选择）
5. 给出基于数据的决策建议""",
        tools=[
            {
                "name": "calculate",
                "description": "执行数学计算",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "数学表达式"}
                    },
                    "required": ["expression"]
                }
            }
        ],
    ),
    Skill(
        id="creative_writing",
        name="创意写作",
        description="协助创作故事、诗歌、文案等创意内容",
        category="creative",
        tags=["writing", "creative", "story"],
        prompt="""## 创意写作模式
你是一个创意写作助手。请遵循以下原则：
1. 充分发挥想象力，创作独特的内容
2. 注重文字的美感和节奏感
3. 根据用户需求调整风格（正式/轻松/幽默/文艺等）
4. 可以主动提供多个创意方向供选择""",
    ),
    Skill(
        id="task_planning",
        name="任务规划",
        description="帮助分解复杂任务，制定执行计划",
        category="productivity",
        tags=["planning", "task", "productivity"],
        prompt="""## 任务规划模式
你是一个任务规划专家。当用户提出复杂任务时，请：
1. 将任务分解为可执行的子任务
2. 为每个子任务估算优先级和时间
3. 识别任务间的依赖关系
4. 提供里程碑和检查点
5. 考虑潜在风险和备选方案
输出格式使用结构化的任务列表""",
    ),
]


class SkillManager:
    """
    Manages skills for an agent instance.

    - Loads built-in skills on init
    - Loads custom (user-imported) skills from file
    - Allows activating/deactivating skills
    - Provides aggregated prompts and tools for active skills
    """

    def __init__(self):
        self.available_skills: Dict[str, Skill] = {}
        self.active_skills: Dict[str, Skill] = {}
        self._load_builtin_skills()
        self._load_custom_skills()

    def _load_builtin_skills(self):
        """Load all built-in skills into the available registry"""
        for skill in BUILTIN_SKILLS:
            self.available_skills[skill.id] = skill
        logger.info(f"Loaded {len(self.available_skills)} built-in skills")

    def _load_custom_skills(self):
        """Load custom skills from the JSON file"""
        if not CUSTOM_SKILLS_PATH.exists():
            return
        try:
            with open(CUSTOM_SKILLS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for skill_data in data:
                skill = Skill.from_dict(skill_data)
                skill.is_custom = True
                self.available_skills[skill.id] = skill
            logger.info(f"Loaded {len(data)} custom skills from {CUSTOM_SKILLS_PATH}")
        except Exception as e:
            logger.error(f"Failed to load custom skills: {e}")

    @staticmethod
    def _save_custom_skills(skills: Dict[str, Skill]):
        """Persist custom skills to the JSON file"""
        CUSTOM_SKILLS_PATH.parent.mkdir(parents=True, exist_ok=True)
        custom = [s.to_full_dict() for s in skills.values() if s.is_custom]
        with open(CUSTOM_SKILLS_PATH, "w", encoding="utf-8") as f:
            json.dump(custom, f, ensure_ascii=False, indent=2)

    def import_skill(self, skill_data: Dict[str, Any]) -> Skill:
        """
        Import a custom skill from a dict. Saves to file.
        Returns the created Skill.
        Raises ValueError if the skill ID conflicts with a built-in.
        """
        skill_id = skill_data.get("id", "")
        if not skill_id:
            raise ValueError("Skill must have an 'id' field")
        if skill_id in {s.id for s in BUILTIN_SKILLS}:
            raise ValueError(f"Cannot override built-in skill '{skill_id}'")

        skill = Skill.from_dict(skill_data)
        skill.is_custom = True
        self.available_skills[skill.id] = skill

        # Persist all custom skills
        self._save_custom_skills(self.available_skills)
        logger.info(f"Imported custom skill: {skill.id}")
        return skill

    def delete_custom_skill(self, skill_id: str) -> bool:
        """Delete a custom skill. Returns False if not found or is built-in."""
        skill = self.available_skills.get(skill_id)
        if not skill or not skill.is_custom:
            return False

        # Remove from active and available
        self.active_skills.pop(skill_id, None)
        del self.available_skills[skill_id]

        # Re-persist
        self._save_custom_skills(self.available_skills)
        logger.info(f"Deleted custom skill: {skill_id}")
        return True

    def activate_skill(self, skill_id: str) -> bool:
        """Activate a skill by ID. Returns True if successful."""
        if skill_id not in self.available_skills:
            logger.warning(f"Skill '{skill_id}' not found in available skills")
            return False
        self.active_skills[skill_id] = self.available_skills[skill_id]
        logger.info(f"Activated skill: {skill_id}")
        return True

    def deactivate_skill(self, skill_id: str) -> bool:
        """Deactivate a skill by ID. Returns True if successful."""
        if skill_id not in self.active_skills:
            return False
        del self.active_skills[skill_id]
        logger.info(f"Deactivated skill: {skill_id}")
        return True

    def get_active_prompt(self) -> str:
        """Build the aggregated prompt from all active skills."""
        if not self.active_skills:
            return ""
        return "\n\n".join(s.prompt for s in self.active_skills.values())

    def get_active_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from active skills"""
        tools = []
        for skill in self.active_skills.values():
            tools.extend(skill.tools)
        return tools

    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available skills, optionally filtered by category"""
        skills = list(self.available_skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return [s.to_dict() for s in skills]

    def get_active_skill_ids(self) -> List[str]:
        """Get list of active skill IDs"""
        return list(self.active_skills.keys())

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID"""
        return self.available_skills.get(skill_id)

    def import_skill_from_markdown(self, content: str) -> List[Skill]:
        """
        Import skills from a markdown file content.
        Supports both single skill and multi-skill formats.

        Format:
        ---
        skill_id: xxx
        name: xxx
        description: xxx
        category: xxx
        tags:
          - tag1
          - tag2
        ---

        ## Prompt Title

        Prompt content here...

        ## Tools (optional)
        ### tool_name
        Description

        **Parameters:**
        - param1 (type): description
        """
        skills = []
        # Split by skill separators (--- at start of line)
        skill_blocks = re.split(r'\n---\n', content)

        for block in skill_blocks:
            if not block.strip():
                continue

            skill = self._parse_skill_block(block)
            if skill:
                if skill.id in {s.id for s in BUILTIN_SKILLS}:
                    logger.warning(f"Cannot import skill '{skill.id}': conflicts with built-in skill")
                    continue

                self.available_skills[skill.id] = skill
                skills.append(skill)
                logger.info(f"Imported skill from markdown: {skill.id}")

        if skills:
            self._save_custom_skills(self.available_skills)

        return skills

    def _parse_skill_block(self, block: str) -> Optional[Skill]:
        """Parse a single skill block from markdown content"""
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', block, re.DOTALL)

        if not frontmatter_match:
            logger.warning(f"Invalid skill block: missing frontmatter")
            return None

        frontmatter_text = frontmatter_match.group(1)
        rest_content = block[frontmatter_match.end():].strip()

        # Parse frontmatter
        skill_data = self._parse_frontmatter(frontmatter_text)
        if not skill_data:
            return None

        # Extract prompt from content (everything before ## Tools section)
        tools_section = None
        if '## Tools' in rest_content:
            parts = rest_content.split('## Tools')
            prompt_content = parts[0].strip()
            tools_section = parts[1].strip()
        else:
            # Remove markdown headers from prompt content
            prompt_content = re.sub(r'^#+\s+', '', rest_content).strip()

        skill_data['prompt'] = prompt_content

        # Parse tools if present
        if tools_section:
            skill_data['tools'] = self._parse_tools_section(tools_section)

        return Skill.from_dict(skill_data)

    def _parse_frontmatter(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse YAML-like frontmatter from text"""
        data = {}

        # Extract skill_id
        match = re.search(r'skill_id:\s*(.+)', text)
        if match:
            data['id'] = match.group(1).strip()
        else:
            # Try alternative: id:
            match = re.search(r'\bid:\s*(.+)', text)
            if match:
                data['id'] = match.group(1).strip()
            else:
                return None

        # Extract name
        match = re.search(r'name:\s*(.+)', text)
        if match:
            data['name'] = match.group(1).strip()

        # Extract description
        match = re.search(r'description:\s*(.+)', text)
        if match:
            data['description'] = match.group(1).strip()

        # Extract category
        match = re.search(r'category:\s*(.+)', text)
        if match:
            data['category'] = match.group(1).strip()
        else:
            data['category'] = 'custom'

        # Extract tags
        tags_match = re.search(r'tags:\s*\n((?:\s*-\s*.+\n)*)', text)
        if tags_match:
            tags_text = tags_match.group(1)
            data['tags'] = re.findall(r'-\s*(.+)', tags_text)

        data['is_custom'] = True
        return data

    def _parse_tools_section(self, section: str) -> List[Dict[str, Any]]:
        """Parse tools section from markdown content"""
        tools = []
        # Match tool definitions: ### tool_name\nDescription\n\n**Parameters:**\n- param (type): desc
        tool_pattern = r'###\s*(\w+)\s*\n([^**]+?)(?:\*\*Parameters:\*\*\s*\n((?:- .+?\n)*))?'

        for match in re.finditer(tool_pattern, section, re.DOTALL):
            tool_name = match.group(1)
            description = match.group(2).strip()

            tool_def = {
                'name': tool_name,
                'description': description,
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }

            # Parse parameters
            if match.group(3):
                param_text = match.group(3)
                for param_match in re.finditer(r'-\s*(\w+)\s*\(([^)]+)\):\s*(.+)', param_text):
                    param_name = param_match.group(1)
                    param_type = param_match.group(2)
                    param_desc = param_match.group(3)

                    tool_def['parameters']['properties'][param_name] = {
                        'type': param_type,
                        'description': param_desc.strip()
                    }
                    tool_def['parameters']['required'].append(param_name)

            tools.append(tool_def)

        return tools

    @staticmethod
    def parse_markdown_file(content: str) -> List[Dict[str, Any]]:
        """
        Static method to parse markdown content and return skill data dicts.
        Useful for preview before importing.
        """
        manager = SkillManager.__new__(SkillManager)
        manager.available_skills = {}
        skills = manager.import_skill_from_markdown(content)
        return [s.to_full_dict() for s in skills]
