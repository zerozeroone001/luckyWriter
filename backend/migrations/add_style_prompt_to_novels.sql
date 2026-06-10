-- 为 novels 表添加 style_prompt 字段
ALTER TABLE novels ADD COLUMN style_prompt TEXT COMMENT '系统风格提示词';
