import json
import os
import glob
from datetime import datetime
from stress_scenario_analyzer import StressScenarioAnalyzer


def find_latest_financial_analysis_file():
    """
    查找最新的金融分析JSON文件
    
    Returns:
        str: 最新JSON文件的路径，如果未找到则返回None
    """
    # 查找所有以financial_analysis_开头的JSON文件
    json_files = glob.glob("financial_analysis_*.json")
    
    if not json_files:
        return None
    
    # 按修改时间排序，返回最新的文件
    latest_file = max(json_files, key=os.path.getmtime)
    return latest_file


def read_portfolio_data_from_file(filename):
    """
    从文件中读取持仓数据
    
    Args:
        filename (str): JSON文件名
        
    Returns:
        list: 持仓数据列表
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"错误: 找不到文件 {filename}")
        return []
    except json.JSONDecodeError:
        print(f"错误: 文件 {filename} 不是有效的JSON格式")
        return []
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return []


def convert_data_format(portfolio_data):
    """
    转换数据格式以适配压力情景分析模块
    
    Args:
        portfolio_data (list): 原始持仓数据
        
    Returns:
        list: 转换后的数据格式
    """
    converted_data = []
    
    for item in portfolio_data:
        # 检查是否已经是目标格式
        if all(key in item for key in ['currency', 'quantity', 'buyPrice', 'proportion', 
                                      'benefit', 'dailyVolatility', 'valueAtRisk', 'beta']):
            converted_data.append(item)
        else:
            # 转换格式
            converted_item = {
                "currency": item.get("currency", item.get("symbol", "")),
                "quantity": item.get("quantity", item.get("position_size", 0)),
                "buyPrice": item.get("buyPrice", item.get("buy_price", 0)),
                "proportion": item.get("proportion", item.get("position_ratio", 0)),
                "benefit": item.get("benefit", item.get("pnl", 0)),
                "dailyVolatility": item.get("dailyVolatility", item.get("daily_volatility", 0)),
                "valueAtRisk": item.get("valueAtRisk", f"${abs(item.get('value_at_risk', 0) * 100000):,.0f}" 
                                      if item.get('value_at_risk') is not None else "$0"),
                "beta": item.get("beta", 0)
            }
            converted_data.append(converted_item)
    
    return converted_data


def main():
    """
    主函数，读取持仓数据并执行压力情景分析
    """
    print("=== 压力情景分析工具 ===")
    
    # 自动查找最新的金融分析JSON文件
    json_filename = find_latest_financial_analysis_file()
    
    if json_filename:
        print(f"找到最新的分析文件: {json_filename}")
        use_latest = input("是否使用此文件？(Y/n): ").strip().lower()
        if use_latest == 'n':
            json_filename = input("请输入包含持仓数据的JSON文件名: ").strip()
    else:
        # 获取JSON文件名
        json_filename = input("未找到自动分析文件，请输入包含持仓数据的JSON文件名: ").strip()
    
    if not json_filename:
        print("错误: 文件名不能为空")
        return
    
    # 读取持仓数据
    print(f"正在读取 {json_filename}...")
    portfolio_data = read_portfolio_data_from_file(json_filename)
    
    if not portfolio_data:
        print("无法读取持仓数据，程序退出")
        return
    
    # 转换数据格式
    if isinstance(portfolio_data, list) and len(portfolio_data) > 0:
        # 如果是列表，直接转换
        converted_data = convert_data_format(portfolio_data)
    else:
        print("数据格式不正确，程序退出")
        return
    
    print(f"成功读取 {len(converted_data)} 条持仓记录")
    
    # 获取事件描述
    event_description = input("请输入事件描述 (例如: 伊朗以色列发生战争，伊朗有意封锁霍尔木兹海峡): ").strip()
    if not event_description:
        print("错误: 事件描述不能为空")
        return
    
    # 检查并设置API密钥
    api_key = os.environ.get('ARK_API_KEY')
    if not api_key:
        print("警告: 未设置 ARK_API_KEY 环境变量")
        api_key_input = input(f"请输入API密钥 (默认使用 b1fd5cf9-f813-4a3a-8f3d-f51b2d3c3f82): ").strip()
        if not api_key_input:
            api_key_input = "b1fd5cf9-f813-4a3a-8f3d-f51b2d3c3f82"
        os.environ['ARK_API_KEY'] = api_key_input
        print("API密钥已设置")
    
    # 创建分析器并执行分析
    print("正在执行压力情景分析...")
    # 使用用户指定的模型接入点
    analyzer = StressScenarioAnalyzer([
        'ep-20250824194947-wrm8q',  # 第一个大模型接入点
        'ep-20250824195709-jdklb'   # 第二个大模型接入点
    ])
    
    try:
        result = analyzer.analyze(converted_data, event_description)
        
        # 输出结果到文件
        output_filename = f"stress_analysis_result_{json_filename}"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n分析完成，结果已保存到 {output_filename}")
        print("\n分析结果摘要:")
        event_analysis = result.get('event_analysis', {})
        if event_analysis:
            print(f"事件类型: {event_analysis.get('event_type', 'N/A')}")
            print(f"事件严重程度: {event_analysis.get('severity', 0):.2f}")
        else:
            print("事件分析: 未能成功获取分析结果")
            
        portfolio_impact = result.get('portfolio_impact', {})
        print(f"预测阿尔法值: {portfolio_impact.get('predicted_alpha_t', 0):.2f}")
        
        most_affected = portfolio_impact.get('most_affected_pair')
        if most_affected:
            print(f"受影响最大的货币对: {most_affected.get('currency', 'N/A')}")
            print(f"影响方向: {most_affected.get('impact_direction', 'N/A')}")
        
        recommendations = result.get('hedging_recommendations', [])
        if recommendations:
            print(f"\n对冲建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec.get('action', 'N/A')} - {rec.get('instrument', 'N/A')}")
                print(f"   对冲比例: {rec.get('hedging_ratio', 'N/A')}")
                print(f"   理由: {rec.get('reason', 'N/A')}")
        else:
            print("\n无对冲建议生成")
        
    except Exception as e:
        print(f"分析过程中出错: {str(e)}")


if __name__ == "__main__":
    main()