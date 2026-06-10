"""初始化系统提示词数据"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, SystemPreset
from config import settings

# 创建同步引擎用于初始化
sync_engine = create_engine(settings.database_url.replace('+aiosqlite', ''))
SessionLocal = sessionmaker(bind=sync_engine)

# 从 ai.py 提取的系统提示词
INITIAL_PROMPTS = [
    {
        "name": "卷级大纲生成",
        "prompt_type": "default",
        "prompt_role": "资深网文作家",
        "system_prompt": "你是一位资深网文作家，擅长{genre}小说创作。",
        "use_case": "plan_novel",
        "is_default": True
    },
    {
        "name": "章节级大纲生成",
        "prompt_type": "default",
        "prompt_role": "资深网文剧情编辑",
        "system_prompt": "你是一位资深网文剧情编辑，擅长把卷级剧情拆分为可执行的章节大纲。",
        "use_case": "generate_volume_chapters",
        "is_default": True
    },
    {
        "name": "角色提取",
        "prompt_type": "default",
        "prompt_role": "角色设计专家",
        "system_prompt": "你是一位角色设计专家，擅长从剧情中提取关键角色。",
        "use_case": "generate_characters",
        "is_default": True
    },
    {
        "name": "角色扩展",
        "prompt_type": "default",
        "prompt_role": "角色设计大师",
        "system_prompt": "你是一位角色设计大师，擅长创造立体丰满的人物形象。",
        "use_case": "expand_character",
        "is_default": True
    },
    {
        "name": "角色润色",
        "prompt_type": "default",
        "prompt_role": "角色设定编辑",
        "system_prompt": "你是一位小说角色设定编辑，擅长在不改变核心设定的前提下润色角色卡。",
        "use_case": "polish_character",
        "is_default": True
    },
    {
        "name": "大纲润色",
        "prompt_type": "default",
        "prompt_role": "资深网文剧情编辑",
        "system_prompt": "你是一位资深网文剧情编辑，擅长把章节大纲打磨成可直接写作的剧情蓝图。",
        "use_case": "polish_outline",
        "is_default": True
    },
    {
        "name": "章节正文生成",
        "prompt_type": "default",
        "prompt_role": "成熟网文作者",
        "system_prompt": "你是一位成熟网文作者，擅长根据章节大纲写出连贯、有张力的小说正文。",
        "use_case": "generate_chapter_content",
        "is_default": True
    },
    {
        "name": "章节正文改写",
        "prompt_type": "default",
        "prompt_role": "资深网文编辑",
        "system_prompt": "你是一位资深网文编辑，擅长根据反馈改写章节内容。",
        "use_case": "rewrite_chapter",
        "is_default": True
    },
    {
        "name": "选段改写",
        "prompt_type": "default",
        "prompt_role": "资深网文编辑",
        "system_prompt": "你是一位资深网文编辑，擅长改写指定文本片段。",
        "use_case": "rewrite_selection",
        "is_default": True
    },
    {
        "name": "章节润色",
        "prompt_type": "default",
        "prompt_role": "资深网文编辑",
        "system_prompt": "你是一位资深网文编辑，擅长润色小说正文。",
        "use_case": "polish_chapter",
        "is_default": True
    },
    {
        "name": "灵感对话",
        "prompt_type": "default",
        "prompt_role": "专业的小说创作助手",
        "system_prompt": """你是一位专业的小说创作助手，帮助作者完成创作的各个环节。
你的能力包括：
- 帮助作者梳理和完善故事创意
- 生成和优化剧情大纲
- 设计角色人物卡
- 创作小说片段和章节内容
- 分析故事结构和节奏
- 提供写作建议和灵感
与作者自然对话，倾听需求，提供专业建议。不要机械提问，根据对话灵活响应。""",
        "use_case": "inspiration_chat",
        "is_default": True
    }
]


def init_prompts():
    """初始化系统提示词数据"""
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing = db.query(SystemPreset).first()
        if existing:
            print("系统提示词已存在，跳过初始化")
            return

        # 插入初始数据
        for prompt_data in INITIAL_PROMPTS:
            prompt = SystemPreset(**prompt_data)
            db.add(prompt)

        db.commit()
        print(f"成功初始化 {len(INITIAL_PROMPTS)} 条系统提示词")
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_prompts()
