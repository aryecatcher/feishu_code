---
title: Pipeline 模块
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
code_clipboard: true
highlight_theme: darkula
headingLevel: 2
generator: "@tarslib/widdershins v4.0.30"

---

# Pipeline 模块

Base URLs:

# Authentication

# pipelines

## GET 获取流水线详情

GET /api/v1/pipelines/{pipeline_id}

获取流水线模板详情信息。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|pipeline_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{
  "pipeline_id": 0,
  "descriptions": {
    "title": "string",
    "content": "string"
  },
  "stages": [
    0
  ],
  "config": {}
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|[PipelineConfig](#schemapipelineconfig)|

## PUT 更新流水线定义

PUT /api/v1/pipelines/{pipeline_id}

更新流水线模板信息。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|pipeline_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 创建并运行流水线实例

POST /api/v1/pipelines/{pipeline_id}/run

基于定义创建并运行流水线实例，返回运行实例ID。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|pipeline_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{
  "pipeline_id": 0,
  "run_id": 0,
  "summary": {
    "status": "string",
    "current_stage": "string"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|[RunSummary](#schemarunsummary)|

# runs

## GET 获取实例详情

GET /api/runs/{run_id}

获取实例运行摘要信息

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |唯一实例ID|

> 返回示例

> 200 Response

```json
{
  "pipeline_id": 0,
  "run_id": 0,
  "summary": {
    "status": "string",
    "current_stage": "string"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|[RunSummary](#schemarunsummary)|

## POST 暂停执行

POST /api/runs/{run_id}/pause

暂停实例执行

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 恢复执行

POST /api/runs/{run_id}/resume

恢复暂停的实例执行

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 强制终止

POST /api/runs/{run_id}/terminate

强制停止进行中的实例执行

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# runs/checkpoints

## GET 获取检查点列表

GET /api/runs/{run_id}/checkpoints

获取检查点的概述信息

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{
  "run_id": 0,
  "checkpoint_id": 0,
  "reviews": "string",
  "resolution": {
    "action": "string",
    "context_id": 0
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|[Checkpoint](#schemacheckpoint)|

## GET 获取检查点详情

GET /api/runs/{run_id}/{stage_id}

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |none|
|stage_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 通过检查点

POST /api/runs/{run_id}/{stage_id}/approve

通过该检查点

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |none|
|stage_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 驳回检查点

POST /api/runs/{run_id}/{stage_id}/reject

驳回该检查点

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|run_id|path|string| 是 |none|
|stage_id|path|string| 是 |none|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# 数据模型

<h2 id="tocS_PipelineConfig">PipelineConfig</h2>

<a id="schemapipelineconfig"></a>
<a id="schema_PipelineConfig"></a>
<a id="tocSpipelineconfig"></a>
<a id="tocspipelineconfig"></a>

```json
{
  "pipeline_id": 0,
  "descriptions": {
    "title": "string",
    "content": "string"
  },
  "stages": [
    0
  ],
  "config": {}
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|pipeline_id|integer|true|none|流水线编号|用于绑定模板，可采用默认值|
|descriptions|object|true|none|流水线描述|文字描述该模板|
|» title|string|true|none|标题|none|
|» content|string|false|none|详情|none|
|stages|[integer]|true|none|流水线阶段配置|连接各阶段StageID|
|config|object|false|none|额外配置|none|

<h2 id="tocS_StageConfig">StageConfig</h2>

<a id="schemastageconfig"></a>
<a id="schema_StageConfig"></a>
<a id="tocSstageconfig"></a>
<a id="tocsstageconfig"></a>

```json
{
  "stage_id": 0,
  "descriptions": {
    "title": "string",
    "content": "string"
  },
  "agent_config": {
    "model_provider": {},
    "roles": {}
  }
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|stage_id|integer|true|none|阶段编号|none|
|descriptions|object|true|none|阶段描述|简要描述阶段内容|
|» title|string|true|none|标题|none|
|» content|string|false|none|详情|none|
|agent_config|object|true|none|Agent配置|配置该阶段Agent信息|
|» model_provider|object|true|none|模型提供商|提供大模型接入|
|» roles|object|true|none|模型配置|配置预定信息|

<h2 id="tocS_RunSummary">RunSummary</h2>

<a id="schemarunsummary"></a>
<a id="schema_RunSummary"></a>
<a id="tocSrunsummary"></a>
<a id="tocsrunsummary"></a>

```json
{
  "pipeline_id": 0,
  "run_id": 0,
  "summary": {
    "status": "string",
    "current_stage": "string"
  }
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|pipeline_id|integer|true|none|流水线模板编号|连接流水线模板|
|run_id|integer|true|none|实例编号|标注实例|
|summary|object|true|none|运行概况|none|
|» status|string|true|none|运行状态|running|paused|awaiting_checkpoint|completed|failed|cancelled|
|» current_stage|string|true|none|当前阶段编号|连接stage_id|

<h2 id="tocS_Checkpoint">Checkpoint</h2>

<a id="schemacheckpoint"></a>
<a id="schema_Checkpoint"></a>
<a id="tocScheckpoint"></a>
<a id="tocscheckpoint"></a>

```json
{
  "run_id": 0,
  "checkpoint_id": 0,
  "reviews": "string",
  "resolution": {
    "action": "string",
    "context_id": 0
  }
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|run_id|integer|true|none|实例编号|连接运行实例|
|checkpoint_id|integer|true|none|检查点编号|标注检查点|
|reviews|string|true|none|检查点说明|呈现检查点内容|
|resolution|object|true|none|用户决策|none|
|» action|string|true|none|决策|accept|reject|
|» context_id|integer|true|none||反馈内容编号|

<h2 id="tocS_Context">Context</h2>

<a id="schemacontext"></a>
<a id="schema_Context"></a>
<a id="tocScontext"></a>
<a id="tocscontext"></a>

```json
{
  "run_id": 0,
  "context_id": 0,
  "type": "string",
  "content": {
    "prompt": "string",
    "refs": {
      "codebase": {},
      "dom": {}
    }
  }
}

```

### 属性

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|run_id|integer|true|none|实例编号|绑定运行实例|
|context_id|integer|true|none|交付内容编号|标注交付内容|
|type|string|true|none|交付类型|initial|checkpoint|
|content|object|true|none|交付内容|具体交付内容|
|» prompt|string|false|none|用户提示词|可选，提示词内容|
|» refs|object|false|none|上下文定位|可选，上下文内容|
|»» codebase|object|false|none|代码库定位|none|
|»» dom|object|false|none|网页元素定位|none|

