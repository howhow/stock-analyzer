"""
本地数据加载器

支持从 CSV 和 Parquet 文件加载历史行情数据。
"""

from pathlib import Path
from typing import Literal

import pandas as pd

from app.core.exceptions import DataNotFoundError, DataSourceError


class LocalDataLoader:
    """
    本地数据加载器

    支持 CSV 和 Parquet 格式的数据文件。
    文件命名约定: {stock_code}.csv 或 {stock_code}.parquet
    """

    def __init__(
        self,
        data_dir: str | Path = "./data/local",
        file_format: Literal["csv", "parquet"] = "csv",
    ):
        """
        初始化加载器

        Args:
            data_dir: 数据目录路径
            file_format: 文件格式 (csv 或 parquet)
        """
        self.data_dir = Path(data_dir)
        self.file_format = file_format

    def load(
        self,
        stock_code: str,
    ) -> pd.DataFrame | None:
        """
        加载股票数据

        Args:
            stock_code: 股票代码 (如 '600519.SH')

        Returns:
            DataFrame 或 None (文件不存在)
        """
        # 规范化股票代码：将 . 转换为 _
        safe_code = stock_code.replace(".", "_")
        file_path = self.data_dir / f"{safe_code}.{self.file_format}"

        if not file_path.exists():
            return None

        try:
            if self.file_format == "csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_parquet(file_path)

            return self._validate_and_normalize(df, stock_code)

        except Exception as e:
            raise DataSourceError(
                f"Failed to load data from {file_path}",
                details={"stock_code": stock_code, "error": str(e)},
            )

    def load_with_date_filter(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame | None:
        """
        加载并过滤日期范围

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            过滤后的 DataFrame 或 None
        """
        df = self.load(stock_code)
        if df is None:
            return None

        # 确保 date 列是 datetime 类型
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df[
                (df["date"] >= start_date) & (df["date"] <= end_date)
            ]

        return df

    def _validate_and_normalize(
        self,
        df: pd.DataFrame,
        stock_code: str,
    ) -> pd.DataFrame:
        """
        验证并标准化数据格式

        Args:
            df: 原始 DataFrame
            stock_code: 股票代码

        Returns:
            标准化后的 DataFrame
        """
        # 检查必需列
        required_columns = {"date", "close"}
        if not required_columns.issubset(set(df.columns)):
            missing = required_columns - set(df.columns)
            raise DataSourceError(
                f"Missing required columns: {missing}",
                details={"stock_code": stock_code, "columns": list(df.columns)},
            )

        # 标准化列名 (支持多种常见格式)
        column_mapping = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Adj Close": "adj_close",
        }
        df = df.rename(columns=column_mapping)

        # 转换日期格式
        df["date"] = pd.to_datetime(df["date"])

        # 按日期排序
        df = df.sort_values("date").reset_index(drop=True)

        return df

    def list_available_stocks(self) -> list[str]:
        """
        列出数据目录中所有可用的股票代码

        Returns:
            股票代码列表
        """
        if not self.data_dir.exists():
            return []

        stocks = []
        for file_path in self.data_dir.glob(f"*.{self.file_format}"):
            # 从文件名提取股票代码，将 _ 还原为 .
            code = file_path.stem.replace("_", ".")
            stocks.append(code)

        return sorted(stocks)

    def has_data(self, stock_code: str) -> bool:
        """
        检查指定股票是否有本地数据

        Args:
            stock_code: 股票代码

        Returns:
            是否存在数据文件
        """
        safe_code = stock_code.replace(".", "_")
        file_path = self.data_dir / f"{safe_code}.{self.file_format}"
        return file_path.exists()
