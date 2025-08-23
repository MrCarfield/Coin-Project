import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import json


class AlphaVantageFinancialDataAnalyzer:
    """
    基于Alpha Vantage API的金融数据分析器类
    """

    def __init__(self, api_key=None):
        """
        初始化金融数据分析器
        
        Args:
            api_key (str): Alpha Vantage API密钥，如果为None则尝试从环境变量获取，再没有则使用demo密钥
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get('ALPHA_VANTAGE_API_KEY') or 'demo'
        
        self.base_url = 'https://www.alphavantage.co/query'
        print(f"使用API密钥: {'demo' if self.api_key == 'demo' else '您的API密钥'}")

    def get_past_month_data(self, symbol, max_retries=3):
        """
        获取过去一个月的交易数据
        
        Args:
            symbol (str): 股票或其他金融工具的代码
            max_retries (int): 最大重试次数
            
        Returns:
            pandas.DataFrame: 包含过去一个月交易数据的DataFrame
        """
        # Alpha Vantage免费版API限制：每分钟5次请求，每天500次请求
        # 使用基础的TIME_SERIES_DAILY而不是TIME_SERIES_DAILY_ADJUSTED以避免付费墙
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'compact'  # compact返回最近100条数据，full返回20年数据
        }
        
        # 使用重试机制
        for attempt in range(max_retries):
            try:
                print(f"正在尝试获取 {symbol} 的数据... (尝试 {attempt + 1}/{max_retries})")
                
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # 检查是否有错误信息
                if "Error Message" in data:
                    print(f"API错误: {data['Error Message']}")
                    return pd.DataFrame()
                
                if "Note" in data:
                    print(f"API提醒: {data['Note']}")
                    # 如果是频率限制，等待更长时间
                    if "higher call frequency" in data["Note"]:
                        wait_time = 60 * (attempt + 1)  # 等待1分钟、2分钟、3分钟
                        print(f"遇到频率限制，等待 {wait_time} 秒...")
                        time.sleep(wait_time)
                        continue
                
                if "Time Series (Daily)" not in data:
                    print("返回数据格式不正确")
                    print(f"收到的数据: {json.dumps(data, indent=2)[:500]}...")  # 打印前500个字符用于调试
                    return pd.DataFrame()
                
                # 解析数据
                ts_data = data["Time Series (Daily)"]
                
                # 转换为DataFrame
                df = pd.DataFrame.from_dict(ts_data, orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # 重命名列
                df.rename(columns={
                    '1. open': 'Open',
                    '2. high': 'High',
                    '3. low': 'Low',
                    '4. close': 'Close',
                    '5. volume': 'Volume'
                }, inplace=True)
                
                # 转换数据类型
                for col in ['Open', 'High', 'Low', 'Close']:
                    df[col] = pd.to_numeric(df[col])
                df['Volume'] = pd.to_numeric(df['Volume'])
                
                # 只保留过去一个月的数据
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                df = df[(df.index >= start_date) & (df.index <= end_date)]
                
                if not df.empty:
                    print(f"成功获取 {symbol} 的数据")
                    return df
                else:
                    print(f"获取到的数据为空")
                    return df
                    
            except Exception as e:
                print(f"获取数据时出错: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print("已达到最大重试次数，无法获取数据")
        
        # 如果所有尝试都失败，返回空DataFrame
        return pd.DataFrame()

    def get_past_three_months_data(self, symbol, max_retries=3):
        """
        获取过去三个月的交易数据
        
        Args:
            symbol (str): 股票或其他金融工具的代码
            max_retries (int): 最大重试次数
            
        Returns:
            pandas.DataFrame: 包含过去三个月交易数据的DataFrame
        """
        # Alpha Vantage免费版API限制：每分钟5次请求，每天500次请求
        # 使用基础的TIME_SERIES_DAILY而不是TIME_SERIES_DAILY_ADJUSTED以避免付费墙
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full'  # full返回20年数据，可以从中提取三个月的数据
        }
        
        # 使用重试机制
        for attempt in range(max_retries):
            try:
                print(f"正在尝试获取 {symbol} 的三个月数据... (尝试 {attempt + 1}/{max_retries})")
                
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # 检查是否有错误信息
                if "Error Message" in data:
                    print(f"API错误: {data['Error Message']}")
                    return pd.DataFrame()
                
                if "Note" in data:
                    print(f"API提醒: {data['Note']}")
                    # 如果是频率限制，等待更长时间
                    if "higher call frequency" in data["Note"]:
                        wait_time = 60 * (attempt + 1)  # 等待1分钟、2分钟、3分钟
                        print(f"遇到频率限制，等待 {wait_time} 秒...")
                        time.sleep(wait_time)
                        continue
                
                if "Time Series (Daily)" not in data:
                    print("返回数据格式不正确")
                    print(f"收到的数据: {json.dumps(data, indent=2)[:500]}...")  # 打印前500个字符用于调试
                    return pd.DataFrame()
                
                # 解析数据
                ts_data = data["Time Series (Daily)"]
                
                # 转换为DataFrame
                df = pd.DataFrame.from_dict(ts_data, orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # 重命名列
                df.rename(columns={
                    '1. open': 'Open',
                    '2. high': 'High',
                    '3. low': 'Low',
                    '4. close': 'Close',
                    '5. volume': 'Volume'
                }, inplace=True)
                
                # 转换数据类型
                for col in ['Open', 'High', 'Low', 'Close']:
                    df[col] = pd.to_numeric(df[col])
                df['Volume'] = pd.to_numeric(df['Volume'])
                
                # 只保留过去三个月的数据
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                df = df[(df.index >= start_date) & (df.index <= end_date)]
                
                if not df.empty:
                    print(f"成功获取 {symbol} 的三个月数据")
                    return df
                else:
                    print(f"获取到的数据为空")
                    return df
                    
            except Exception as e:
                print(f"获取数据时出错: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print("已达到最大重试次数，无法获取数据")
        
        # 如果所有尝试都失败，返回空DataFrame
        return pd.DataFrame()

    def export_to_excel(self, data, symbol, filename=None):
        """
        将数据导出到Excel文件
        
        Args:
            data (pandas.DataFrame): 要导出的数据
            symbol (str): 金融工具代码
            filename (str, optional): 文件名，如果未提供则自动生成
            
        Returns:
            str: 导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{symbol}_past_three_months_data_{timestamp}.xlsx"  # 修改为三个月数据
        
        # 确保文件名以.xlsx结尾
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        try:
            # 导出到Excel
            data.to_excel(filename)
            print(f"数据已成功导出到: {filename}")
            return filename
        except Exception as e:
            print(f"导出Excel文件时出错: {str(e)}")
            return None
            
    def calculate_position_ratio(self, data, position_size, total_assets=None):
        """
        计算持仓占比
        
        Args:
            data (pandas.DataFrame): 金融数据
            position_size (float): 持仓量
            total_assets (float, optional): 总资产，如果未提供则提示用户输入
            
        Returns:
            float: 持仓占比
        """
        if data.empty:
            print("警告: 数据为空，无法计算持仓占比")
            return 0.0
            
        # 计算持仓价值
        latest_close_price = data['Close'].iloc[-1]
        position_value = position_size * latest_close_price
        
        # 获取总资产
        if total_assets is None:
            try:
                total_assets_input = input("请输入您的总资产金额（直接回车默认为1,000,000）: ").strip()
                if total_assets_input:
                    total_assets = float(total_assets_input)
                else:
                    total_assets = 1000000  # 默认值
                    print("使用默认总资产: 1,000,000")
            except ValueError:
                print("输入无效，使用默认总资产: 1,000,000")
                total_assets = 1000000
        
        position_ratio = position_value / total_assets
        print(f"持仓价值: {position_value:.2f}")
        print(f"总资产: {total_assets:.2f}")
        return position_ratio

    def calculate_pnl(self, data, position_size, buy_price):
        """
        计算盈亏
        
        Args:
            data (pandas.DataFrame): 金融数据
            position_size (float): 持仓量
            buy_price (float): 买入价格
            
        Returns:
            float: 盈亏
        """
        if data.empty:
            print("警告: 数据为空，无法计算盈亏")
            return 0.0
            
        current_price = data['Close'].iloc[-1]
        pnl = position_size * (current_price - buy_price)
        return pnl

    def calculate_daily_volatility(self, data):
        """
        计算日波动率
        
        Args:
            data (pandas.DataFrame): 金融数据（最近30个交易日）
            
        Returns:
            float: 日波动率
        """
        if data.empty:
            print("警告: 数据为空，无法计算日波动率")
            return 0.0
            
        # 计算每日收益率
        data['Daily_Return'] = data['Close'].pct_change()
        # 计算日波动率（标准差）
        daily_volatility = data['Daily_Return'].std()
        return daily_volatility

    def calculate_value_at_risk(self, data, confidence_level=0.05):
        """
        计算在险价值(Value at Risk)
        
        Args:
            data (pandas.DataFrame): 金融数据
            confidence_level (float): 置信水平，默认为0.05（95%置信度）
            
        Returns:
            float: 在险价值
        """
        if data.empty:
            print("警告: 数据为空，无法计算在险价值")
            return 0.0
            
        # 计算每日收益率
        data['Daily_Return'] = data['Close'].pct_change()
        # 计算在险价值（使用历史模拟法，取分位数）
        var = data['Daily_Return'].quantile(confidence_level)
        return var

    def calculate_beta(self, data, market_symbol='SPY'):
        """
        计算贝塔系数（基于SPY ETF作为市场基准）
        
        Args:
            data (pandas.DataFrame): 金融数据
            market_symbol (str): 市场基准代码，默认为SPY（标普500ETF）
            
        Returns:
            float: 贝塔系数
        """
        if data.empty:
            print("警告: 数据为空，无法计算贝塔系数")
            return None
            
        try:
            # 获取市场数据
            market_data = self.get_past_three_months_data(market_symbol)
            
            if market_data.empty:
                print(f"警告: 无法获取市场数据 {market_symbol}")
                return None
                
            # 计算收益率
            data['Daily_Return'] = data['Close'].pct_change()
            market_data['Market_Return'] = market_data['Close'].pct_change()
            
            # 合并数据
            combined_data = pd.merge(data[['Daily_Return']], market_data[['Market_Return']], 
                                    left_index=True, right_index=True, how='inner')
            
            # 删除NaN值
            combined_data = combined_data.dropna()
            
            # 计算贝塔系数
            if len(combined_data) > 0:
                beta = combined_data['Daily_Return'].cov(combined_data['Market_Return']) / \
                       combined_data['Market_Return'].var()
                return beta
            else:
                print("警告: 合并后的数据为空，无法计算贝塔系数")
                return None
        except Exception as e:
            print(f"计算贝塔系数时出错: {str(e)}")
            return None


