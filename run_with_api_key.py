import os
import pandas as pd
from financial_data_analyzer_alpha_vantage import AlphaVantageFinancialDataAnalyzer

# 设置API密钥
os.environ['ALPHA_VANTAGE_API_KEY'] = 'AYIVXRHGGOO2RXH6'

# 创建分析器实例（将从环境变量获取API密钥）
analyzer = AlphaVantageFinancialDataAnalyzer()

def calculate_daily_volatility_from_three_months(data):
    """
    从三个月数据中计算日波动率（使用最新的30个交易日）
    
    Args:
        data (pandas.DataFrame): 三个月的金融数据
        
    Returns:
        float: 日波动率
    """
    if data.empty:
        print("警告: 数据为空，无法计算日波动率")
        return 0.0
    
    # 选取最新的30个交易日
    recent_data = data.tail(30)
    
    # 计算每日收益率
    recent_data = recent_data.copy()
    recent_data['Daily_Return'] = recent_data['Close'].pct_change()
    # 计算日波动率（标准差）
    daily_volatility = recent_data['Daily_Return'].std()
    return daily_volatility

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
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{symbol}_past_three_months_data_{timestamp}.xlsx"
    export_result = analyzer.export_to_excel(data, symbol, filename)
    
    # 计算各种指标
    print("\n计算分析指标...")
    
    # 持仓占比
    position_ratio = analyzer.calculate_position_ratio(data, position_size)
    print(f"持仓占比: {position_ratio:.4f}")
    
    # 盈亏计算
    pnl = analyzer.calculate_pnl(data, position_size, buy_price)
    print(f"盈亏: {pnl:.2f}")
    
    # 日波动率（从三个月数据中选取最新的30个交易日）
    daily_volatility = calculate_daily_volatility_from_three_months(data)
    print(f"日波动率: {daily_volatility:.4f}")
    
    # 在险价值（使用三个月数据）
    var = analyzer.calculate_value_at_risk(data)
    print(f"在险价值 (95% 置信度): {var:.4f}")
    
    # 贝塔系数（使用三个月数据）
    beta = analyzer.calculate_beta(data)
    if beta is not None:
        print(f"贝塔系数: {beta:.4f}")
    else:
        print("贝塔系数: 无法计算")

if __name__ == "__main__":
    main()