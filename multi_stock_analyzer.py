import os
import pandas as pd
import json
import numpy as np
from datetime import datetime
from financial_data_analyzer_alpha_vantage import AlphaVantageFinancialDataAnalyzer

# 设置API密钥
api_key = 'AYIVXRHGGOO2RXH6'
analyzer = AlphaVantageFinancialDataAnalyzer(api_key=api_key)

def get_stock_data():
    """
    获取单个股票的数据
    """
    symbol = input("请输入金融工具代码 (例如: MSFT, AAPL, GOOGL): ").strip()
    if not symbol:
        print("错误: 金融工具代码不能为空")
        return None, None, None, None
    
    try:
        position_size = float(input(f"请输入 {symbol} 的持仓量: ") or 0)
    except ValueError:
        print("错误: 持仓量必须是数字")
        return None, None, None, None
    
    buy_price_input = input(f"请输入 {symbol} 的买入价格 (直接回车将使用当前价格): ").strip()
    buy_price = None
    if buy_price_input:
        try:
            buy_price = float(buy_price_input)
        except ValueError:
            print("错误: 买入价格必须是数字")
            return None, None, None, None
    
    # 直接获取过去三个月的数据
    print(f"\n正在获取 {symbol} 过去三个月的数据...")
    data_three_months = analyzer.get_past_three_months_data(symbol)
    
    if data_three_months.empty:
        print(f"\n*** 无法获取 {symbol} 的三个月数据 ***")
        return None, None, None, None
    
    # 如果用户没有输入买入价格，则使用当前价格
    if buy_price is None:
        buy_price = data_three_months['Close'].iloc[-1]
        print(f"使用当前价格作为买入价格: {buy_price:.2f}")
    
    return symbol, data_three_months, position_size, buy_price

def calculate_total_assets(stock_data_list):
    """
    计算总资产价值
    
    Args:
        stock_data_list: 股票数据列表 [(symbol, data_three_months, position_size, buy_price), ...]
        
    Returns:
        float: 总资产价值
    """
    total_value = 0
    print("\n计算各股票持仓价值:")
    for symbol, data_three_months, position_size, buy_price in stock_data_list:
        latest_close_price = data_three_months['Close'].iloc[-1]
        position_value = position_size * latest_close_price
        total_value += position_value
        print(f"{symbol}: {position_size} 股 × {latest_close_price:.2f} = {position_value:.2f}")
    
    print(f"\n总资产价值: {total_value:.2f}")
    return total_value

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

def format_analysis_as_json(symbol, position_size, buy_price, position_ratio, pnl, 
                           daily_volatility, var, beta):
    """
    将分析结果格式化为指定的JSON格式
    
    Args:
        symbol (str): 货币对或股票代码
        position_size (float): 持仓量
        buy_price (float): 买入价格
        position_ratio (float): 持仓占比
        pnl (float): 盈亏
        daily_volatility (float): 日波动率
        var (float): 在险价值
        beta (float): Beta系数
        
    Returns:
        dict: 格式化的JSON数据
    """
    # 格式化VaR值为带美元符号的字符串
    var_formatted = f"${abs(var * 100000):,.0f}" if var < 0 else f"${var * 100000:,.0f}"
    
    formatted_data = {
        "currency": symbol,  # 货币对
        "quantity": position_size,  # 持仓量
        "buyPrice": buy_price,  # 买入价格
        "proportion": round(position_ratio, 4),  # 持仓占比
        "benefit": round(pnl, 2),  # 盈亏
        "dailyVolatility": round(daily_volatility, 4),  # 日波动率
        "valueAtRisk": var_formatted,  # VaR(95%)
        "beta": round(beta, 2)  # Beta系数
    }
    
    return formatted_data

