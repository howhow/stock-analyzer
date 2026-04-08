"""
行业分析完整测试

目标覆盖率: ≥ 90%
当前覆盖率: 79%
"""

import pytest

from app.analysis.fundamental.industry import (
    INDUSTRY_WEIGHTS,
    analyze_industry_position,
    calculate_industry_score,
    get_industry_category,
)


class TestGetIndustryCategory:
    """获取行业大类测试"""

    def test_get_industry_category_tech(self):
        """测试科技行业分类"""
        assert get_industry_category("软件开发") == "科技"
        assert get_industry_category("电子元器件") == "科技"
        assert get_industry_category("通信设备") == "科技"
        assert get_industry_category("计算机") == "科技"
        assert get_industry_category("半导体") == "科技"
        assert get_industry_category("芯片设计") == "科技"

    def test_get_industry_category_consumer(self):
        """测试消费行业分类"""
        assert get_industry_category("食品饮料") == "消费"
        assert get_industry_category("白酒") == "消费"
        assert get_industry_category("家用电器") == "消费"
        assert get_industry_category("零售百货") == "消费"
        assert get_industry_category("服装纺织") == "消费"

    def test_get_industry_category_finance(self):
        """测试金融行业分类"""
        assert get_industry_category("银行") == "金融"
        assert get_industry_category("保险") == "金融"
        assert get_industry_category("证券") == "金融"
        assert get_industry_category("信托") == "金融"

    def test_get_industry_category_healthcare(self):
        """测试医药行业分类"""
        assert get_industry_category("医药制造") == "医药"
        assert get_industry_category("生物制药") == "医药"
        assert get_industry_category("医疗器械") == "医药"
        assert get_industry_category("制药") == "医药"

    def test_get_industry_category_manufacturing(self):
        """测试制造行业分类"""
        assert get_industry_category("机械制造") == "制造"
        assert get_industry_category("汽车零部件") == "制造"
        assert get_industry_category("化工") == "制造"
        assert get_industry_category("建材") == "制造"
        assert get_industry_category("钢铁") == "制造"

    def test_get_industry_category_energy(self):
        """测试能源行业分类"""
        assert get_industry_category("石油开采") == "能源"
        assert get_industry_category("煤炭开采") == "能源"
        assert get_industry_category("电力") == "能源"
        assert get_industry_category("新能源") == "能源"
        assert get_industry_category("光伏") == "能源"

    def test_get_industry_category_unknown(self):
        """测试未知行业分类"""
        assert get_industry_category("未知行业") == "default"
        assert get_industry_category("新行业") == "default"

    def test_get_industry_category_none(self):
        """测试空值"""
        assert get_industry_category(None) == "default"
        assert get_industry_category("") == "default"


class TestAnalyzeIndustryPosition:
    """分析行业地位测试"""

    def test_analyze_industry_position_leader(self):
        """测试龙头企业"""
        result = analyze_industry_position("科技", industry_rank=5)

        assert result["score"] >= 90
        assert result["details"]["position"] == "龙头"
        assert result["details"]["category"] == "科技"
        assert result["details"]["prospect_score"] == 85

    def test_analyze_industry_position_leading(self):
        """测试领先企业"""
        result = analyze_industry_position("消费", industry_rank=20)

        assert result["score"] >= 75
        assert result["details"]["position"] == "领先"
        assert result["details"]["category"] == "消费"

    def test_analyze_industry_position_middle(self):
        """测试中游企业"""
        result = analyze_industry_position("金融", industry_rank=40)

        assert result["score"] >= 65
        assert result["details"]["position"] == "中游"
        assert result["details"]["category"] == "金融"

    def test_analyze_industry_position_lagging(self):
        """测试落后企业"""
        result = analyze_industry_position("制造", industry_rank=80)

        assert result["score"] >= 55
        assert result["details"]["position"] == "落后"
        assert result["details"]["category"] == "制造"

    def test_analyze_industry_position_no_rank(self):
        """测试无排名情况"""
        result = analyze_industry_position("医药", industry_rank=None)

        assert result["score"] == 50
        assert result["details"]["position"] == "未知"
        assert result["details"]["category"] == "医药"

    def test_analyze_industry_position_none_industry(self):
        """测试空行业名"""
        result = analyze_industry_position(None, industry_rank=10)

        assert result["details"]["category"] == "default"
        assert result["details"]["position"] == "龙头"


class TestCalculateIndustryScore:
    """计算行业评分测试"""

    def test_calculate_industry_score_complete(self):
        """测试完整评分计算"""
        result = calculate_industry_score("科技", industry_rank=10)

        assert "total_score" in result
        assert "position" in result
        assert "category" in result
        assert "weights" in result
        assert "details" in result

        assert result["category"] == "科技"
        assert result["position"] == "龙头"
        assert result["weights"]["growth"] == 0.4
        assert result["weights"]["profitability"] == 0.3
        assert result["weights"]["valuation"] == 0.3

    def test_calculate_industry_score_different_categories(self):
        """测试不同行业分类的评分"""
        # 科技行业
        tech_result = calculate_industry_score("软件开发", industry_rank=15)
        assert tech_result["category"] == "科技"

        # 金融行业
        finance_result = calculate_industry_score("银行", industry_rank=25)
        assert finance_result["category"] == "金融"
        assert finance_result["weights"]["growth"] == 0.2
        assert finance_result["weights"]["profitability"] == 0.4

    def test_calculate_industry_score_default_category(self):
        """测试默认行业分类"""
        result = calculate_industry_score("新行业", industry_rank=50)

        assert result["category"] == "default"
        assert result["weights"]["growth"] == 0.3
        assert result["weights"]["profitability"] == 0.4

    def test_calculate_industry_score_none_industry(self):
        """测试空行业"""
        result = calculate_industry_score(None, industry_rank=30)

        assert result["category"] == "default"


class TestIndustryWeights:
    """行业权重配置测试"""

    def test_industry_weights_config(self):
        """测试行业权重配置"""
        # 科技行业权重
        assert INDUSTRY_WEIGHTS["科技"]["growth"] == 0.4
        assert INDUSTRY_WEIGHTS["科技"]["profitability"] == 0.3
        assert INDUSTRY_WEIGHTS["科技"]["valuation"] == 0.3

        # 金融行业权重
        assert INDUSTRY_WEIGHTS["金融"]["growth"] == 0.2
        assert INDUSTRY_WEIGHTS["金融"]["profitability"] == 0.4
        assert INDUSTRY_WEIGHTS["金融"]["valuation"] == 0.4

        # 默认权重
        assert INDUSTRY_WEIGHTS["default"]["growth"] == 0.3
        assert INDUSTRY_WEIGHTS["default"]["profitability"] == 0.4
        assert INDUSTRY_WEIGHTS["default"]["valuation"] == 0.3


# 运行测试
if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=app.analysis.fundamental.industry",
            "--cov-report=term-missing",
        ]
    )
