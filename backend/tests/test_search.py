"""图片搜索 API 和 Service 层的单元测试。

本模块使用 pytest 和 unittest.mock 对搜索功能进行隔离测试：
- Service 层：通过 MagicMock 模拟 SQLAlchemy Session 和 Query 链式调用
- API 层：通过 TestClient 和 patch 模拟 service 函数

由于 SQLite 不支持 PostgreSQL 的 JSONB 和 @> 操作符，
所有数据库查询均通过 mock 隔离，不依赖真实数据库。
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.search import ImageOut, SearchParams, SearchResponse
from backend.services.search_service import search_images


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """创建一个模拟的 SQLAlchemy Session，支持查询链式调用。"""
    db = MagicMock()
    mock_query = MagicMock()
    # 链式调用：每个方法返回 mock_query 自身
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.with_entities.return_value = mock_query
    db.query.return_value = mock_query
    return db, mock_query


def make_mock_image(**kwargs):
    """创建模拟的 Image ORM 对象，用于 query.all() 返回。"""
    defaults = {
        "id": 1,
        "title": "测试图片",
        "image_url": "http://example.com/img.jpg",
        "thumbnail_url": "http://example.com/thumb.jpg",
        "tags": ["nature"],
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# -----------------------------------------------------------------------------
# Service 层测试 — search_images()
# -----------------------------------------------------------------------------


class TestSearchImagesService:
    """测试 search_images 服务函数的查询构建逻辑。"""

    def test_default_pagination(self, mock_db):
        """默认分页 — 无参数调用，验证返回默认 page=1, limit=20 结构。"""
        db, mock_query = mock_db
        mock_query.all.return_value = []
        mock_query.scalar.return_value = 0

        params = SearchParams()
        result = search_images(db, params)

        assert result.total == 0
        assert result.page == 1
        assert result.pages == 1
        assert result.items == []
        # 验证 offset 计算：(1-1)*20 = 0
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(20)

    def test_keyword_search(self, mock_db):
        """关键词搜索 — q="风景"，验证 ILIKE 过滤条件被构建。"""
        db, mock_query = mock_db
        mock_image = make_mock_image(id=1, title="美丽风景")
        mock_query.all.return_value = [mock_image]
        mock_query.scalar.return_value = 1

        params = SearchParams(q="风景")
        result = search_images(db, params)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].title == "美丽风景"
        # 验证 filter 被调用（包含 ILIKE 条件）
        assert mock_query.filter.called

    def test_single_tag_filter(self, mock_db):
        """单个标签过滤 — tags=["nature"]，验证 JSONB 过滤被构建。"""
        db, mock_query = mock_db
        mock_image = make_mock_image(id=2, tags=["nature"])
        mock_query.all.return_value = [mock_image]
        mock_query.scalar.return_value = 1

        params = SearchParams(tags=["nature"])
        result = search_images(db, params)

        assert result.total == 1
        assert len(result.items) == 1
        # 验证 filter 被调用（包含 @> 操作）
        assert mock_query.filter.called

    def test_multiple_tags_filter(self, mock_db):
        """多标签过滤 — tags=["nature", "ai"]，验证多标签精确匹配。"""
        db, mock_query = mock_db
        mock_image = make_mock_image(id=3, tags=["nature", "ai", "art"])
        mock_query.all.return_value = [mock_image]
        mock_query.scalar.return_value = 1

        params = SearchParams(tags=["nature", "ai"])
        result = search_images(db, params)

        assert result.total == 1
        assert len(result.items) == 1
        assert set(result.items[0].tags) >= {"nature", "ai"}
        assert mock_query.filter.called

    def test_date_range_filter(self, mock_db):
        """日期范围过滤 — start_date + end_date，验证日期条件被构建。"""
        db, mock_query = mock_db
        mock_image = make_mock_image(
            id=4, created_at=datetime(2024, 6, 15, 10, 0, 0)
        )
        mock_query.all.return_value = [mock_image]
        mock_query.scalar.return_value = 1

        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 12, 31, 23, 59, 59)
        params = SearchParams(start_date=start, end_date=end)
        result = search_images(db, params)

        assert result.total == 1
        assert result.items[0].id == 4
        assert mock_query.filter.called

    def test_pagination_boundary(self, mock_db):
        """分页边界 — page=2, limit=10，验证 offset 计算正确。"""
        db, mock_query = mock_db
        mock_images = [
            make_mock_image(id=i, title=f"图片{i}")
            for i in range(11, 21)  # 第2页的10条数据
        ]
        mock_query.all.return_value = mock_images
        mock_query.scalar.return_value = 25  # 总共25条

        params = SearchParams(page=2, limit=10)
        result = search_images(db, params)

        assert result.total == 25
        assert result.page == 2
        assert result.pages == 3  # ceil(25/10) = 3
        assert len(result.items) == 10
        # 验证 offset 计算：(2-1)*10 = 10
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(10)

    def test_empty_result(self, mock_db):
        """空结果 — 无匹配条件，返回 total=0, items=[]。"""
        db, mock_query = mock_db
        mock_query.all.return_value = []
        mock_query.scalar.return_value = 0

        params = SearchParams(q="不存在的关键词")
        result = search_images(db, params)

        assert result.total == 0
        assert result.page == 1
        assert result.pages == 1
        assert result.items == []


# -----------------------------------------------------------------------------
# API 层测试 — GET /images/
# -----------------------------------------------------------------------------

client = TestClient(app)


class TestSearchImagesAPI:
    """测试图片搜索 API 端点的参数传递和响应格式。"""

    @patch("backend.routers.images.search_images")
    def test_api_default_params(self, mock_search):
        """API 默认参数 — 无查询参数调用，验证使用默认值。"""
        mock_search.return_value = SearchResponse(
            total=0, page=1, pages=1, items=[]
        )

        response = client.get("/images/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["pages"] == 1
        assert data["items"] == []

        # 验证 service 被调用，参数使用默认值
        params = mock_search.call_args[0][1]  # 第二个位置参数
        assert params.q is None
        assert params.tags is None
        assert params.page == 1
        assert params.limit == 20

    @patch("backend.routers.images.search_images")
    def test_api_keyword_search(self, mock_search):
        """API 关键词搜索 — 通过 query 参数传递 q="风景"。"""
        mock_image = ImageOut(
            id=1,
            title="风景图",
            image_url="http://example.com/1.jpg",
            thumbnail_url=None,
            tags=[],
            created_at=datetime(2024, 1, 1),
        )
        mock_search.return_value = SearchResponse(
            total=1, page=1, pages=1, items=[mock_image]
        )

        response = client.get("/images/?q=风景")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "风景图"

        params = mock_search.call_args[0][1]
        assert params.q == "风景"

    @patch("backend.routers.images.search_images")
    def test_api_with_tags(self, mock_search):
        """API 标签过滤 — 通过 query 参数传递 tags=["nature", "ai"。"""
        mock_search.return_value = SearchResponse(
            total=0, page=1, pages=1, items=[]
        )

        response = client.get("/images/?tags=nature&tags=ai")
        assert response.status_code == 200

        params = mock_search.call_args[0][1]
        assert params.tags == ["nature", "ai"]

    @patch("backend.routers.images.search_images")
    def test_api_pagination(self, mock_search):
        """API 分页参数 — 传递 page=2&limit=10。"""
        mock_search.return_value = SearchResponse(
            total=0, page=2, pages=1, items=[]
        )

        response = client.get("/images/?page=2&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2

        params = mock_search.call_args[0][1]
        assert params.page == 2
        assert params.limit == 10

    @patch("backend.routers.images.search_images")
    def test_api_date_range(self, mock_search):
        """API 日期范围 — 传递 start_date 和 end_date。"""
        mock_search.return_value = SearchResponse(
            total=0, page=1, pages=1, items=[]
        )

        response = client.get(
            "/images/?start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59"
        )
        assert response.status_code == 200

        params = mock_search.call_args[0][1]
        assert params.start_date is not None
        assert params.end_date is not None

    @patch("backend.routers.images.search_images")
    def test_api_combined_params(self, mock_search):
        """API 组合参数 — 同时传递 q, tags, page, limit。"""
        mock_search.return_value = SearchResponse(
            total=0, page=1, pages=1, items=[]
        )

        response = client.get("/images/?q=风景&tags=nature&page=1&limit=5")
        assert response.status_code == 200

        params = mock_search.call_args[0][1]
        assert params.q == "风景"
        assert params.tags == ["nature"]
        assert params.page == 1
        assert params.limit == 5

    @patch("backend.routers.images.search_images")
    def test_api_empty_result(self, mock_search):
        """API 空结果 — 无匹配时返回空列表和正确的分页信息。"""
        mock_search.return_value = SearchResponse(
            total=0, page=1, pages=1, items=[]
        )

        response = client.get("/images/?q=不存在的关键词")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
