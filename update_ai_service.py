# 批量更新ai_service.py中的API调用
import re

with open('ai_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 更新check_settings方法
content = re.sub(
    r"(def check_settings.*?messages = \[.*?\])\s+result = self\._call_api\(messages, temperature=0\.3, max_tokens=1500\)",
    r"\1\n\n        result, usage = self._call_api(\n            messages,\n            temperature=0.3,\n            max_tokens=1500,\n            novel_id=novel_id,\n            operation='check_settings',\n            stage='check'\n        )",
    content,
    flags=re.DOTALL
)

# 更新generate_outline方法
content = re.sub(
    r"(def generate_outline.*?messages = \[.*?\])\s+result = self\._call_api\(messages, temperature=0\.7, max_tokens=4000\)",
    r"\1\n\n        result, usage = self._call_api(\n            messages,\n            temperature=0.7,\n            max_tokens=4000,\n            novel_id=novel_id,\n            operation='generate_outline',\n            stage='outline'\n        )",
    content,
    flags=re.DOTALL
)

# 保存更新后的文件
with open('ai_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ ai_service.py 已更新")
