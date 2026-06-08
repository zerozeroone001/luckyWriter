from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
import json
import re
import time

from database import get_db
from models import Novel, Outline, Chapter, Character, AIGenerationLog, AIChannel, AIModel
from services import ai_service, context_manager


router = APIRouter(prefix="/api/ai", tags=["ai"])


# Pydantic模型
class PlanNovelRequest(BaseModel):
    novel_id: int
    target_words: int = 1000000
    target_chapters: int = 200
    target_volumes: int = 5
    genre: Optional[str] = None
    style_requirements: Optional[str] = None

    @field_validator("target_words", "target_chapters", "target_volumes")
    @classmethod
    def validate_positive_number(cls, value: int) -> int:
        """校验一键规划目标数值必须为正数。"""
        if value <= 0:
            raise ValueError("目标字数、章节数和卷数必须大于 0")
        return value

    @model_validator(mode="after")
    def validate_volume_count(self) -> "PlanNovelRequest":
        """校验目标卷数不能超过目标章节数。"""
        if self.target_volumes > self.target_chapters:
            raise ValueError("目标卷数不能大于目标章节数")
        return self


class GenerateCharactersRequest(BaseModel):
    novel_id: int
    outline_text: str
    character_count: int = 12


class ExpandCharacterRequest(BaseModel):
    character_id: int
    novel_id: int


class PolishCharacterRequest(BaseModel):
    character_id: int
    novel_id: int


class GenerateCharacterImageRequest(BaseModel):
    character_id: int
    style: str = "realistic"


class GenerateContentRequest(BaseModel):
    novel_id: int
    chapter_id: int
    target_words: int = 3000


class PolishOutlineRequest(BaseModel):
    novel_id: int
    outline_id: int
    polish_requirements: Optional[str] = None
    save: bool = True


class GenerateChapterContentRequest(BaseModel):
    novel_id: int
    outline_id: int
    chapter_id: Optional[int] = None
    target_words: int = 3000
    writing_requirements: Optional[str] = None
    save: bool = True

    @field_validator("target_words")
    @classmethod
    def validate_target_words(cls, value: int) -> int:
        """校验章节正文目标字数必须为正数。"""
        if value <= 0:
            raise ValueError("目标字数必须大于 0")
        return value


class RewriteChapterContentRequest(BaseModel):
    novel_id: int
    chapter_id: int
    rewrite_requirements: Optional[str] = None
    save: bool = True


class RewriteChapterSelectionRequest(BaseModel):
    novel_id: int
    chapter_id: int
    selected_text: str
    rewrite_requirements: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None

    @field_validator("selected_text")
    @classmethod
    def validate_selected_text(cls, value: str) -> str:
        """校验局部改写选区不能为空。"""
        selected_text = value.strip()
        if not selected_text:
            raise ValueError("选中文本不能为空")
        return selected_text


class PolishChapterContentRequest(BaseModel):
    novel_id: int
    chapter_id: int
    style_requirements: Optional[str] = None
    save: bool = True


async def get_enabled_ai_model(db: AsyncSession) -> tuple[AIChannel, AIModel]:
    """获取当前可用的 AI 渠道和模型。"""
    result = await db.execute(
        select(AIChannel, AIModel)
        .join(AIModel, AIModel.channel_id == AIChannel.id)
        .where(AIChannel.is_enabled == True, AIModel.is_enabled == True)
        .order_by(
            AIModel.response_time_ms.is_(None),
            AIModel.response_time_ms.asc(),
            AIModel.created_at.desc(),
        )
        .limit(1)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=500, detail="没有可用的AI模型，请先在渠道中启用模型")

    return row


