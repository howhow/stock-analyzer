"""
报告存储

管理报告文件的存储、检索和清理
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.models.report import (
    ReportFormat,
    ReportMetadata,
    ReportStatus,
    ReportStorageConfig,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReportStorage:
    """
    报告存储管理器

    负责报告文件的存储、检索、清理
    """

    def __init__(self, config: ReportStorageConfig | None = None):
        """
        初始化报告存储

        Args:
            config: 存储配置
        """
        self.config = config or ReportStorageConfig()
        self._ensure_directories()

        logger.info(
            "report_storage_initialized",
            base_path=str(self.config.base_path),
            retention_days=self.config.retention_days,
        )

    def _ensure_directories(self) -> None:
        """确保存储目录存在"""
        self.config.base_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (self.config.base_path / "html").mkdir(exist_ok=True)
        (self.config.base_path / "json").mkdir(exist_ok=True)
        (self.config.base_path / "metadata").mkdir(exist_ok=True)

    def save(
        self,
        report_id: str,
        content: str,
        stock_code: str,
        analysis_id: str,
        format_type: ReportFormat = ReportFormat.HTML,
        stock_name: str | None = None,
    ) -> ReportMetadata:
        """
        保存报告

        Args:
            report_id: 报告ID
            content: 报告内容
            stock_code: 股票代码
            analysis_id: 关联的分析ID
            format_type: 报告格式
            stock_name: 股票名称

        Returns:
            报告元数据
        """
        # 确定文件路径
        file_path = self._get_file_path(report_id, stock_code, format_type)

        # 保存文件
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        # 获取文件大小
        file_size = file_path.stat().st_size

        # 创建元数据
        metadata = ReportMetadata(
            report_id=report_id,
            analysis_id=analysis_id,
            stock_code=stock_code,
            stock_name=stock_name,
            file_path=file_path,
            file_size_bytes=file_size,
            format=format_type,
            status=ReportStatus.COMPLETED,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=self.config.retention_days),
        )

        # 保存元数据
        self._save_metadata(metadata)

        logger.info(
            "report_saved",
            report_id=report_id,
            stock_code=stock_code,
            file_path=str(file_path),
            file_size=file_size,
        )

        return metadata

    def load(self, report_id: str) -> str | None:
        """
        加载报告内容

        Args:
            report_id: 报告ID

        Returns:
            报告内容或None
        """
        metadata = self.get_metadata(report_id)
        if not metadata or not metadata.file_path:
            return None

        if not metadata.file_path.exists():
            logger.warning("report_file_not_found", report_id=report_id)
            return None

        # 更新访问信息
        self._update_access_info(metadata)

        return metadata.file_path.read_text(encoding="utf-8")

    def get_metadata(self, report_id: str) -> ReportMetadata | None:
        """
        获取报告元数据

        Args:
            report_id: 报告ID

        Returns:
            报告元数据或None
        """
        metadata_path = self.config.base_path / "metadata" / f"{report_id}.json"

        if not metadata_path.exists():
            return None

        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            data["file_path"] = (
                Path(data["file_path"]) if data.get("file_path") else None
            )
            return ReportMetadata(**data)
        except Exception as e:
            logger.error("metadata_load_failed", report_id=report_id, error=str(e))
            return None

    def delete(self, report_id: str) -> bool:
        """
        删除报告

        Args:
            report_id: 报告ID

        Returns:
            是否成功
        """
        metadata = self.get_metadata(report_id)
        if not metadata:
            return False

        # 删除文件
        if metadata.file_path and metadata.file_path.exists():
            metadata.file_path.unlink()

        # 删除元数据
        metadata_path = self.config.base_path / "metadata" / f"{report_id}.json"
        if metadata_path.exists():
            metadata_path.unlink()

        logger.info("report_deleted", report_id=report_id)

        return True

    def list_reports(
        self,
        stock_code: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ReportMetadata]:
        """
        列出报告

        Args:
            stock_code: 股票代码过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            报告元数据列表
        """
        metadata_dir = self.config.base_path / "metadata"
        if not metadata_dir.exists():
            return []

        reports = []
        for meta_file in sorted(
            metadata_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True
        ):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                data["file_path"] = (
                    Path(data["file_path"]) if data.get("file_path") else None
                )
                metadata = ReportMetadata(**data)

                # 过滤股票代码
                if stock_code and metadata.stock_code != stock_code:
                    continue

                reports.append(metadata)

                if len(reports) >= limit + offset:
                    break
            except Exception as e:
                logger.warning(
                    "metadata_parse_failed", file=str(meta_file), error=str(e)
                )
                continue

        return reports[offset:offset + limit]

    def cleanup_expired(self) -> int:
        """
        清理过期报告

        Returns:
            清理数量
        """
        metadata_dir = self.config.base_path / "metadata"
        if not metadata_dir.exists():
            return 0

        cleaned = 0
        now = datetime.now()

        for meta_file in metadata_dir.glob("*.json"):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                expires_at = datetime.fromisoformat(data.get("expires_at", ""))

                if expires_at < now:
                    self.delete(data["report_id"])
                    cleaned += 1
            except Exception as e:
                logger.warning(
                    "cleanup_parse_failed", file=str(meta_file), error=str(e)
                )
                continue

        logger.info("expired_reports_cleaned", count=cleaned)

        return cleaned

    def cleanup_old_reports(self, stock_code: str) -> int:
        """
        清理单只股票的旧报告（保留最新的N个）

        Args:
            stock_code: 股票代码

        Returns:
            清理数量
        """
        reports = self.list_reports(stock_code=stock_code, limit=1000)
        max_keep = self.config.max_reports_per_stock

        if len(reports) <= max_keep:
            return 0

        # 按创建时间排序
        reports.sort(key=lambda x: x.created_at, reverse=True)

        # 删除超出的报告
        cleaned = 0
        for report in reports[max_keep:]:
            if self.delete(report.report_id):
                cleaned += 1

        logger.info(
            "old_reports_cleaned",
            stock_code=stock_code,
            cleaned=cleaned,
            kept=max_keep,
        )

        return cleaned

    def get_storage_stats(self) -> dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            统计信息
        """
        metadata_dir = self.config.base_path / "metadata"

        total_size = 0
        total_count = 0
        by_format: dict[str, int] = {}

        if metadata_dir.exists():
            for meta_file in metadata_dir.glob("*.json"):
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    total_count += 1
                    total_size += data.get("file_size_bytes", 0)
                    fmt = data.get("format", "unknown")
                    by_format[fmt] = by_format.get(fmt, 0) + 1
                except Exception:
                    continue

        return {
            "total_reports": total_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_format": by_format,
            "max_size_mb": self.config.max_total_size_mb,
            "usage_percent": round(
                total_size / (self.config.max_total_size_mb * 1024 * 1024) * 100, 2
            ),
        }

    def _get_file_path(
        self, report_id: str, stock_code: str, format_type: ReportFormat
    ) -> Path:
        """获取报告文件路径"""
        # 按股票代码分子目录
        safe_code = stock_code.replace(".", "_").replace("/", "_")
        ext = "html" if format_type == ReportFormat.HTML else "json"
        return self.config.base_path / ext / safe_code / f"{report_id}.{ext}"

    def _save_metadata(self, metadata: ReportMetadata) -> None:
        """保存元数据"""
        metadata_path = (
            self.config.base_path / "metadata" / f"{metadata.report_id}.json"
        )

        data = metadata.model_dump()
        data["file_path"] = str(data["file_path"]) if data.get("file_path") else None
        data["created_at"] = data["created_at"].isoformat()
        data["expires_at"] = (
            data["expires_at"].isoformat() if data.get("expires_at") else None
        )
        data["last_accessed_at"] = (
            data["last_accessed_at"].isoformat()
            if data.get("last_accessed_at")
            else None
        )
        data["status"] = data["status"].value
        data["format"] = data["format"].value

        metadata_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _update_access_info(self, metadata: ReportMetadata) -> None:
        """更新访问信息"""
        metadata.access_count += 1
        metadata.last_accessed_at = datetime.now()
        self._save_metadata(metadata)


# 全局报告存储实例
_report_storage: ReportStorage | None = None


def get_report_storage() -> ReportStorage:
    """获取全局报告存储实例"""
    global _report_storage
    if _report_storage is None:
        _report_storage = ReportStorage()
    return _report_storage
