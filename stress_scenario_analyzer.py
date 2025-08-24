import os
import json
import requests
from typing import Dict, Any, List, Tuple
import statistics
from numbers import Number


class StressScenarioAnalyzer:
    """
    压力情景分析模块，用于分析金融事件对用户持仓的影响
    """

    def __init__(self, models: List[str] = None):
        """
        初始化压力情景分析器
        
        Args:
            models: 使用的模型列表，默认使用用户指定的模型
        """
        self.api_key = os.environ.get('ARK_API_KEY')
        self.base_url = 'https://ark.cn-beijing.volces.com/api/v3'
        
        # 使用用户指定的模型
        self.available_models = models or [
            'ep-20250824194947-wrm8q',  # 第一个大模型接入点
            'ep-20250824195709-jdklb'   # 第二个大模型接入点
        ]
        
        # 定义Prompt模板
        self.event_classification_prompt = """
请分析以下金融事件并提供结构化输出：

事件描述: {event_description}

请严格按照以下JSON格式输出:
{{
  "event_type": "事件类型，例如：地缘政治、经济数据、货币政策等",
  "factor_directions": {{
    "OIL": "石油价格影响方向：positive(上涨)、negative(下跌)、neutral(中性)",
    "RISK": "风险偏好影响方向：positive(风险偏好增加)、negative(风险规避增加)、neutral(中性)",
    "USD_SAFE": "美元安全资产影响方向：positive(美元走强)、negative(美元走弱)、neutral(中性)"
  }},
  "severity": "事件严重程度评分，范围0-1，例如：0.76"
}}

请确保输出是有效的JSON格式，不要包含其他内容。
"""

    def analyze_event_impact(self, event_description: str, models: List[str] = None) -> Dict[str, Any]:
        """
        分析事件影响，使用多个模型并集成结果以降低单一模型偏差
        
        Args:
            event_description: 事件描述文本
            models: 使用的模型列表，如果未指定则使用初始化时的模型列表
            
        Returns:
            事件分析结果，集成多个模型的输出
        """
        if models is None:
            models = self.available_models
            
        results = []
        
        # 收集所有模型的结果
        for model in models:
            result = self._call_llm_model(model, event_description)
            if result:
                results.append(result)
        
        # 集成多个模型的结果
        if results:
            integrated_result = self._ensemble_results(results)
            return integrated_result
        else:
            # 如果所有模型都失败，使用模拟分析结果
            print("警告: 所有模型调用失败，使用模拟分析结果")
            return self._simulate_analysis(event_description)

    def _simulate_analysis(self, event_description: str) -> Dict[str, Any]:
        """
        当模型调用失败时，使用模拟分析结果
        
        Args:
            event_description: 事件描述文本
            
        Returns:
            模拟的分析结果
        """
        # 基于事件描述中的关键词进行简单分析
        event_description = event_description.lower()
        
        # 简单的关键词匹配逻辑
        if "战争" in event_description or "冲突" in event_description:
            event_type = "地缘政治"
            severity = 0.8
        elif "加息" in event_description or "利率" in event_description:
            event_type = "货币政策"
            severity = 0.6
        elif "通胀" in event_description or "cpi" in event_description:
            event_type = "经济数据"
            severity = 0.5
        else:
            event_type = "一般事件"
            severity = 0.3
            
        # 基于事件类型设置因子方向
        factor_directions = {
            "OIL": "neutral",
            "RISK": "neutral",
            "USD_SAFE": "neutral"
        }
        
        if event_type == "地缘政治":
            factor_directions["OIL"] = "positive"  # 战争通常推高油价
            factor_directions["RISK"] = "negative"  # 风险规避增加
            factor_directions["USD_SAFE"] = "positive"  # 美元作为避险资产
        elif event_type == "货币政策":
            factor_directions["RISK"] = "negative"  # 加息通常导致风险规避
            factor_directions["USD_SAFE"] = "positive"  # 美元走强
        elif event_type == "经济数据":
            factor_directions["RISK"] = "negative"  # 高通胀导致风险规避
            
        return {
            "event_type": event_type,
            "factor_directions": factor_directions,
            "severity": severity
        }

    def _ensemble_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        集成多个模型的结果，通过平均值/多数投票等方式降低单一模型偏差
        
        Args:
            results: 多个模型的分析结果列表
            
        Returns:
            集成后的结果
        """
        if not results:
            return {}
        
        if len(results) == 1:
            return results[0]
        
        # 集成逻辑
        integrated = {}
        
        # 对event_type采用多数投票
        event_types = [r.get("event_type") for r in results if r.get("event_type")]
        if event_types:
            # 选择出现次数最多的event_type
            integrated["event_type"] = max(set(event_types), key=event_types.count)
        else:
            integrated["event_type"] = results[0].get("event_type", "")
        
        # 对factor_directions采用多数投票
        factor_keys = ["OIL", "RISK", "USD_SAFE"]
        integrated["factor_directions"] = {}
        for key in factor_keys:
            directions = [r.get("factor_directions", {}).get(key) for r in results 
                         if r.get("factor_directions", {}).get(key)]
            if directions:
                # 选择出现次数最多的direction
                integrated["factor_directions"][key] = max(set(directions), key=directions.count)
            else:
                integrated["factor_directions"][key] = results[0].get("factor_directions", {}).get(key, "neutral")
        
        # 对severity采用平均值
        severities = []
        for r in results:
            if r.get("severity") is not None:
                severity_val = r.get("severity")
                # 确保severity是数值类型
                if isinstance(severity_val, str):
                    try:
                        severity_val = float(severity_val)
                    except ValueError:
                        continue  # 跳过无效值
                severities.append(severity_val)
        
        if severities:
            integrated["severity"] = sum(severities) / len(severities)
        else:
            integrated["severity"] = results[0].get("severity", 0)
            # 确保默认severity也是数值类型
            if isinstance(integrated["severity"], str):
                try:
                    integrated["severity"] = float(integrated["severity"])
                except ValueError:
                    integrated["severity"] = 0
        
        return integrated

    def _call_llm_model(self, model: str, event_description: str) -> Dict[str, Any]:
        """
        调用大语言模型进行分析
        
        Args:
            model: 模型ID
            event_description: 事件描述
            
        Returns:
            模型分析结果
        """
        if not self.api_key:
            print("错误: ARK_API_KEY 环境变量未设置")
            return {}
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = self.event_classification_prompt.format(event_description=event_description)
        
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1
        }
        
        try:
            print(f"正在调用模型: {model}")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            print(f"模型 {model} 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                # 解析JSON内容
                return json.loads(content)
            else:
                print(f"模型 {model} 调用失败: {response.status_code} - {response.text}")
                return {}
                
        except requests.exceptions.Timeout:
            print(f"模型 {model} 调用超时")
            return {}
        except requests.exceptions.RequestException as e:
            print(f"调用模型 {model} 时网络错误: {str(e)}")
            return {}
        except json.JSONDecodeError as e:
            print(f"模型 {model} 返回结果解析失败: {str(e)}")
            return {}
        except Exception as e:
            print(f"调用模型 {model} 时出错: {str(e)}")
            return {}

    def calculate_portfolio_impact(self, portfolio_data: List[Dict[str, Any]], 
                                 event_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算事件对投资组合的影响
        
        Args:
            portfolio_data: 用户持仓数据
            event_analysis: 事件分析结果
            
        Returns:
            投资组合影响分析结果
        """
        # 计算投资组合的整体风险敞口
        total_value = 0
        for item in portfolio_data:
            benefit = item.get('benefit', 0)
            # 确保benefit是数值类型
            if isinstance(benefit, str):
                # 如果是字符串，尝试去除货币符号并转换为数值
                try:
                    # 去除美元符号和逗号
                    cleaned_benefit = benefit.replace('$', '').replace(',', '')
                    benefit = float(cleaned_benefit)
                except ValueError:
                    # 转换失败则使用默认值0
                    benefit = 0
            elif not isinstance(benefit, (int, float)):
                # 如果既不是字符串也不是数值，则使用默认值0
                benefit = 0
                
            total_value += benefit
        
        # 确定受影响最大的货币对
        factor_directions = event_analysis.get('factor_directions', {})
        affected_pairs = []
        
        for item in portfolio_data:
            currency = item.get('currency', '')
            
            # 确保beta是数值类型
            beta = item.get('beta', 0)
            if isinstance(beta, str):
                try:
                    beta = float(beta)
                except ValueError:
                    beta = 0
            elif not isinstance(beta, (int, float)):
                beta = 0
                
            # 确保volatility是数值类型
            volatility = item.get('dailyVolatility', 0)
            if isinstance(volatility, str):
                try:
                    volatility = float(volatility)
                except ValueError:
                    volatility = 0
            elif not isinstance(volatility, (int, float)):
                volatility = 0
            
            # 根据因子方向和持仓特性判断影响
            impact_score = 0
            impact_direction = "neutral"
            
            # 简化的逻辑：根据事件因子和货币对特性判断影响
            if 'USD' in currency and 'USD_SAFE' in factor_directions:
                direction = factor_directions['USD_SAFE']
                if direction == 'positive':
                    impact_score = beta * volatility
                    impact_direction = "看涨" if beta > 0 else "看跌"
                elif direction == 'negative':
                    impact_score = -beta * volatility
                    impact_direction = "看跌" if beta > 0 else "看涨"
            
            if 'OIL' in currency and 'OIL' in factor_directions:
                direction = factor_directions['OIL']
                if direction == 'positive':
                    impact_score = beta * volatility
                    impact_direction = "看涨" if beta > 0 else "看跌"
                elif direction == 'negative':
                    impact_score = -beta * volatility
                    impact_direction = "看跌" if beta > 0 else "看涨"
            
            affected_pairs.append({
                'currency': currency,
                'impact_score': impact_score,
                'impact_direction': impact_direction
            })
        
        # 找出影响最大的货币对
        if affected_pairs:
            most_affected = max(affected_pairs, key=lambda x: abs(x['impact_score']))
        else:
            most_affected = None
        
        # 计算预测的阿尔法值 (简化计算)
        severity = event_analysis.get('severity', 0)
        if isinstance(severity, str):
            try:
                severity = float(severity)
            except ValueError:
                severity = 0
        elif not isinstance(severity, (int, float)):
            severity = 0
        predicted_alpha_t = min(1.0, max(0.0, severity * 0.5))  # 简化映射到[0,1]
        
        return {
            'predicted_alpha_t': predicted_alpha_t,
            'most_affected_pair': most_affected,
            'affected_pairs': affected_pairs
        }

    def generate_hedging_recommendations(self, portfolio_data: List[Dict[str, Any]], 
                                       event_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成对冲建议
        
        Args:
            portfolio_data: 用户持仓数据
            event_analysis: 事件分析结果
            
        Returns:
            对冲建议列表
        """
        recommendations = []
        factor_directions = event_analysis.get('factor_directions', {})
        severity = event_analysis.get('severity', 0)
        
        # 确保severity是数值类型
        severity = float(self._ensure_numeric(severity))
        
        # 基于风险因子方向和严重程度生成对冲建议
        if factor_directions.get('RISK') == 'negative':
            # 风险规避增加，建议增持避险资产
            hedging_ratio = min(1.0, severity * 0.8)
            recommendations.append({
                'action': '增加避险资产仓位',
                'instrument': 'USD/JPY 或 Gold',
                'hedging_ratio': f"{hedging_ratio*100:.1f}%",
                'reason': '事件导致风险规避情绪上升'
            })
        
        if factor_directions.get('USD_SAFE') == 'positive':
            # 美元走强，建议做多美元相关资产
            hedging_ratio = min(1.0, severity * 0.6)
            recommendations.append({
                'action': '增加美元多头仓位',
                'instrument': 'EUR/USD 空头 或 USD/CHF 多头',
                'hedging_ratio': f"{hedging_ratio*100:.1f}%",
                'reason': '事件导致美元作为安全资产需求增加'
            })
        
        if factor_directions.get('OIL') == 'positive':
            # 石油价格上涨，建议做多石油相关资产
            hedging_ratio = min(1.0, severity * 0.5)
            recommendations.append({
                'action': '增加能源板块仓位',
                'instrument': 'WTI Crude Oil 或 Energy Stocks',
                'hedging_ratio': f"{hedging_ratio*100:.1f}%",
                'reason': '事件可能导致石油供应紧张，价格上涨'
            })
        elif factor_directions.get('OIL') == 'negative':
            # 石油价格下跌，建议做空石油相关资产
            hedging_ratio = min(1.0, severity * 0.5)
            recommendations.append({
                'action': '增加石油空头仓位',
                'instrument': 'WTI Crude Oil 或 Energy Stocks',
                'hedging_ratio': f"{hedging_ratio*100:.1f}%",
                'reason': '事件可能导致石油需求下降，价格下跌'
            })
        
        # 确保所有数值字段为数值类型
        for recommendation in recommendations:
            for key, value in recommendation.items():
                if key in ['hedging_ratio']:
                    recommendation[key] = self._ensure_numeric(value)
        
        return recommendations

    def _ensure_numeric(self, value: Any) -> float:
        """
        确保值为数值类型
        
        Args:
            value: 需要转换为数值类型的值
            
        Returns:
            float: 转换后的数值
        """
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value.replace('%', '').replace(',', ''))
            except ValueError:
                return 0.0
        else:
            return 0.0
    
    def analyze(self, portfolio_data: List[Dict[str, Any]], event_description: str) -> Dict[str, Any]:
        """
        完整的压力情景分析
        
        Args:
            portfolio_data: 用户持仓数据
            event_description: 事件描述
            
        Returns:
            完整的分析结果
        """
        # 1. 分析事件影响
        event_analysis = self.analyze_event_impact(event_description)
        
        if not event_analysis:
            return {"error": "事件分析失败"}
        
        # 2. 计算投资组合影响
        portfolio_impact = self.calculate_portfolio_impact(portfolio_data, event_analysis)
        
        # 3. 生成对冲建议
        hedging_recommendations = self.generate_hedging_recommendations(portfolio_data, event_analysis)
        
        # 4. 组合结果
        result = {
            "event_analysis": event_analysis,
            "portfolio_impact": portfolio_impact,
            "hedging_recommendations": hedging_recommendations
        }
        
        return result


def main():
    """
    示例用法
    """
    # 示例持仓数据
    portfolio_data = [
        {
            "currency": "USD/JPY",
            "quantity": 10000,
            "proportion": 0.25,
            "benefit": 500,
            "dailyVolatility": 0.005,
            "valueAtRisk": "$250",
            "beta": 0.8,
            "hedgingCost": 50
        },
        {
            "currency": "EUR/USD",
            "quantity": 8000,
            "proportion": 0.20,
            "benefit": -200,
            "dailyVolatility": 0.007,
            "valueAtRisk": "$300",
            "beta": -0.6,
            "hedgingCost": 40
        },
        {
            "currency": "WTI",
            "quantity": 500,
            "proportion": 0.15,
            "benefit": 300,
            "dailyVolatility": 0.02,
            "valueAtRisk": "$150",
            "beta": 1.2,
            "hedgingCost": 30
        }
    ]
    
    # 示例事件
    event_description = "伊朗以色列发生战争，伊朗有意封锁霍尔木兹海峡"
    
    # 创建分析器实例
    analyzer = StressScenarioAnalyzer()
    
    # 执行分析
    try:
        result = analyzer.analyze(portfolio_data, event_description)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"分析过程中出错: {str(e)}")


if __name__ == "__main__":
    main()