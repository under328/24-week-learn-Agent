"""
DB 模块 - 数据库连接管理

【对应学习日】Day35: SQLAlchemy 连接池 + 上下文管理器
【核心概念】
  - Engine:连接工厂(管理连接池)
  - Session:工作单元(每次请求一个 Session)
  - 连接池:复用数据库连接,避免频繁建连/断连
  - 上下文管理器:确保 Session 正确关闭(with 语句)

【连接池参数】
  pool_size:    常驻连接数(5-20)
  max_overflow: 临时连接数(超出 pool_size 后允许的数量)
  pool_recycle: 连接回收时间(避免 MySQL 8 小时断连)
  pool_pre_ping: 使用前检查连接(避免使用已断开的连接)
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DBSession
import config

# 创建 Engine(全局唯一,管理连接池)
engine = create_engine(
    config.DATABASE_URL,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_recycle=config.DB_POOL_RECYCLE,
    pool_pre_ping=True,     # 使用前 ping,避免使用已断开的连接
    echo=False,             # True = 打印 SQL 日志(调试用)
)

# Session 工厂(每次调用创建一个新 Session)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """初始化数据库:创建所有表"""
    from db.models import Base
    Base.metadata.create_all(engine)
    print("[DB] 数据库初始化完成")


@contextmanager
def get_db():
    """
    获取数据库 Session(上下文管理器)

    使用方式:
      with get_db() as db:
          session = db.query(Session).first()
          db.commit()

    自动处理:
      - 正常退出 → commit
      - 异常退出 → rollback
      - 无论如何 → close
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_dependency():
    """
    FastAPI 依赖注入版本的 get_db

    使用方式:
      @app.get("/items")
      def get_items(db: DBSession = Depends(get_db_dependency)):
          ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
