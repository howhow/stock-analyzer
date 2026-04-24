"""数据库真实操作集成测试"""

import pytest


@pytest.mark.integration
class TestDatabaseIntegration:
    """数据库真实操作集成测试"""

    def test_database_connection(self):
        """验证数据库连接"""
        import os

        from sqlalchemy import create_engine, text

        # 使用 sqlite 进行同步测试
        database_url = os.getenv(
            "DATABASE_URL", "sqlite:///local_test_report/test_integration.db"
        )

        # 如果是 asyncpg URL，转为 sqlite
        if database_url.startswith("postgresql+asyncpg"):
            database_url = "sqlite:///local_test_report/test_integration.db"

        engine = create_engine(database_url, echo=False)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_database_crud(self):
        """数据库CRUD操作"""
        import os

        from sqlalchemy import Column, Integer, String, create_engine
        from sqlalchemy.orm import declarative_base, sessionmaker

        # 使用 sqlite 进行同步测试
        database_url = os.getenv(
            "DATABASE_URL", "sqlite:///local_test_report/test_integration.db"
        )

        # 如果是 asyncpg URL，转为 sqlite
        if database_url.startswith("postgresql+asyncpg"):
            database_url = "sqlite:///local_test_report/test_integration.db"

        engine = create_engine(database_url, echo=False)
        Base = declarative_base()

        class TestModel(Base):
            __tablename__ = "test_integration"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Create
            obj = TestModel(name="integration_test")
            session.add(obj)
            session.commit()

            # Read
            result = session.query(TestModel).filter_by(name="integration_test").first()
            assert result is not None
            assert result.name == "integration_test"

            # Update
            result.name = "updated"
            session.commit()

            # Delete
            session.delete(result)
            session.commit()

            # Verify delete
            assert session.query(TestModel).filter_by(name="updated").first() is None
        finally:
            session.close()
