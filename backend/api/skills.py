"""
Skill System API routes
Provides endpoints for listing, importing, activating, and deactivating agent skills
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Dict, Any, List, Optional

from backend.agents.skills import SkillManager
from backend.agents.a2a_manager import a2a_agent_manager

router = APIRouter(prefix="/api", tags=["skills"])

# Global skill manager for listing all available skills
_global_skill_manager = SkillManager()


@router.get("/skills")
async def list_skills(category: str = None):
    """List all available skills (built-in + custom)"""
    skills = _global_skill_manager.list_skills(category=category)
    return {
        "status": "success",
        "skills": skills,
        "total": len(skills),
    }


@router.post("/skills/import")
async def import_skill(skill_data: Dict[str, Any]):
    """
    Import a custom skill.

    Request body must contain:
    - id: unique skill identifier (e.g., "my_custom_skill")
    - name: display name
    - description: what the skill does
    - prompt: the system prompt injection text

    Optional fields:
    - category: skill category (default "custom")
    - tags: list of tag strings
    - tools: list of tool definitions
    """
    try:
        skill = _global_skill_manager.import_skill(skill_data)
        return {
            "status": "success",
            "message": f"Skill '{skill.id}' imported successfully",
            "skill": skill.to_full_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import skill: {e}")


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    """Delete a custom skill (built-in skills cannot be deleted)"""
    success = _global_skill_manager.delete_custom_skill(skill_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found or is a built-in skill (cannot delete)"
        )
    return {
        "status": "success",
        "message": f"Skill '{skill_id}' deleted",
    }


@router.post("/skills/import-file")
async def import_skills_from_file(
    file: UploadFile = File(...),
    mode: str = Form("import")  # "import" to save, "preview" to just show
):
    """
    Import skills from a markdown (.md) file.

    The file should follow the skill.md format:
    - Frontmatter with skill metadata
    - Prompt content
    - Optional tools definitions

    Args:
        file: The .md file to import
        mode: "import" to save skills, "preview" to just parse and return without saving
    """
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only .md files are supported")

    content = await file.read()
    try:
        content_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    try:
        if mode == "preview":
            # Parse but don't save
            skill_data = SkillManager.parse_markdown_file(content_text)
            return {
                "status": "success",
                "message": f"Preview: found {len(skill_data)} skill(s)",
                "skills": skill_data,
                "preview": True
            }
        else:
            # Import and save
            skills = _global_skill_manager.import_skill_from_markdown(content_text)
            return {
                "status": "success",
                "message": f"Imported {len(skills)} skill(s) successfully",
                "skills": [s.to_full_dict() for s in skills],
                "imported": len(skills)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse skill file: {str(e)}")


@router.post("/skills/parse")
async def parse_skill_content(content: Dict[str, str]):
    """
    Parse skill content from markdown text without saving.
    Useful for previewing before import.

    Request body:
        content: The markdown content to parse
    """
    content_text = content.get('content', '')
    if not content_text.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    try:
        skill_data = SkillManager.parse_markdown_file(content_text)
        return {
            "status": "success",
            "skills": skill_data,
            "count": len(skill_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse content: {str(e)}")


@router.get("/skills/{skill_id}")
async def get_skill_detail(skill_id: str):
    """Get full details of a skill including prompt and tools"""
    skill = _global_skill_manager.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
    return {
        "status": "success",
        "skill": skill.to_full_dict(),
    }


@router.get("/agents/{agent_id}/skills")
async def get_agent_skills(agent_id: str):
    """Get the active skills for a specific agent"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    active_ids = agent.skill_manager.get_active_skill_ids()
    active_skills = []
    for sid in active_ids:
        skill = agent.skill_manager.get_skill(sid)
        if skill:
            active_skills.append(skill.to_dict())

    return {
        "status": "success",
        "agent_id": agent_id,
        "active_skills": active_skills,
        "available_skills": agent.skill_manager.list_skills(),
    }


@router.post("/agents/{agent_id}/skills/{skill_id}/activate")
async def activate_skill(agent_id: str, skill_id: str):
    """Activate a skill for an agent"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    success = agent.skill_manager.activate_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")

    return {
        "status": "success",
        "message": f"Skill '{skill_id}' activated",
        "active_skills": agent.skill_manager.get_active_skill_ids(),
    }


@router.post("/agents/{agent_id}/skills/{skill_id}/deactivate")
async def deactivate_skill(agent_id: str, skill_id: str):
    """Deactivate a skill for an agent"""
    agent = await a2a_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    success = agent.skill_manager.deactivate_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' is not active")

    return {
        "status": "success",
        "message": f"Skill '{skill_id}' deactivated",
        "active_skills": agent.skill_manager.get_active_skill_ids(),
    }
