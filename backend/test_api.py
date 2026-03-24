import urllib.request
import json

print("=== 测试创建会话 ===")
url = "http://127.0.0.1:8000/api/v1/sessions"
data = {
    "trigger_type": "manual",
    "trigger_source": "user",
    "title": "测试会话2"
}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"✓ 创建会话成功")
        print(f"  ID: {result['id']}")
        print(f"  标题: {result['title']}")
        print(f"  状态: {result['status']}")
        print(f"  消息数: {result['message_count']}")
except Exception as e:
    print(f"✗ 创建会话失败: {e}")

print("\n=== 测试获取会话列表 ===")
try:
    req = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"✓ 获取会话列表成功")
        print(f"  会话数量: {len(result)}")
        for session in result:
            print(f"  - {session['title']} ({session['status']})")
except Exception as e:
    print(f"✗ 获取会话列表失败: {e}")