def main():
    """
    主函数，演示如何使用AlphaVantageFinancialDataAnalyzer类
    """
    print("=== 基于Alpha Vantage API的金融数据分析工具 ===")
    print(f"当前使用的API密钥: {'demo' if analyzer.api_key == 'demo' else '您的API密钥'}")
    
    if analyzer.api_key == 'demo':
        print("注意: 您正在使用demo密钥，功能受限。建议注册获取免费API密钥以获得更好的体验。")
        print("注册地址: https://www.alphavantage.co/support/#api-key")
    
    # 获取用户输入
    symbol = input("请输入金融工具代码 (例如: MSFT, AAPL, GOOGL): ").strip()
    if not symbol:
        print("错误: 金融工具代码不能为空")
        return
    
    try:
        position_size = float(input("请输入持仓量: ") or 0)
    except ValueError:
        print("错误: 持仓量必须是数字")
        return
    
    buy_price_input = input("请输入买入价格 (直接回车将使用当前价格): ").strip()
    buy_price = None
    if buy_price_input:
        try:
            buy_price = float(buy_price_input)
        except ValueError:
            print("错误: 买入价格必须是数字")
            return
    
    # 直接获取过去三个月的数据
    print(f"\n正在获取 {symbol} 过去三个月的数据...")
    data = analyzer.get_past_three_months_data(symbol)
    
    if data.empty:
        print(f"\n*** 无法获取 {symbol} 的数据 ***")
        print("可能的原因:")
        print("1. 金融工具代码不正确")
        print("2. Alpha Vantage API访问限制，请稍后再试")
        print("3. 网络连接问题")
        print("\n建议:")
        print("- 检查金融工具代码是否正确")
        print("- 稍后再试，避开API访问高峰期")
        print("- 考虑注册Alpha Vantage获取免费API密钥以获得更高请求频率")
        print("  注册地址: https://www.alphavantage.co/support/#api-key")
        return
    
    # 如果用户没有输入买入价格，则使用当前价格
    if buy_price is None:
        buy_price = data['Close'].iloc[-1]
        print(f"使用当前价格作为买入价格: {buy_price:.2f}")
    
    # 显示数据基本信息
    print(f"\n{symbol} 过去三个月的数据:")
    print(data.head().to_string())
    print(f"\n数据形状: {data.shape}")
    
    # 导出到Excel
    filename = analyzer.export_to_excel(data, symbol)
    if not filename:
        print("数据导出失败")
        return
    
    # 计算各种指标
    print("\n计算分析指标...")
    
    # 持仓占比
    position_ratio = analyzer.calculate_position_ratio(data, position_size)
    print(f"持仓占比: {position_ratio:.4f}")
    
    # 盈亏计算
    pnl = analyzer.calculate_pnl(data, position_size, buy_price)
    print(f"盈亏: {pnl:.2f}")
    
    # 日波动率（使用最近30个交易日的数据）
    recent_data = data.tail(30)  # 选取最近30个交易日
    daily_volatility = analyzer.calculate_daily_volatility(recent_data)
    print(f"日波动率: {daily_volatility:.4f}")
    
    # 在险价值
    var = analyzer.calculate_value_at_risk(data)
    print(f"在险价值 (95% 置信度): {var:.4f}")
    
    # 贝塔系数
    beta = analyzer.calculate_beta(data)
    if beta is not None:
        print(f"贝塔系数: {beta:.4f}")
    else:
        print("贝塔系数: 无法计算")


# 创建分析器实例（使用demo密钥或环境变量中的密钥）
analyzer = AlphaVantageFinancialDataAnalyzer()

if __name__ == "__main__":
    main()