"""
报告存储测试
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.models.report import ReportFormat, ReportStatus, ReportStorageConfig
from app.report.storage import ReportStorage, get_report_storage


class TestReportStorage:
    """报告存储测试"""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """创建临时目录"""
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_dir: Path) -> ReportStorage:
        """创建报告存储"""
        config = ReportStorageConfig(
            base_path=temp_dir,
            max_reports_per_stock=5,
            retention_days=7,
        )
        return ReportStorage(config)

    @pytest.fixture
    def sample_html_content(self) -> str:
        """示例 HTML 内容"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Test Report</title></head>
        <body><h1>Test Report</h1></body>
        </html>
        """

    def test_storage_init(self, storage: ReportStorage) -> None:
        """测试存储初始化"""
        assert storage is not None
        assert storage.config.base_path.exists()

    def test_save_report(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试保存报告"""
        metadata = storage.save(
            report_id="test_report_001",
            content=sample_html_content,
            stock_code="600519.SH",
            analysis_id="analysis_001",
            format_type=ReportFormat.HTML,
            stock_name="贵州茅台",
        )

        assert metadata is not None
        assert metadata.report_id == "test_report_001"
        assert metadata.stock_code == "600519.SH"
        assert metadata.stock_name == "贵州茅台"
        assert metadata.status == ReportStatus.COMPLETED
        assert metadata.file_path is not None
        assert metadata.file_path.exists()

    def test_load_report(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试加载报告"""
        # 保存报告
        storage.save(
            report_id="test_report_002",
            content=sample_html_content,
            stock_code="600519.SH",
            analysis_id="analysis_002",
        )

        # 加载报告
        loaded = storage.load("test_report_002")
        assert loaded is not None
        assert "Test Report" in loaded

    def test_load_nonexistent_report(self, storage: ReportStorage) -> None:
        """测试加载不存在的报告"""
        loaded = storage.load("nonexistent_id")
        assert loaded is None

    def test_get_metadata(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试获取元数据"""
        storage.save(
            report_id="test_report_003",
            content=sample_html_content,
            stock_code="600519.SH",
            analysis_id="analysis_003",
            stock_name="贵州茅台",
        )

        metadata = storage.get_metadata("test_report_003")
        assert metadata is not None
        assert metadata.report_id == "test_report_003"
        assert metadata.stock_name == "贵州茅台"

    def test_delete_report(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试删除报告"""
        storage.save(
            report_id="test_report_004",
            content=sample_html_content,
            stock_code="600519.SH",
            analysis_id="analysis_004",
        )

        # 删除
        result = storage.delete("test_report_004")
        assert result is True

        # 确认删除
        loaded = storage.load("test_report_004")
        assert loaded is None

    def test_list_reports(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试列出报告"""
        # 保存多个报告
        for i in range(3):
            storage.save(
                report_id=f"test_report_{i:03d}",
                content=sample_html_content,
                stock_code="600519.SH",
                analysis_id=f"analysis_{i:03d}",
            )

        reports = storage.list_reports(stock_code="600519.SH")
        assert len(reports) == 3

    def test_list_reports_with_pagination(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试分页列出报告"""
        # 保存多个报告
        for i in range(5):
            storage.save(
                report_id=f"test_report_page_{i:03d}",
                content=sample_html_content,
                stock_code="600519.SH",
                analysis_id=f"analysis_page_{i:03d}",
            )

        # 分页
        page1 = storage.list_reports(limit=2, offset=0)
        assert len(page1) == 2

        page2 = storage.list_reports(limit=2, offset=2)
        assert len(page2) == 2

    def test_get_storage_stats(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试获取存储统计"""
        # 保存报告
        storage.save(
            report_id="test_report_stats",
            content=sample_html_content,
            stock_code="600519.SH",
            analysis_id="analysis_stats",
        )

        stats = storage.get_storage_stats()
        assert stats["total_reports"] >= 1
        assert stats["total_size_bytes"] > 0
        assert "by_format" in stats

    def test_cleanup_old_reports(
        self, storage: ReportStorage, sample_html_content: str
    ) -> None:
        """测试清理旧报告"""
        # 保存超过限制的报告
        for i in range(7):
            storage.save(
                report_id=f"test_report_cleanup_{i:03d}",
                content=sample_html_content,
                stock_code="600519.SH",
                analysis_id=f"analysis_cleanup_{i:03d}",
            )

        # 清理（保留5个）
        cleaned = storage.cleanup_old_reports("600519.SH")
        assert cleaned == 2  # 删除了2个

        # 确认剩余数量
        remaining = storage.list_reports(stock_code="600519.SH")
        assert len(remaining) == 5

    def test_get_report_storage(self) -> None:
        """测试获取全局存储实例"""
        s1 = get_report_storage()
        s2 = get_report_storage()
        assert s1 is s2