@router.post("/plan-novel/stream")
async def plan_novel_outline_stream(
    request: PlanNovelRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    一键规划小说大纲（流式输出）
    生成：卷结构 + 章节标题 + 情节要点 + 角色列表
    """
    # 获取小说信息
    result = await db.execute(
        select(Novel).where(Novel.id == request.novel_id)
    )
    novel = result.scalar_one_or_none()

    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    base_chapters_per_volume = request.target_chapters // request.target_volumes
    extra_chapter_volumes = request.target_chapters % request.target_volumes
    chapter_distribution = (
        f"前{extra_chapter_volumes}卷每卷约{base_chapters_per_volume + 1}章，"
        f"其余卷每卷约{base_chapters_per_volume}章"
        if extra_chapter_volumes
        else f"每卷约{base_chapters_per_volume}章"
    )
    character_count = max(3, request.target_chapters // 15)

    # 构建提示词
    prompt = f"""请为以下小说规划完整大纲：

标题：{novel.title}
类型：{request.genre or novel.genre or "未指定"}
目标字数：{request.target_words}字
目标章节数：{request.target_chapters}章
目标卷数：{request.target_volumes}卷
章节分配：{chapter_distribution}
简介：{novel.synopsis or "暂无"}
风格要求：{request.style_requirements or "无特殊要求"}

请严格按以下 Markdown 格式输出，卷号和章节号必须使用阿拉伯数字，章节号必须是全书连续编号：

## 第1卷：卷标题
### 卷概要
用 2-4 句话概括本卷核心冲突、转折和结局。

### 关键事件
- 关键事件1
- 关键事件2
- 关键事件3

### 章节列表
1. 第1章：章节标题 - 简要情节
2. 第2章：章节标题 - 简要情节

## 第2卷：卷标题
### 卷概要
用 2-4 句话概括本卷核心冲突、转折和结局。

### 关键事件
- 关键事件1
- 关键事件2
- 关键事件3

### 章节列表
3. 第3章：章节标题 - 简要情节
4. 第4章：章节标题 - 简要情节

## 角色列表
1. 角色名 - 性别 - 年龄 - 角色类型 - 一句话介绍
2. 角色名 - 性别 - 年龄 - 角色类型 - 一句话介绍

要求：
1. 必须输出共{request.target_volumes}卷、共{request.target_chapters}章。
2. 每章标题要有吸引力，简要情节控制在 30-80 字。
3. 卷概要要体现阶段目标、核心矛盾、高潮节点和结尾钩子。
4. 提取约{character_count}个主要角色。
5. 角色类型包括：主角、主要配角、次要配角、反派等。
"""

    system_prompt = f"你是一位资深网文作家，擅长{request.genre or '各类'}小说创作。"

    channel, model = await get_enabled_ai_model(db)

    # 流式生成
    async def generate_stream():
        accumulated_text = []
        start_time = time.time()

        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=model.temperature,
                max_tokens=4000,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            # 生成完成，解析并保存
            full_text = "".join(accumulated_text)
            duration = time.time() - start_time

            # 解析大纲结构（简单实现，按格式提取）
            outlines_created = await _parse_and_save_outline(
                db, request.novel_id, full_text
            )

            # 记录日志
            log = AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="outline",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=duration,
                status="success",
            )
            db.add(log)
            await db.commit()

            yield f"data: {json.dumps({'type': 'done', 'result': {'outlines_count': outlines_created}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


VOLUME_HEADING_PATTERN = re.compile(
    r"^#{1,3}\s*第\s*([0-9零〇一二两三四五六七八九十百千万]+)\s*卷\s*[：:]\s*(.+?)\s*$",
    re.MULTILINE,
)
CHAPTER_LINE_PATTERN = re.compile(
    r"^\s*(?:(?:\d+|[零〇一二两三四五六七八九十百千万]+)[.、)]\s*)?"
    r"第\s*([0-9零〇一二两三四五六七八九十百千万]+)\s*章\s*[：:]\s*"
    r"(.+?)(?:\s*[-—–－]\s*(.+))?\s*$"
)
NUMBERED_CHAPTER_LINE_PATTERN = re.compile(
    r"^\s*(\d+|[零〇一二两三四五六七八九十百千万]+)[.、)]\s*"
    r"(.+?)(?:\s*[-—–－]\s*(.+))?\s*$"
)
CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
CHINESE_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}


async def _parse_and_save_outline(db: AsyncSession, novel_id: int, text: str) -> int:
    """解析并保存 AI 生成的大纲到数据库。"""
    outline_items = _parse_outline_items(text)
    if not outline_items:
        raise ValueError("未解析到有效大纲内容")

    for item in outline_items:
        db.add(Outline(novel_id=novel_id, **item))

    await db.commit()
    return len(outline_items)


def _parse_outline_items(text: str) -> list[dict[str, object]]:
    """将 AI 生成文本解析为可保存的大纲条目。"""
    items: list[dict[str, object]] = []
    volume_sections = _split_volume_sections(text)
    next_chapter_number = 1

    for index, (volume_number_text, volume_title, volume_content) in enumerate(volume_sections, start=1):
        volume_number = _parse_outline_number(volume_number_text) or index
        key_events = _extract_bullet_items(_extract_markdown_section(volume_content, ["关键事件", "情节要点"]))
        volume_summary = _extract_markdown_section(volume_content, ["卷概要", "情节概要", "情节要点"])
        if not volume_summary and key_events:
            volume_summary = "\n".join(key_events[:5])

        items.append(
            {
                "volume_number": volume_number,
                "chapter_number": None,
                "title": volume_title.strip() or f"第{volume_number}卷",
                "plot_summary": volume_summary.strip() if volume_summary else "",
                "key_events": "\n".join(key_events) if key_events else None,
                "characters_involved": None,
                "outline_type": "volume",
            }
        )

        chapter_section = _extract_markdown_section(volume_content, ["章节列表", "章节规划"])
        chapter_source = chapter_section or volume_content
        chapter_items, next_chapter_number = _parse_chapter_items(
            chapter_source,
            volume_number,
            next_chapter_number,
        )
        items.extend(chapter_items)

    return items


def _split_volume_sections(text: str) -> list[tuple[str, str, str]]:
    """按卷标题切分 AI 输出文本。"""
    matches = list(VOLUME_HEADING_PATTERN.finditer(text))
    sections = []

    for index, match in enumerate(matches):
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = _remove_role_list_section(text[content_start:content_end])
        sections.append((match.group(1), match.group(2).strip(), content.strip()))

    return sections


def _remove_role_list_section(text: str) -> str:
    """移除最后一卷后可能拼接进来的角色列表内容。"""
    role_match = re.search(r"^#{1,3}\s*角色列表\s*$", text, re.MULTILINE)
    return text[: role_match.start()] if role_match else text


def _parse_chapter_items(
    text: str,
    volume_number: int,
    next_chapter_number: int,
) -> tuple[list[dict[str, object]], int]:
    """解析章节列表文本为章节级大纲条目。"""
    items: list[dict[str, object]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        chapter_number, title, summary = _parse_chapter_line(line)
        if not title:
            continue

        if chapter_number is None:
            chapter_number = next_chapter_number

        items.append(
            {
                "volume_number": volume_number,
                "chapter_number": chapter_number,
                "title": title,
                "plot_summary": summary or "",
                "key_events": None,
                "characters_involved": None,
                "outline_type": "chapter",
            }
        )
        next_chapter_number = max(next_chapter_number, chapter_number + 1)

    return items, next_chapter_number


def _parse_chapter_line(line: str) -> tuple[int | None, str, str]:
    """解析单行章节文本。"""
    match = CHAPTER_LINE_PATTERN.match(line)
    if match:
        chapter_number_text, title, summary = match.groups()
        return _parse_outline_number(chapter_number_text), title.strip(), (summary or "").strip()

    match = NUMBERED_CHAPTER_LINE_PATTERN.match(line)
    if not match:
        return None, "", ""

    list_number_text, title, summary = match.groups()
    return _parse_outline_number(list_number_text), title.strip(), (summary or "").strip()


def _extract_markdown_section(text: str, headings: list[str]) -> str:
    """提取指定三级标题下的 Markdown 内容。"""
    escaped_headings = "|".join(re.escape(heading) for heading in headings)
    pattern = re.compile(
        rf"^###\s*(?:{escaped_headings})\s*$\n(?P<content>.*?)(?=^###\s+|^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group("content").strip() if match else ""


def _extract_bullet_items(text: str) -> list[str]:
    """提取 Markdown 列表中的条目文本。"""
    items = []
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if match:
            items.append(match.group(1).strip())
    return items


def _parse_outline_number(value: str) -> int | None:
    """解析阿拉伯数字或中文数字。"""
    normalized_value = value.strip()
    if normalized_value.isdigit():
        return int(normalized_value)

    total = 0
    section = 0
    number = 0
    parsed = False

    for char in normalized_value:
        if char in CHINESE_DIGITS:
            number = CHINESE_DIGITS[char]
            parsed = True
            continue

        unit = CHINESE_UNITS.get(char)
        if not unit:
            return None

        parsed = True
        if unit == 10000:
            section = (section + number) * unit
            total += section
            section = 0
        else:
            section += (number or 1) * unit
        number = 0

    if not parsed:
        return None

    return total + section + number


@router.post("/generate-characters/stream")
async def generate_characters_stream(
    request: GenerateCharactersRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    批量生成简要角色卡（流式输出）
    从大纲中提取角色，生成简要信息
    """
    # 获取小说信息
    result = await db.execute(
        select(Novel).where(Novel.id == request.novel_id)
    )
    novel = result.scalar_one_or_none()

    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    # 构建提示词
    prompt = f"""根据以下小说大纲，提取{request.character_count}个主要角色：

{request.outline_text}

请按以下格式输出每个角色（一行一个）：
角色名|性别|年龄|角色类型|一句话介绍

例如：
张三|男|25岁|主角|天赋异禀的修仙者，立志成为最强
李四|女|23岁|女主|冰山美人，实则内心火热
王五|男|50岁|反派|阴险狡诈的邪教教主

要求：
1. 提取{request.character_count}个角色
2. 角色类型包括：主角、女主、主要配角、次要配角、反派
3. 简介控制在20字以内
"""

    system_prompt = "你是一位角色设计专家，擅长从剧情中提取关键角色。"

    channel, model = await get_enabled_ai_model(db)

    # 流式生成
    async def generate_stream():
        accumulated_text = []
        start_time = time.time()

        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=model.temperature,
                max_tokens=2000,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            # 生成完成，解析并保存
            full_text = "".join(accumulated_text)
            duration = time.time() - start_time

            # 解析角色
            characters_created = await _parse_and_save_characters(
                db, request.novel_id, full_text
            )

            # 记录日志
            log = AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="character",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=duration,
                status="success",
            )
            db.add(log)
            await db.commit()

            yield f"data: {json.dumps({'type': 'done', 'result': {'characters_count': characters_created}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


