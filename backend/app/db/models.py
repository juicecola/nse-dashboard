"""
models.py
---------
Postgres schema for the NSE dashboard.

  dim_ticker              - one row per listed security (name, sector)
  fact_daily_price         - one row per (ticker, trade_date): volume, close, change
  fact_market_index        - one row per (index_name, trade_date): NASI/NSE20/etc.
  fact_market_summary      - one row per trade_date: market-wide totals
  etl_run_log              - audit trail, same pattern as the cost-of-living project

This is a genuinely time-series schema (unlike the county project): every
fact table is grained by trade_date, and is meant to accumulate one new row
per ticker/index per trading day as the scraper runs - so a year of daily
runs gives you ~250 rows per ticker, which is exactly the shape a warehouse
is designed for.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DimTicker(Base):
    __tablename__ = "dim_ticker"

    ticker_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    sector_approx = Column(String, nullable=True)

    prices = relationship("FactDailyPrice", back_populates="ticker_ref")


class FactDailyPrice(Base):
    __tablename__ = "fact_daily_price"
    __table_args__ = (UniqueConstraint("ticker_id", "trade_date", name="uq_ticker_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker_id = Column(Integer, ForeignKey("dim_ticker.ticker_id"), nullable=False)
    trade_date = Column(Date, nullable=False)

    volume = Column(BigInteger, nullable=True)  # nullable: illiquid stocks may not trade that day
    close_price = Column(Float, nullable=True)
    change_abs = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)

    ticker_ref = relationship("DimTicker", back_populates="prices")


class FactMarketIndex(Base):
    __tablename__ = "fact_market_index"
    __table_args__ = (UniqueConstraint("index_name", "trade_date", name="uq_index_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_name = Column(String, nullable=False)  # 'NASI', 'NSE20', 'NSE25', 'NSE10', 'Banking'
    trade_date = Column(Date, nullable=False)
    close_value = Column(Float, nullable=False)
    change_abs = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)
    ytd_pct = Column(Float, nullable=True)
    source_url = Column(String, nullable=True)
    source_note = Column(String, nullable=True)


class FactMarketSummary(Base):
    __tablename__ = "fact_market_summary"

    trade_date = Column(Date, primary_key=True)
    total_shares_traded = Column(BigInteger, nullable=True)
    total_deals = Column(Integer, nullable=True)
    market_value_kes = Column(Float, nullable=True)
    market_cap_kes = Column(Float, nullable=True)
    gainers_count = Column(Integer, nullable=True)
    losers_count = Column(Integer, nullable=True)
    listed_companies_traded = Column(Integer, nullable=True)
    source_url = Column(String, nullable=True)


class ETLRunLog(Base):
    __tablename__ = "etl_run_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_date = Column(Date, nullable=False)
    task_name = Column(String, nullable=False)
    rows_loaded = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # 'success' | 'failed'
    detail = Column(String, nullable=True)
