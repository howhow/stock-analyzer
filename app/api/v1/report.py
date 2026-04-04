"""
报告 API
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/report", tags=["报告"])


@router.get("/{analysis_id}", response_class=HTMLResponse)
async def get_report(analysis_id: str):
    """
    获取 HTML 报告

    Args:
        analysis_id: 分析ID

    Returns:
        HTML 报告
    """
    logger.info("report_requested", analysis_id=analysis_id)

    # TODO: 从存储获取报告
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>股票分析报告 - {analysis_id}</title>
    </head>
    <body>
        <h1>股票分析报告</h1>
        <p>分析ID: {analysis_id}</p>
        <p>报告功能开发中...</p>
    </body>
    </html>
    """
    return html_content
