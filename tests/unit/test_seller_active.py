"""
卖家活跃时间服务与筛选逻辑测试
"""
from datetime import datetime, timedelta

from src.scraper import _passes_seller_active_filter
from src.services.seller_active_service import (
    format_active_time,
    get_active_level,
    is_seller_recently_active,
)


def _iso(hours_ago):
    return (datetime.now() - timedelta(hours=hours_ago)).isoformat()


class TestFormatActiveTime:
    def test_null_returns_unknown(self):
        assert format_active_time(None) == "未知"
        assert format_active_time("") == "未知"

    def test_recently_online(self):
        assert format_active_time(_iso(0.01)) == "刚刚在线"

    def test_minutes_ago(self):
        assert "分钟前" in format_active_time(_iso(0.5))

    def test_hours_ago(self):
        assert "小时前" in format_active_time(_iso(2))

    def test_days_ago(self):
        assert "天前" in format_active_time(_iso(48))

    def test_invalid_input_returns_raw_value(self):
        assert format_active_time("not-a-date") == "not-a-date"


class TestIsSellerRecentlyActive:
    def test_null_returns_false(self):
        assert is_seller_recently_active(None) is False

    def test_within_window(self):
        assert is_seller_recently_active(_iso(2), within_hours=24) is True

    def test_outside_window(self):
        assert is_seller_recently_active(_iso(48), within_hours=24) is False

    def test_invalid_input_returns_false(self):
        assert is_seller_recently_active("bad", within_hours=24) is False


class TestGetActiveLevel:
    def test_very_active(self):
        assert get_active_level(_iso(0.5)) == "非常活跃"

    def test_active(self):
        assert get_active_level(_iso(6)) == "活跃"

    def test_normal(self):
        assert get_active_level(_iso(48)) == "一般"

    def test_inactive(self):
        assert get_active_level(_iso(96)) == "不活跃"

    def test_unknown(self):
        assert get_active_level(None) == "未知"


class TestPassesSellerActiveFilter:
    def test_no_option_allows(self):
        assert _passes_seller_active_filter({}, None) is True
        assert _passes_seller_active_filter({"seller_active_option": "__none__"}, None) is True

    def test_no_active_data_allows(self):
        assert _passes_seller_active_filter({"seller_active_option": "24 小时内"}, None) is True

    def test_within_window_passes(self):
        assert (
            _passes_seller_active_filter(
                {"seller_active_option": "24 小时内"}, _iso(2)
            )
            is True
        )

    def test_outside_window_rejected(self):
        assert (
            _passes_seller_active_filter(
                {"seller_active_option": "24 小时内"}, _iso(48)
            )
            is False
        )

    def test_three_days_option(self):
        assert _passes_seller_active_filter({"seller_active_option": "3 天内"}, _iso(48)) is True
        assert _passes_seller_active_filter({"seller_active_option": "3 天内"}, _iso(96)) is False

    def test_unknown_option_allows(self):
        assert _passes_seller_active_filter({"seller_active_option": "1 周内"}, _iso(2)) is True
