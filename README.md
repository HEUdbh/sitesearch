# SiteSearch 项目

一个集成 OneForAll 域名收集工具的综合站点搜索与分析平台。

## 项目简介

SiteSearch 是一个专为安全研究人员、渗透测试人员和网络管理员设计的综合工具平台，主要功能包括：

- 基于 OneForAll 的高效子域名收集
- 站点信息在线展示与管理
- RESTful API 接口支持
- 任务管理与执行结果持久化存储
- 现代化的前端界面
- 实时任务进度监控
- 结果文件在线查看

## 项目结构

```
sitesearch/
├── OneForAll/          # OneForAll 子域名收集工具
├── siteback/           # 后端服务 (Flask)
│   ├── app/            # 应用主程序
│   │   └── main.py     # Flask 应用入口
│   └── model/          # 核心代码模块
│       ├── database.py # 数据库操作
│       ├── handleofa.py # OneForAll 任务处理
│       └── result.py   # 结果文件处理
└── sitevue/            # 前端 Vue 项目
    ├── src/
    │   ├── views/      # 页面组件
    │   │   └── Task.vue # 任务管理页面
    │   └── routes/     # 路由配置
    └── package.json    # 项目配置
```

### OneForAll

强大的子域名收集工具，提供多种子域名收集方式，包括但不限于：

- 证书透明度日志
- 搜索引擎
- DNS 记录
- 域名爆破
- 爬取

### siteback

后端服务，基于 Python Flask 开发，主要功能：

- 提供 RESTful API 接口
- 管理 OneForAll 任务的执行
- SQLite 数据库存储与查询
- 任务状态监控
- 结果文件读取与处理
- 实时进度跟踪

### sitevue

基于 Vue.js 的现代化前端界面，提供：

- 用户友好的交互界面
- 任务创建与管理
- 结果可视化展示
- 实时状态更新
- 进度条显示
- 结果文件在线查看

## 技术栈

### 后端

- Python 3.7+
- Flask 2.3.3
- SQLite 数据库
- pandas (结果文件处理)

### 前端

- Vue.js 3
- TypeScript
- Vite 构建工具

### 核心工具

- OneForAll 子域名收集

## 安装部署

### 环境要求

- Python 3.7+
- Node.js 14+
- SQLite 3 (内置，无需额外安装)

### 安装步骤

#### 1. 克隆项目

```bash
git clone [仓库地址]
cd sitesearch
```

#### 2. 后端安装

```bash
cd siteback
# 安装依赖
pip install -r requirements.txt
# 启动服务
python -m app.main
```

服务将在 http://127.0.0.1:5000 启动

#### 3. 前端安装

```bash
cd ../sitevue
# 安装依赖
npm install
# 开发模式运行
npm run dev
# 或构建生产版本
npm run build
```

前端将在 http://localhost:5173 启动

## 使用说明

### API 接口

#### 创建扫描任务

- **接口**: `/api/task`
- **方法**: `POST`
- **参数**:
  - `target`: 目标域名 (必需)
  - `module`: 执行模块 (可选，默认: all)
- **返回**: 任务 ID 和状态

#### 获取任务列表

- **接口**: `/api/task`
- **方法**: `GET`
- **返回**: 所有任务列表 (包含任务ID、目标域名、状态、扫描参数等)

#### 获取单个任务详情

- **接口**: `/api/task/<task_id>`
- **方法**: `GET`
- **返回**: 指定任务的详细信息

#### 获取任务结果

- **接口**: `/api/result`
- **方法**: `GET`
- **参数**:
  - `taskid`: 任务ID (必需)
- **返回**: 任务扫描结果数据 (支持CSV/JSON/TXT格式)

#### 获取任务摘要

- **接口**: `/api/result/summary`
- **方法**: `GET`
- **参数**:
  - `taskid`: 任务ID (必需)
- **返回**: 结果文件摘要信息 (文件大小、记录数等)

### 数据库设计

系统使用 SQLite 数据库，主要表结构：

#### task_info 表

- 存储任务基本信息
- 包含任务ID、目标域名、状态、扫描参数、开始时间、结束时间、结果文件路径等

## 主要功能模块

### 数据库管理
- SQLite 数据库操作
- 线程安全的数据库连接
- 事务管理与错误处理
- 结果持久化存储

### 任务管理
- 异步任务执行
- 状态监控与进度跟踪
- 结果收集与处理

### OneForAll 集成
- 命令行参数解析
- 结果文件处理
- 输出格式转换 (CSV/JSON/TXT)

### 结果文件处理
- 多格式文件读取 (CSV/JSON/TXT)
- 自动格式检测
- 数据解析与格式化
- 文件摘要信息生成

## 注意事项

1. 首次使用会自动创建 SQLite 数据库文件
2. 大规模扫描可能需要较长时间，请耐心等待
3. 请遵守相关法律法规，仅在授权范围内使用本工具
4. 建议在测试环境中先进行小规模测试
5. 确保有足够的磁盘空间存储扫描结果文件

## 快速开始

1. 安装后端依赖：`pip install -r siteback/requirements.txt`
2. 启动后端服务：`python -m siteback.app.main`
3. 安装前端依赖：`cd sitevue && npm install`
4. 启动前端服务：`npm run dev`
5. 访问 http://localhost:5173 使用系统

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进本项目。

## 许可证

[在此添加许可证信息]

## 联系方式

如有问题或建议，请通过以下方式联系：

[在此添加联系方式]