async def _parse_and_save_characters(db: AsyncSession, novel_id: int, text: str) -> int:
    """解析并保存角色到数据库"""
    import re

    characters_created = 0

    # 按行分割
    lines = text.strip().split('\n')

    for line in lines:
        # 匹配格式：角色名|性别|年龄|角色类型|一句话介绍
        match = re.match(r'(.+?)\|(.+?)\|(.+?)\|(.+?)\|(.+)', line.strip())

        if match:
            name, gender, age, char_type, intro = match.groups()

            # 判断重要性
            importance = "main" if "主角" in char_type or "女主" in char_type else \
                        "major" if "主要" in char_type or "反派" in char_type else "minor"

            character = Character(
                novel_id=novel_id,
                name=name.strip(),
                gender=gender.strip(),
                age=age.strip(),
                identity_info=intro.strip(),
                importance=importance,
                is_detailed=False,
            )
            db.add(character)
            characters_created += 1

    await db.commit()
    return characters_created


@router.post("/expand-character/stream")
async def expand_character_stream(
    request: ExpandCharacterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    扩展角色卡详细信息（流式输出）
    为选中的角色生成详细的角色卡
    """
    # 获取角色
    result = await db.execute(
        select(Character).where(Character.id == request.character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 获取小说信息
    novel_result = await db.execute(
        select(Novel).where(Novel.id == request.novel_id)
    )
    novel = novel_result.scalar_one_or_none()

    # 构建提示词
    prompt = f"""请为以下角色扩展详细信息：

小说：{novel.title if novel else ""}
类型：{novel.genre if novel else ""}
角色名：{character.name}
性别：{character.gender}
年龄：{character.age}
简介：{character.identity_info}

请按以下格式输出：

## 外貌身材
[详细描述，100-200字]

## 性格特点
[详细描述，100-150字]

## 背景故事
[详细描述，200-300字]

## 人物关系
[与其他角色的关系，100-150字]

## 能力特长
[特殊能力、技能等，100-150字]

## 角色成长线
[在故事中的发展轨迹，100-150字]

## 经典语录
- 语录1
- 语录2
- 语录3
"""

    system_prompt = "你是一位角色设计大师，擅长创造立体丰满的人物形象。"

    channel, model = await get_enabled_ai_model(db)

    # 流式生成
    async def generate_stream():
        accumulated_text = []
        start_time = time.time()

        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=0.8,
                max_tokens=2000,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            # 生成完成，解析并更新
            full_text = "".join(accumulated_text)
            duration = time.time() - start_time

            # 解析并更新角色卡
            await _parse_and_update_character(db, character, full_text)

            # 记录日志
            log = AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="character",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=duration,
                status="success",
            )
            db.add(log)
            await db.commit()

            yield f"data: {json.dumps({'type': 'done', 'result': {'character_id': character.id}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/polish-character/stream")
async def polish_character_stream(
    request: PolishCharacterRequest,
    db: AsyncSession = Depends(get_db),
):
    """润色单个角色卡（流式输出）。"""
    result = await db.execute(select(Character).where(Character.id == request.character_id))
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    novel_result = await db.execute(select(Novel).where(Novel.id == request.novel_id))
    novel = novel_result.scalar_one_or_none()

    prompt = f"""请润色以下单个角色卡，不要处理其它角色，也不要新增角色。

小说：{novel.title if novel else ""}
类型：{novel.genre if novel else ""}
角色名：{character.name}
性别：{character.gender or "未填写"}
年龄：{character.age or "未填写"}
重要性：{character.importance}
身份简介：{character.identity_info or "暂无"}
外貌身材：{character.appearance or "暂无"}
性格特点：{character.personality or "暂无"}
背景故事：{character.background or "暂无"}
人物关系：{character.relationships or "暂无"}
能力特长：{character.abilities or "暂无"}
角色成长线：{character.character_arc or "暂无"}
经典语录：{character.quotes or "暂无"}

要求：
1. 只润色这个角色，保持角色名、性别、年龄和核心身份不变。
2. 可以补足缺失内容、优化表达、增强文学性和一致性。
3. 不要引入与原设定冲突的新关系或新能力。
4. 严格按以下 Markdown 标题输出，不要输出解释说明。

## 身份简介
[润色后的身份简介，30-80字]

## 外貌身材
[润色后的外貌身材，80-180字]

## 性格特点
[润色后的性格特点，80-160字]

## 背景故事
[润色后的背景故事，120-260字]

## 人物关系
[润色后的人物关系，80-180字]

## 能力特长
[润色后的能力特长，80-180字]

## 角色成长线
[润色后的角色成长线，80-180字]

## 经典语录
- 语录1
- 语录2
- 语录3
"""

    system_prompt = "你是一位小说角色设定编辑，擅长在不改变核心设定的前提下润色角色卡。"
    channel, model = await get_enabled_ai_model(db)

    async def generate_stream():
        accumulated_text = []
        start_time = time.time()

        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=0.7,
                max_tokens=2200,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            full_text = "".join(accumulated_text)
            duration = time.time() - start_time

            await _parse_and_update_character(db, character, full_text)

            log = AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="character",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=duration,
                status="success",
            )
            db.add(log)
            await db.commit()

            yield f"data: {json.dumps({'type': 'done', 'result': {'character_id': character.id}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


async def _parse_and_update_character(db: AsyncSession, character: Character, text: str):
    """解析并更新角色详细信息。"""

    # 提取各部分内容
    identity_match = re.search(r'## 身份简介\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)
    appearance_match = re.search(r'## 外貌身材\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)
    personality_match = re.search(r'## 性格特点\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)
    background_match = re.search(r'## 背景故事\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)
    relationships_match = re.search(r'## 人物关系\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)
    abilities_match = re.search(r'## 能力特长\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)
    arc_match = re.search(r'## 角色成长线\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)
    quotes_match = re.search(r'## 经典语录\s*\n(.+?)(?=\n##|$)', text, re.DOTALL)

    # 更新字段
    if identity_match:
        character.identity_info = identity_match.group(1).strip()
    if appearance_match:
        character.appearance = appearance_match.group(1).strip()
    if personality_match:
        character.personality = personality_match.group(1).strip()
    if background_match:
        character.background = background_match.group(1).strip()
    if relationships_match:
        character.relationships = relationships_match.group(1).strip()
    if abilities_match:
        character.abilities = abilities_match.group(1).strip()
    if arc_match:
        character.character_arc = arc_match.group(1).strip()
    if quotes_match:
        character.quotes = quotes_match.group(1).strip()

    character.is_detailed = True
    await db.commit()


async def _get_novel_or_404(db: AsyncSession, novel_id: int) -> Novel:
    """根据小说 ID 获取小说，找不到时返回 404。"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    return novel


async def _get_outline_or_404(db: AsyncSession, outline_id: int, novel_id: int) -> Outline:
    """根据大纲 ID 和小说 ID 获取大纲，找不到时返回 404。"""
    result = await db.execute(
        select(Outline).where(Outline.id == outline_id, Outline.novel_id == novel_id)
    )
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(status_code=404, detail="大纲不存在")
    return outline


async def _get_chapter_or_404(db: AsyncSession, chapter_id: int, novel_id: int) -> Chapter:
    """根据章节 ID 和小说 ID 获取章节，找不到时返回 404。"""
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.novel_id == novel_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return chapter


async def _get_chapter_outline_for_chapter(db: AsyncSession, chapter: Chapter) -> Outline | None:
    """根据章节卷号和章号查找对应章节级大纲。"""
    result = await db.execute(
        select(Outline)
        .where(
            Outline.novel_id == chapter.novel_id,
            Outline.outline_type == "chapter",
            Outline.volume_number == chapter.volume_number,
            Outline.chapter_number == chapter.chapter_number,
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_adjacent_outline_context(db: AsyncSession, outline: Outline) -> str:
    """获取当前大纲前后章节的简要上下文。"""
    result = await db.execute(
        select(Outline)
        .where(Outline.novel_id == outline.novel_id, Outline.outline_type == "chapter")
        .order_by(
            Outline.volume_number.is_(None),
            Outline.volume_number.asc(),
            Outline.chapter_number.is_(None),
            Outline.chapter_number.asc(),
            Outline.id.asc(),
        )
    )
    outlines = result.scalars().all()
    current_index = next((index for index, item in enumerate(outlines) if item.id == outline.id), -1)
    if current_index == -1:
        return "无"

    neighbors = []
    for item in outlines[max(0, current_index - 1):current_index + 2]:
        marker = "当前" if item.id == outline.id else "相邻"
        neighbors.append(
            f"{marker}：第{item.volume_number or 1}卷 第{item.chapter_number or '?'}章《{item.title}》：{item.plot_summary or '暂无梗概'}"
        )
    return "\n".join(neighbors)


async def _get_character_context(db: AsyncSession, novel_id: int) -> str:
    """获取小说主要角色简表。"""
    result = await db.execute(
        select(Character)
        .where(Character.novel_id == novel_id)
        .order_by(Character.importance.asc(), Character.id.asc())
        .limit(12)
    )
    characters = result.scalars().all()
    if not characters:
        return "暂无角色卡"

    return "\n".join(
        f"- {character.name}（{character.gender or '未知'}，{character.age or '年龄未知'}，{character.identity_info or '暂无简介'}）"
        for character in characters
    )


def _format_outline_context(outline: Outline) -> str:
    """格式化单个章节大纲上下文。"""
    return f"""第{outline.volume_number or 1}卷 第{outline.chapter_number or '?'}章
标题：{outline.title}
情节梗概：{outline.plot_summary or '暂无'}
关键事件：{outline.key_events or '暂无'}
涉及角色：{outline.characters_involved or '暂无'}"""


def _extract_ai_section(text: str, headings: list[str]) -> str:
    """提取 AI 返回中的二级或三级 Markdown 标题内容。"""
    escaped_headings = "|".join(re.escape(heading) for heading in headings)
    pattern = re.compile(
        rf"^##+\s*(?:{escaped_headings})\s*$\n(?P<content>.*?)(?=^##+\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group("content").strip() if match else ""


def _clean_generated_content(text: str) -> str:
    """清理 AI 正文输出中的包裹标题和 Markdown 代码块。"""
    content = text.strip()
    content = re.sub(r"^```(?:markdown|text)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content).strip()
    content = re.sub(r"^#\s*正文\s*\n", "", content).strip()
    content = re.sub(r"^##\s*正文\s*\n", "", content).strip()
    return content


def _update_chapter_content(chapter: Chapter, content: str) -> None:
    """更新章节正文并同步字数。"""
    chapter.content = content
    chapter.word_count = len(content)


async def _find_or_create_chapter_for_outline(
    db: AsyncSession,
    novel_id: int,
    outline: Outline,
    chapter_id: int | None,
) -> Chapter:
    """根据大纲查找或创建正文承载章节。"""
    if chapter_id:
        return await _get_chapter_or_404(db, chapter_id, novel_id)

    result = await db.execute(
        select(Chapter).where(
            Chapter.novel_id == novel_id,
            Chapter.volume_number == (outline.volume_number or 1),
            Chapter.chapter_number == outline.chapter_number,
        )
    )
    chapter = result.scalar_one_or_none()
    if chapter:
        return chapter

    chapter = Chapter(
        novel_id=novel_id,
        volume_number=outline.volume_number or 1,
        chapter_number=outline.chapter_number or 1,
        title=outline.title,
        content="",
        word_count=0,
        status="draft",
    )
    db.add(chapter)
    await db.flush()
    return chapter


def _text_streaming_response(generator):
    """创建文本事件流响应。"""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/polish-outline/stream")
async def polish_outline_stream(
    request: PolishOutlineRequest,
    db: AsyncSession = Depends(get_db),
):
    """润色单个章节级剧情大纲，并将结果保存回大纲。"""
    novel = await _get_novel_or_404(db, request.novel_id)
    outline = await _get_outline_or_404(db, request.outline_id, request.novel_id)
    if outline.outline_type != "chapter":
        raise HTTPException(status_code=422, detail="只能润色章节级大纲")

    adjacent_context = await _get_adjacent_outline_context(db, outline)
    character_context = await _get_character_context(db, request.novel_id)
    prompt = f"""请润色以下小说章节剧情大纲，使其更适合后续正文写作。

小说：{novel.title}
类型：{novel.genre or '未指定'}
简介：{novel.synopsis or '暂无'}

当前大纲：
{_format_outline_context(outline)}

前后文：
{adjacent_context}

主要角色：
{character_context}

用户修改建议：{request.polish_requirements or '无'}

要求：
1. 保持卷号、章节号、章节标题和核心剧情方向不变。
2. 强化冲突、转折、人物动机和章节钩子。
3. 不要写正文，只润色剧情大纲。
4. 严格按以下 Markdown 标题输出。

## 情节梗概
[120-260字]

## 关键事件
- 事件1
- 事件2
- 事件3

## 涉及角色
[角色及其本章作用]
"""
    system_prompt = "你是一位资深网文剧情编辑，擅长把章节大纲打磨成可直接写作的剧情蓝图。"
    channel, model = await get_enabled_ai_model(db)

    async def generate_stream():
        accumulated_text = []
        start_time = time.time()
        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=0.7,
                max_tokens=1800,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            full_text = "".join(accumulated_text)
            if request.save:
                outline.plot_summary = _extract_ai_section(full_text, ["情节梗概"]) or outline.plot_summary
                outline.key_events = _extract_ai_section(full_text, ["关键事件"]) or outline.key_events
                outline.characters_involved = _extract_ai_section(full_text, ["涉及角色"]) or outline.characters_involved
            db.add(AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="outline_polish",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=time.time() - start_time,
                status="success",
            ))
            await db.commit()
            yield f"data: {json.dumps({'type': 'done', 'result': {'outline_id': outline.id, 'content': full_text}}, ensure_ascii=False)}\n\n"
        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return _text_streaming_response(generate_stream())


@router.post("/generate-chapter-content/stream")
async def generate_chapter_content_stream(
    request: GenerateChapterContentRequest,
    db: AsyncSession = Depends(get_db),
):
    """根据章节大纲生成正文，必要时创建对应章节。"""
    novel = await _get_novel_or_404(db, request.novel_id)
    outline = await _get_outline_or_404(db, request.outline_id, request.novel_id)
    if outline.outline_type != "chapter":
        raise HTTPException(status_code=422, detail="只能根据章节级大纲生成正文")

    adjacent_context = await _get_adjacent_outline_context(db, outline)
    character_context = await _get_character_context(db, request.novel_id)
    prompt = f"""请根据章节大纲创作小说正文。

小说：{novel.title}
类型：{novel.genre or '未指定'}
简介：{novel.synopsis or '暂无'}
目标字数：约{request.target_words}字

当前章节大纲：
{_format_outline_context(outline)}

前后文：
{adjacent_context}

主要角色：
{character_context}

用户写作建议：{request.writing_requirements or '无'}

要求：
1. 只输出本章正文，不要输出分析、标题说明或 Markdown 解释。
2. 正文要符合章节大纲，不要跳过关键事件。
3. 叙事要有场景、动作、对话、心理和章节钩子。
4. 不要改写其它章节剧情。
"""
    system_prompt = "你是一位成熟网文作者，擅长根据章节大纲写出连贯、有张力的小说正文。"
    channel, model = await get_enabled_ai_model(db)

    async def generate_stream():
        accumulated_text = []
        start_time = time.time()
        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=0.85,
                max_tokens=6000,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            full_text = _clean_generated_content("".join(accumulated_text))
            chapter_id = request.chapter_id
            if request.save:
                chapter = await _find_or_create_chapter_for_outline(db, request.novel_id, outline, request.chapter_id)
                chapter.title = chapter.title or outline.title
                _update_chapter_content(chapter, full_text)
                await db.flush()
                chapter_id = chapter.id
            db.add(AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="content_generate",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=time.time() - start_time,
                status="success",
            ))
            await db.commit()
            yield f"data: {json.dumps({'type': 'done', 'result': {'chapter_id': chapter_id, 'content': full_text}}, ensure_ascii=False)}\n\n"
        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return _text_streaming_response(generate_stream())


@router.post("/rewrite-chapter-content/stream")
async def rewrite_chapter_content_stream(
    request: RewriteChapterContentRequest,
    db: AsyncSession = Depends(get_db),
):
    """根据当前章节正文和大纲重写正文，并覆盖保存。"""
    novel = await _get_novel_or_404(db, request.novel_id)
    chapter = await _get_chapter_or_404(db, request.chapter_id, request.novel_id)
    if not chapter.content:
        raise HTTPException(status_code=422, detail="当前章节没有正文，无法重写")

    outline = await _get_chapter_outline_for_chapter(db, chapter)
    outline_context = _format_outline_context(outline) if outline else "暂无对应大纲"
    character_context = await _get_character_context(db, request.novel_id)
    prompt = f"""请重写以下小说章节正文。

小说：{novel.title}
类型：{novel.genre or '未指定'}
章节：第{chapter.volume_number}卷 第{chapter.chapter_number}章《{chapter.title}》

对应大纲：
{outline_context}

主要角色：
{character_context}

原正文：
{chapter.content}

重写要求：{request.rewrite_requirements or '增强可读性、冲突和画面感，保持核心剧情不变'}

要求：
1. 只输出重写后的正文，不要输出说明。
2. 保留本章核心剧情、人物关系和重要信息。
3. 可以调整表达、节奏、对话和细节，让正文更流畅。
"""
    system_prompt = "你是一位小说改稿编辑，擅长在保留核心剧情的前提下重写章节正文。"
    channel, model = await get_enabled_ai_model(db)

    async def generate_stream():
        accumulated_text = []
        start_time = time.time()
        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=0.75,
                max_tokens=6000,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            full_text = _clean_generated_content("".join(accumulated_text))
            if request.save:
                _update_chapter_content(chapter, full_text)
            db.add(AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="content_rewrite",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=time.time() - start_time,
                status="success",
            ))
            await db.commit()
            yield f"data: {json.dumps({'type': 'done', 'result': {'chapter_id': chapter.id, 'content': full_text}}, ensure_ascii=False)}\n\n"
        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return _text_streaming_response(generate_stream())


@router.post("/rewrite-chapter-selection/stream")
async def rewrite_chapter_selection_stream(
    request: RewriteChapterSelectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """根据阅读正文选区生成局部替换片段，不直接保存章节。"""
    novel = await _get_novel_or_404(db, request.novel_id)
    chapter = await _get_chapter_or_404(db, request.chapter_id, request.novel_id)
    if not chapter.content:
        raise HTTPException(status_code=422, detail="当前章节没有正文，无法局部改写")
    if request.selected_text not in chapter.content:
        raise HTTPException(status_code=422, detail="选中文本不在当前章节正文中，请重新选择")

    outline = await _get_chapter_outline_for_chapter(db, chapter)
    outline_context = _format_outline_context(outline) if outline else "暂无对应大纲"
    character_context = await _get_character_context(db, request.novel_id)
    prompt = f"""请根据修改意见改写小说章节中的选中文本。

小说：{novel.title}
类型：{novel.genre or '未指定'}
章节：第{chapter.volume_number}卷 第{chapter.chapter_number}章《{chapter.title}》

对应大纲：
{outline_context}

主要角色：
{character_context}

选区前文：
{request.context_before or '无'}

需要替换的选中文本：
{request.selected_text}

选区后文：
{request.context_after or '无'}

修改意见：{request.rewrite_requirements or '在保持剧情和人物信息一致的前提下，让表达更自然、有画面感'}

要求：
1. 只输出用于替换选中文本的正文片段，不要输出说明、标题或 Markdown。
2. 不要复述选区前文或后文，只改写选中文本对应内容。
3. 改写后的片段要能与前后文自然衔接。
4. 保持角色、剧情事实和叙事视角一致。
"""
    system_prompt = "你是一位小说局部改稿编辑，擅长在保持上下文连贯的前提下改写选中文本。"
    channel, model = await get_enabled_ai_model(db)

    async def generate_stream():
        accumulated_text = []
        start_time = time.time()
        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=0.7,
                max_tokens=3000,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            full_text = _clean_generated_content("".join(accumulated_text))
            db.add(AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="content_selection_rewrite",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=time.time() - start_time,
                status="success",
            ))
            await db.commit()
            yield f"data: {json.dumps({'type': 'done', 'result': {'chapter_id': chapter.id, 'content': full_text}}, ensure_ascii=False)}\n\n"
        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return _text_streaming_response(generate_stream())


@router.post("/polish-chapter-content/stream")
async def polish_chapter_content_stream(
    request: PolishChapterContentRequest,
    db: AsyncSession = Depends(get_db),
):
    """润色当前章节正文，并覆盖保存。"""
    novel = await _get_novel_or_404(db, request.novel_id)
    chapter = await _get_chapter_or_404(db, request.chapter_id, request.novel_id)
    if not chapter.content:
        raise HTTPException(status_code=422, detail="当前章节没有正文，无法润色")

    outline = await _get_chapter_outline_for_chapter(db, chapter)
    outline_context = _format_outline_context(outline) if outline else "暂无对应大纲"
    prompt = f"""请润色以下小说章节正文。

小说：{novel.title}
类型：{novel.genre or '未指定'}
章节：第{chapter.volume_number}卷 第{chapter.chapter_number}章《{chapter.title}》

对应大纲：
{outline_context}

原正文：
{chapter.content}

润色要求：{request.style_requirements or '提升文字表现力、节奏、对话自然度和画面感'}

要求：
1. 只输出润色后的正文，不要输出说明。
2. 不改变核心剧情、人物动机和章节结局。
3. 保留原正文的重要信息，优化语言和节奏。
"""
    system_prompt = "你是一位小说文字润色编辑，擅长提升正文质感但不改变剧情。"
    channel, model = await get_enabled_ai_model(db)

    async def generate_stream():
        accumulated_text = []
        start_time = time.time()
        try:
            async for chunk in ai_service.generate_streaming(
                prompt=prompt,
                system_prompt=system_prompt,
                provider=channel.provider,
                model=model.model_id,
                temperature=0.65,
                max_tokens=6000,
                api_key=channel.api_key,
                base_url=channel.base_url,
            ):
                accumulated_text.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            full_text = _clean_generated_content("".join(accumulated_text))
            if request.save:
                _update_chapter_content(chapter, full_text)
            db.add(AIGenerationLog(
                novel_id=request.novel_id,
                model_id=model.id,
                generation_type="content_polish",
                input_tokens=len(prompt) // 4,
                output_tokens=len(full_text) // 4,
                duration_seconds=time.time() - start_time,
                status="success",
            ))
            await db.commit()
            yield f"data: {json.dumps({'type': 'done', 'result': {'chapter_id': chapter.id, 'content': full_text}}, ensure_ascii=False)}\n\n"
        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return _text_streaming_response(generate_stream())


@router.post("/generate-character-image")
async def generate_character_image(
    request: GenerateCharacterImageRequest,
    db: AsyncSession = Depends(get_db),
):
    """生成角色形象图片（DALL-E 3）"""
    # 获取角色
    result = await db.execute(
        select(Character).where(Character.id == request.character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 构建图片描述
    prompt_parts = [character.name]

    if character.gender:
        prompt_parts.append(character.gender)
    if character.age:
        prompt_parts.append(f"{character.age} years old")
    if character.appearance:
        prompt_parts.append(character.appearance[:200])

    image_prompt = ", ".join(prompt_parts)

    try:
        image_url = await ai_service.generate_image(
            prompt=image_prompt,
            style=request.style,
        )

        # 更新角色头像
        character.avatar_url = image_url
        await db.commit()

        return {
            "character_id": character.id,
            "image_url": image_url,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成图片失败: {str(e)}")
