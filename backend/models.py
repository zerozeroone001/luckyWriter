from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Novel(Base):
    """小说表"""
    __tablename__ = "novels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="小说标题")
    author = Column(String(100), default="默认作者", comment="作者名")
    genre = Column(String(50), comment="小说类型（玄幻、都市等）")
    target_words = Column(Integer, default=1000000, comment="目标字数")
    current_words = Column(Integer, default=0, comment="当前字数")
    cover_image = Column(String(500), comment="封面图片路径")
    synopsis = Column(Text, comment="简介")
    style_prompt = Column(Text, comment="系统风格提示词")
    status = Column(String(20), default="writing", comment="状态：writing/completed/paused")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class Chapter(Base):
    """章节表"""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, comment="所属小说")
    volume_number = Column(Integer, default=1, comment="卷号")
    chapter_number = Column(Integer, nullable=False, comment="章节号")
    title = Column(String(200), nullable=False, comment="章节标题")
    content = Column(Text, comment="章节正文")
    word_count = Column(Integer, default=0, comment="字数")
    status = Column(String(20), default="draft", comment="状态：draft/published")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class Character(Base):
    """角色卡表"""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, comment="所属小说")
    name = Column(String(100), nullable=False, comment="角色姓名")
    gender = Column(String(20), comment="性别")
    age = Column(String(50), comment="年龄")
    appearance = Column(Text, comment="外貌身材描述")
    identity_info = Column(Text, comment="身份信息介绍")
    personality = Column(Text, comment="性格特点")
    background = Column(Text, comment="背景故事")
    relationships = Column(Text, comment="人物关系")
    abilities = Column(Text, comment="能力特长")
    character_arc = Column(Text, comment="角色成长线")
    quotes = Column(Text, comment="经典语录")
    avatar_url = Column(String(500), comment="角色形象图片URL")
    importance = Column(String(20), default="minor", comment="重要性：main/major/minor")
    is_detailed = Column(Boolean, default=False, comment="是否已详细扩展")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class Outline(Base):
    """大纲表"""
    __tablename__ = "outlines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, comment="所属小说")
    volume_number = Column(Integer, comment="卷号")
    chapter_number = Column(Integer, comment="章节号")
    title = Column(String(200), nullable=False, comment="标题")
    plot_summary = Column(Text, comment="情节梗概")
    key_events = Column(Text, comment="关键事件（JSON数组）")
    characters_involved = Column(Text, comment="涉及角色（JSON数组）")
    outline_type = Column(String(20), default="chapter", comment="类型：volume/chapter/scene")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class AIChannel(Base):
    """AI渠道表"""
    __tablename__ = "ai_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="渠道名称")
    provider = Column(String(50), nullable=False, comment="提供商：newapi")
    api_key = Column(String(500), comment="API密钥")
    base_url = Column(String(500), comment="API地址")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class AIModel(Base):
    """AI模型表"""
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("ai_channels.id", ondelete="CASCADE"), nullable=False, comment="所属渠道")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    model_id = Column(String(100), nullable=False, comment="模型ID")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    temperature = Column(Float, default=0.8, comment="温度参数")
    cost_per_1k_input_tokens = Column(Float, default=0.0, comment="输入token成本（美元/1K）")
    cost_per_1k_output_tokens = Column(Float, default=0.0, comment="输出token成本（美元/1K）")
    response_time_ms = Column(Integer, comment="响应时间（毫秒）")
    last_test_at = Column(DateTime, comment="最后测速时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class GenrePreset(Base):
    """小说类型预设表"""
    __tablename__ = "genre_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    genre_name = Column(String(50), nullable=False, unique=True, comment="类型名称")
    description = Column(Text, comment="类型描述")
    prompt_template = Column(Text, nullable=False, comment="提示词模板")
    style_constraints = Column(Text, comment="风格约束（JSON）")
    typical_elements = Column(Text, comment="典型元素（JSON数组）")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class SystemPreset(Base):
    """系统提示词预设表"""
    __tablename__ = "system_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    preset_name = Column(String(100), nullable=False, unique=True, comment="预设名称")
    description = Column(Text, comment="预设描述")
    system_prompt = Column(Text, nullable=False, comment="系统提示词内容")
    use_case = Column(String(100), comment="使用场景：outline/character/content/summary")
    is_default = Column(Boolean, default=False, comment="是否默认")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class AIGenerationLog(Base):
    """AI生成日志表"""
    __tablename__ = "ai_generation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), comment="所属小说")
    model_id = Column(Integer, ForeignKey("ai_models.id", ondelete="SET NULL"), comment="使用的AI模型")
    generation_type = Column(String(50), nullable=False, comment="生成类型：outline/character/content/summary")
    prompt_fingerprint = Column(String(64), comment="提示词指纹（MD5）")
    api_endpoint = Column(String(200), comment="API接口路径")
    channel_name = Column(String(100), comment="渠道名称快照")
    channel_provider = Column(String(50), comment="渠道提供商快照")
    model_name = Column(String(100), comment="模型名称快照")
    model_identifier = Column(String(100), comment="模型ID快照")
    request_params = Column(Text, comment="请求参数（脱敏后，JSON格式）")
    input_tokens = Column(Integer, default=0, comment="输入token数")
    output_tokens = Column(Integer, default=0, comment="输出token数")
    cost = Column(Float, default=0.0, comment="成本（美元）")
    duration_seconds = Column(Float, comment="耗时（秒）")
    status = Column(String(20), default="success", comment="状态：success/failed/stopped")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
