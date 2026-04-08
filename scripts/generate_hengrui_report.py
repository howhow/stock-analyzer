#!/usr/bin/env python3
"""
生成恒瑞医药分析报告

使用真实数据生成HTML和MD格式报告
"""

import asyncio
import json
from datetime import date, timedelta
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.analysis.system import SystemAnalyzer
from app.data.data_fetcher import DataFetcher
from app.report.generator import ReportGenerator
from app.report.markdown_report import MarkdownReportGenerator
from app.models.report import ReportFormat
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_reports():
    """生成恒瑞医药分析报告"""
    
    stock_code = "600276.SH"
    stock_name = "恒瑞医药"
    
    print(f"\n{'='*60}")
    print(f"开始分析: {stock_name} ({stock_code})")
    print(f"{'='*60}\n")
    
    # 1. 初始化数据获取器
    print("📊 初始化数据获取器...")
    fetcher = DataFetcher()
    
    # 2. 获取数据
    print("📈 获取股票数据...")
    end_date = date.today()
    start_date = end_date - timedelta(days=365)  # 一年数据
    
    try:
        # 获取股票信息
        stock_info = await fetcher.get_stock_info(stock_code)
        if stock_info:
            print(f"✅ 股票信息: {stock_info.name} ({stock_info.code})")
            print(f"   行业: {stock_info.industry}")
            stock_name = stock_info.name
        else:
            print("⚠️  未获取到股票信息，使用默认值")
            
        # 获取日线数据
        print(f"   获取日线数据: {start_date} ~ {end_date}")
        quotes = await fetcher.get_daily_quotes(stock_code, start_date, end_date)
        print(f"✅ 日线数据: {len(quotes)} 条")
        
        # 获取财务数据
        print("   获取财务数据...")
        financial = await fetcher.get_financial_data(stock_code)
        if financial:
            print(f"✅ 财务数据已获取")
        else:
            print("⚠️  未获取到财务数据")
            
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        logger.error("data_fetch_failed", error=str(e), stock_code=stock_code)
        return
    
    # 3. 执行分析
    print("\n🔍 执行综合分析...")
    analyzer = SystemAnalyzer()
    
    try:
        result = await analyzer.analyze(
            stock_info=stock_info,
            quotes=quotes,
            financial=financial,
            analysis_type="both",  # 技术面+基本面
        )
        
        print(f"✅ 分析完成!")
        print(f"   总分: {result.scores.get('total', 50):.1f}")
        print(f"   推荐: {result.details.get('recommendation', '持有')}")
        print(f"   置信度: {result.details.get('confidence', 60):.0f}%")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        logger.error("analysis_failed", error=str(e), stock_code=stock_code)
        import traceback
        traceback.print_exc()
        return
    
    # 4. 生成HTML报告
    print("\n📄 生成HTML报告...")
    html_generator = ReportGenerator()
    
    try:
        html_report = html_generator.generate(
            analysis_result=result,
            stock_code=stock_code,
            stock_name=stock_name,
            format_type=ReportFormat.HTML,
            chart_data={
                "quotes": quotes,
                "indicators": result.details.get("indicators", {}),
            },
            indicators=result.details.get("indicators", {}),
            fundamentals=result.details.get("fundamentals", {}),
        )
        
        html_path = Path(f"reports/{stock_code}_report.html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_report.content, encoding="utf-8")
        print(f"✅ HTML报告已保存: {html_path}")
        
    except Exception as e:
        print(f"❌ HTML报告生成失败: {e}")
        logger.error("html_report_failed", error=str(e))
        import traceback
        traceback.print_exc()
    
    # 5. 生成Markdown报告
    print("\n📝 生成Markdown报告...")
    md_generator = MarkdownReportGenerator()
    
    try:
        md_report = md_generator.generate(
            result=result,
            stock_code=stock_code,
            stock_name=stock_name,
            quotes=quotes,
            indicators=result.details.get("indicators", {}),
        )
        
        md_path = Path(f"reports/{stock_code}_report.md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_report, encoding="utf-8")
        print(f"✅ Markdown报告已保存: {md_path}")
        
    except Exception as e:
        print(f"❌ Markdown报告生成失败: {e}")
        logger.error("md_report_failed", error=str(e))
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ 报告生成完成!")
    print(f"{'='*60}\n")
    
    # 返回报告路径
    return {
        "html": html_path if 'html_path' in locals() else None,
        "md": md_path if 'md_path' in locals() else None,
        "result": {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "total_score": result.scores.get("total", 50),
            "recommendation": result.details.get("recommendation", "持有"),
            "confidence": result.details.get("confidence", 60),
        }
    }


if __name__ == "__main__":
    result = asyncio.run(generate_reports())
    if result:
        print(json.dumps(result.get("result", {}), ensure_ascii=False, indent=2))
