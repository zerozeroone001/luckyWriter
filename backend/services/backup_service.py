import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
from config import settings


class BackupService:
    """本地备份服务"""

    def __init__(self):
        self.backup_dir = settings.BASE_DIR / "data" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> str:
        """
        创建数据库备份

        Returns:
            str: 备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"writer_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        # 复制数据库文件
        db_path = settings.BASE_DIR / settings.DATABASE_PATH
        if db_path.exists():
            shutil.copy2(db_path, backup_path)
            return str(backup_path)
        else:
            raise FileNotFoundError("数据库文件不存在")

    def list_backups(self) -> List[dict]:
        """
        列出所有备份文件

        Returns:
            List[dict]: 备份文件列表
        """
        backups = []
        for backup_file in self.backup_dir.glob("writer_backup_*.db"):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        # 按创建时间倒序排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def restore_backup(self, backup_filename: str) -> bool:
        """
        恢复备份

        Args:
            backup_filename: 备份文件名

        Returns:
            bool: 是否成功
        """
        backup_path = self.backup_dir / backup_filename
        if not backup_path.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_filename}")

        db_path = settings.BASE_DIR / settings.DATABASE_PATH

        # 先备份当前数据库
        if db_path.exists():
            self.create_backup()

        # 恢复备份
        shutil.copy2(backup_path, db_path)
        return True

    def delete_backup(self, backup_filename: str) -> bool:
        """删除指定备份"""
        backup_path = self.backup_dir / backup_filename
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False

    def cleanup_old_backups(self) -> int:
        """
        清理过期备份

        Returns:
            int: 删除的备份数量
        """
        cutoff_date = datetime.now() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
        deleted_count = 0

        for backup_file in self.backup_dir.glob("writer_backup_*.db"):
            created_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if created_time < cutoff_date:
                backup_file.unlink()
                deleted_count += 1

        return deleted_count


# 全局备份服务实例
backup_service = BackupService()
