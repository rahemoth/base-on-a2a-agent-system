# Skill 导入规范

本文件定义了 Agent Skill 的导入格式规范，支持从 `.md` 文件导入自定义技能。

## 格式规范

### 基础结构

```markdown
---
skill_id: my_custom_skill
name: 我的自定义技能
description: 技能的简短描述
category: custom
tags:
  - tag1
  - tag2
---

## 系统提示词

这里是技能的详细系统提示词内容。
可以包含多行文本。
```

### 字段说明

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `skill_id` | 是 | 字符串 | 唯一标识符，只允许小写字母、数字、下划线 |
| `name` | 是 | 字符串 | 显示名称 |
| `description` | 是 | 字符串 | 技能功能描述 |
| `prompt` | 是 | 字符串 | 系统提示词内容 |
| `category` | 否 | 字符串 | 分类，默认为 `custom` |
| `tags` | 否 | 数组 | 标签列表 |
| `tools` | 否 | 数组 | 工具定义数组 |

### 高级格式：包含工具定义

```markdown
---
skill_id: data_analysis
name: 数据分析技能
description: 专业的数据分析技能
category: analysis
tags:
  - data
  - analysis
---

## 数据分析模式

你是一个数据分析专家。当用户提供数据时，请：
1. 识别数据类型、分布和特征
2. 计算关键统计指标
3. 发现数据中的趋势和异常
4. 提供可视化建议

## 工具定义

### calculate
执行数学计算

**参数:**
- `expression` (string): 数学表达式

### plot_chart
生成图表

**参数:**
- `chart_type` (string): 图表类型
- `data` (string): 数据内容
```

### 多技能文件

可以在一个文件中定义多个技能，使用 `---` 分隔：

```markdown
---
skill_id: skill_one
name: 技能一
description: 第一个技能
---

## 技能一提示词

第一个技能的提示词内容...

---
skill_id: skill_two
name: 技能二
description: 第二个技能
---

## 技能二提示词

第二个技能的提示词内容...
```

## 导入示例

### 方式一：通过 API 导入

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/skills/import-file', {
  method: 'POST',
  body: formData
});
```

### 方式二：通过 JSON API 导入

```json
{
  "id": "my_skill",
  "name": "我的技能",
  "description": "描述",
  "prompt": "提示词内容",
  "category": "custom",
  "tags": ["tag1", "tag2"]
}
```

## 注意事项

1. **唯一性**: `skill_id` 不能与内置技能冲突
2. **安全性**: 导入时会对内容进行基本校验
3. **持久化**: 自定义技能保存在 `data/custom_skills.json`
4. **生效**: 导入后需重启服务或刷新页面才能看到更新
