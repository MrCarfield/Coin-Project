import os
import requests
import json

def test_api_connection():
    """
    测试API连接和模型可用性
    """
    api_key = os.environ.get('ARK_API_KEY')
    if not api_key:
        print("错误: 未设置 ARK_API_KEY 环境变量")
        return False
    
    base_url = 'https://ark.cn-beijing.volces.com/api/v3'
    
    # 测试模型列表
    print("正在获取可用模型列表...")
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        print(f"获取模型列表状态码: {response.status_code}")
        
        if response.status_code == 200:
            models_data = response.json()
            print("可用模型列表:")
            print(json.dumps(models_data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"获取模型列表失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"测试模型列表时出错: {str(e)}")
        return False

def test_model_call(model_name):
    """
    测试特定模型调用
    """
    api_key = os.environ.get('ARK_API_KEY')
    if not api_key:
        print("错误: 未设置 ARK_API_KEY 环境变量")
        return False
    
    base_url = 'https://ark.cn-beijing.volces.com/api/v3'
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    test_prompt = "请用一句话回答：你好世界"
    
    data = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "temperature": 0.7
    }
    
    print(f"正在测试模型 {model_name}...")
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"模型 {model_name} 调用状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"模型 {model_name} 调用成功:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"模型 {model_name} 调用失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"调用模型 {model_name} 时出错: {str(e)}")
        return False

def main():
    """
    主函数
    """
    print("=== API诊断工具 ===")
    
    # 测试API连接
    if not test_api_connection():
        print("API连接测试失败")
        return
    
    # 测试指定的模型
    models_to_test = [
        'ep-20250824194947-wrm8q',  # 第一个大模型接入点
        'ep-20250824195709-jdklb'   # 第二个大模型接入点
    ]
    
    print("\n=== 模型调用测试 ===")
    for model in models_to_test:
        print()
        test_model_call(model)
        print("-" * 50)

if __name__ == "__main__":
    main()