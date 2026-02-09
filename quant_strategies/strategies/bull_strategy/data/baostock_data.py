#!/usr/bin/env python3
"""
BaoStock 数据源集成模块

提供股票数据获取功能：
- 日线数据
- 周线数据
- 复权因子
- 行业分类
"""

import baostock as bs
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time


class BaoStockData:
    """BaoStock 数据获取器"""
    
    def __init__(self):
        """初始化"""
        self.lg = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        连接 BaoStock
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.lg = bs.login()
            self.connected = (self.lg.error_code == '0')
            return self.connected
        except Exception as e:
            print(f"❌ BaoStock 连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.lg:
            bs.logout()
            self.connected = False
    
    def get_daily_data(self, 
                       stock_code: str,
                       start_date: str,
                       end_date: str,
                       adjust: str = '2') -> pd.DataFrame:
        """
        获取日线数据
        
        Args:
            stock_code: 股票代码 (e.g., 'sh.600000')
            start_date: 开始日期 (e.g., '20200101')
            end_date: 结束日期 (e.g., '20201231')
            adjust: 复权类型 (1=前复权, 2=后复权, 3=不复权)
        
        Returns:
            DataFrame: 日线数据
        """
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,preclose,volume,amount,turn,tradestatus,pctChg,isST",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag=adjust
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 转换数据类型
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            return df
            
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_list(self, 
                       date: str = None) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            date: 日期 (默认最新)
        
        Returns:
            DataFrame: 股票列表
        """
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            if date:
                rs = bs.query_all_stock(date)
            else:
                rs = bs.query_all_stock()
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            return df
            
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_industry_classification(self) -> pd.DataFrame:
        """
        获取行业分类
        
        Returns:
            DataFrame: 行业分类
        """
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            rs = bs.query_stock_industry()
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            return df
            
        except Exception as e:
            print(f"❌ 获取行业分类失败: {e}")
            return pd.DataFrame()


class BullDataLoader:
    """Bull 策略数据加载器"""
    
    def __init__(self):
        """初始化"""
        self.baostock = BaoStockData()
    
    def load_stock_data(self, 
                        stock_codes: List[str],
                        start_date: str,
                        end_date: str) -> Dict[str, pd.DataFrame]:
        """
        加载多只股票数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            Dict: {股票代码: DataFrame}
        """
        data = {}
        
        for code in stock_codes:
            print(f"📥 加载 {code}...")
            df = self.baostock.get_daily_data(code, start_date, end_date)
            if not df.empty:
                data[code] = df
            time.sleep(0.1)  # 避免请求过快
        
        return data
    
    def load_market_data(self, 
                          index_code: str = 'sh.000001',
                          start_date: str = '20200101',
                          end_date: str = '20201231') -> pd.DataFrame:
        """
        获取大盘指数数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            DataFrame: 指数数据
        """
        return self.baostock.get_daily_data(index_code, start_date, end_date)


if __name__ == "__main__":
    # 测试
    print("🧪 测试 BaoStock 数据源...")
    
    loader = BullDataLoader()
    
    # 测试获取单只股票
    df = loader.baostock.get_daily_data('sh.600000', '20200101', '20200131')
    
    if not df.empty:
        print(f"✅ 成功获取 {len(df)} 条数据")
        print(df.head())
    else:
        print("❌ 获取数据失败")
    
    loader.baostock.disconnect()