def analyze_stock(symbol, data_three_months, position_size, buy_price, total_assets):
    """
    分析单个股票
    
    Args:
        symbol: 股票代码
        data_three_months: 股票三个月的数据
        position_size: 持仓量
        buy_price: 买入价格
        total_assets: 总资产
    """
    print(f"\n=== 分析 {symbol} ===")
    
    # 显示数据基本信息
    print(f"\n{symbol} 过去三个月的数据:")
    print(data_three_months.head().to_string())
    print(f"\n数据形状: {data_three_months.shape}")
    
    # 导出到Excel（使用三个月的数据）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f"{symbol}_past_three_months_data_{timestamp}.xlsx"
    export_result = analyzer.export_to_excel(data_three_months, symbol, excel_filename)
    if not export_result:
        print("Excel数据导出失败")
    
    # 计算各种指标
    print("\n计算分析指标...")
    
    # 持仓占比（基于总资产计算，确保正确性）
    latest_close_price = data_three_months['Close'].iloc[-1]
    position_value = position_size * latest_close_price
    position_ratio = position_value / total_assets if total_assets > 0 else 0
    print(f"持仓价值: {position_value:.2f}")
    print(f"持仓占比: {position_ratio:.4f} ({position_ratio*100:.2f}%)")
    
    # 盈亏计算
    pnl = analyzer.calculate_pnl(data_three_months, position_size, buy_price)
    print(f"盈亏: {pnl:.2f}")
    
    # 日波动率（从三个月数据中选取最新的30个交易日）
    daily_volatility = calculate_daily_volatility_from_three_months(data_three_months)
    print(f"日波动率: {daily_volatility:.4f}")
    
    # 在险价值（使用三个月数据，95%置信度）
    var = analyzer.calculate_value_at_risk(data_three_months)
    print(f"在险价值 (95% 置信度): {var:.4f}")
    
    # 贝塔系数（使用三个月数据）
    beta = analyzer.calculate_beta(data_three_months)
    if beta is not None:
        print(f"贝塔系数: {beta:.4f}")
    else:
        print("贝塔系数: 无法计算")
    
    # 格式化为指定JSON格式并打印
    formatted_json = format_analysis_as_json(
        symbol, position_size, buy_price, position_ratio, pnl, 
        daily_volatility, var, beta if beta is not None else 0
    )
    
    print(f"\n{symbol} 的格式化分析结果:")
    print(json.dumps(formatted_json, indent=2))
    
    # 返回分析结果
    return {
        "symbol": symbol,
        "position_size": float(position_size),
        "buy_price": float(buy_price),
        "current_price": float(latest_close_price),
        "position_value": float(position_value),
        "position_ratio": float(position_ratio),  # 确保使用基于总资产计算的正确比例
        "pnl": float(pnl),
        "daily_volatility": float(daily_volatility),
        "value_at_risk": float(var),
        "beta": float(beta) if beta is not None else None,
        "excel_file": excel_filename,
        "formatted_json": formatted_json
    }

def main():
    """
    主函数
    """
    print("=== 基于Alpha Vantage API的多股票金融数据分析工具 ===")
    print(f"当前使用的API密钥: {'您的API密钥' if analyzer.api_key != 'demo' else 'demo'}")
    
    stock_data_list = []
    
    # 循环获取股票数据
    while True:
        result = get_stock_data()
        if result[0] is not None:  # 成功获取数据
            symbol, data_three_months, position_size, buy_price = result
            stock_data_list.append((symbol, data_three_months, position_size, buy_price))
        
        # 询问是否继续添加股票
        more = input("\n是否还有其他股票需要分析？(y/n): ").strip().lower()
        if more not in ['y', 'yes', '是', '']:
            break
    
    if not stock_data_list:
        print("没有获取到任何股票数据")
        return
    
    # 计算总资产
    total_assets = calculate_total_assets(stock_data_list)
    
    # 验证总资产不为0
    if total_assets <= 0:
        print("总资产为0，无法计算持仓占比")
        return
    
    # 分析每个股票并收集结果
    analysis_results = []
    formatted_results = []
    for symbol, data_three_months, position_size, buy_price in stock_data_list:
        result = analyze_stock(symbol, data_three_months, position_size, buy_price, total_assets)
        analysis_results.append(result)
        formatted_results.append(result["formatted_json"])
    
    # 验证持仓占比总和是否为1（考虑浮点数精度）
    total_proportion = sum(result["position_ratio"] for result in analysis_results)
    print(f"\n所有股票持仓占比总和: {total_proportion:.4f}")
    
    # 导出所有格式化的JSON结果到一个文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"financial_analysis_{timestamp}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n所有股票的分析结果已导出到: {output_filename}")

if __name__ == "__main__":
    main()