# 金融数据分析工具

## 项目概述

本项目是一个基于Python的金融数据分析工具，可以从多个数据源获取金融数据并进行基础分析。工具支持多种金融工具（股票、加密货币、指数、外汇等）的数据获取和分析。

## 功能特性

1. 使用Alpha Vantage API获取过去三个月的交易数据
2. 数据导出到Excel文件
3. 计算多种金融指标：
   - 持仓占比
   - 盈亏
   - 日波动率
   - 在险价值(Value at Risk)
   - 贝塔系数

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 预配置API密钥运行

```bash
python run_with_api_key.py
```

程序会提示您输入金融工具代码、持仓量和买入价格，然后自动获取数据并计算各项指标。

### 2. 多股票分析

```bash
python multi_stock_analyzer.py
```

可以分析多个股票，程序会计算每个股票的指标并汇总所有股票的持仓占比。

## 代码结构

### financial_data_analyzer_alpha_vantage.py

这是主要的分析器类文件，包含以下主要方法：

- `get_past_three_months_data(symbol, max_retries)`: 获取过去三个月的交易数据，支持重试机制
- `export_to_excel(data, symbol, filename)`: 将数据导出到Excel文件
- `calculate_position_ratio(data, position_size, total_assets)`: 计算持仓占比
- `calculate_pnl(data, position_size, buy_price)`: 计算盈亏
- `calculate_daily_volatility(data)`: 计算日波动率（使用最近30个交易日的数据）
- `calculate_value_at_risk(data, confidence_level)`: 计算在险价值
- `calculate_beta(data, market_symbol)`: 计算贝塔系数

### run_with_api_key.py

这是一个使用预配置API密钥的示例程序，演示如何使用AlphaVantageFinancialDataAnalyzer类。

程序会自动从环境变量`ALPHA_VANTAGE_API_KEY`中读取API密钥，如果没有设置则使用demo密钥。

### multi_stock_analyzer.py

这是一个多股票分析工具，可以分析多个股票并计算它们在投资组合中的占比。

程序会提示用户输入多个股票的信息，然后计算每个股票的指标，并确保所有股票的持仓占比总和为100%。

## API密钥配置

项目使用Alpha Vantage API获取金融数据。您可以通过以下方式配置API密钥：

1. 设置环境变量`ALPHA_VANTAGE_API_KEY`
2. 在代码中直接指定API密钥

获取免费API密钥：https://www.alphavantage.co/support/#api-key

## 注意事项

1. Alpha Vantage免费版API限制：
   - 每分钟最多5次请求
   - 每天最多500次请求
2. 程序内置了重试机制，遇到API限制时会自动等待并重试
3. 如果使用demo密钥，功能会受到限制
4. 程序会自动获取过去三个月的数据并导出到Excel文件，同时计算各种金融指标
