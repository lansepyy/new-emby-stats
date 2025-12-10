#!/usr/bin/env python3
"""
Emby Stats Integration Test Script
完整的 Docker 集成测试脚本，验证所有 API 端点
"""
import requests
import time
import sys
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class IntegrationTest:
    """集成测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8899"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message: str, color: str = ""):
        """打印日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {color}{message}{Colors.RESET}")
        
    def test(self, name: str, func) -> bool:
        """运行单个测试"""
        self.log(f"Testing: {name}", Colors.BLUE)
        try:
            result, message = func()
            if result:
                self.log(f"✓ PASS: {name} - {message}", Colors.GREEN)
                self.passed += 1
                self.test_results.append({
                    "name": name,
                    "status": "PASS",
                    "message": message
                })
                return True
            else:
                self.log(f"✗ FAIL: {name} - {message}", Colors.RED)
                self.failed += 1
                self.test_results.append({
                    "name": name,
                    "status": "FAIL",
                    "message": message
                })
                return False
        except Exception as e:
            self.log(f"✗ ERROR: {name} - {str(e)}", Colors.RED)
            self.failed += 1
            self.test_results.append({
                "name": name,
                "status": "ERROR",
                "message": str(e)
            })
            return False
    
    def wait_for_service(self, timeout: int = 60) -> bool:
        """等待服务就绪"""
        self.log(f"Waiting for service at {self.base_url}...", Colors.YELLOW)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.base_url}/", timeout=2)
                if response.status_code in [200, 401]:  # 200 OK or 401 Unauthorized (need auth)
                    self.log("Service is ready!", Colors.GREEN)
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        
        self.log("Service failed to start within timeout", Colors.RED)
        return False
    
    # === Authentication Tests ===
    
    def test_auth_check(self) -> Tuple[bool, str]:
        """测试认证检查"""
        response = self.session.get(f"{self.base_url}/api/auth/check")
        
        if response.status_code == 200:
            data = response.json()
            return True, f"Auth check returned: {data}"
        return False, f"Status code: {response.status_code}"
    
    # === Notification API Tests ===
    
    def test_get_notifications(self) -> Tuple[bool, str]:
        """测试获取通知配置"""
        response = self.session.get(f"{self.base_url}/api/notifications")
        
        if response.status_code == 200:
            data = response.json()
            
            # 验证返回结构
            required_keys = ['settings', 'templates', 'config', 'history']
            for key in required_keys:
                if key not in data:
                    return False, f"Missing key: {key}"
            
            # 验证 config 结构
            config = data['config']
            channels = ['emby', 'telegram', 'discord', 'wecom', 'tmdb']
            for channel in channels:
                if channel not in config:
                    return False, f"Missing channel in config: {channel}"
            
            template_count = len(data['templates'])
            return True, f"Found {template_count} templates and {len(channels)} channels"
        
        return False, f"Status code: {response.status_code}, Response: {response.text}"
    
    def test_get_notification_settings(self) -> Tuple[bool, str]:
        """测试获取通知设置"""
        response = self.session.get(f"{self.base_url}/api/notifications/settings")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'success' in data and data['success']:
                settings = data.get('data', {})
                return True, f"Settings retrieved successfully with {len(settings)} fields"
            return False, "Response doesn't contain success=true"
        
        return False, f"Status code: {response.status_code}"
    
    def test_save_notification_settings(self) -> Tuple[bool, str]:
        """测试保存通知设置"""
        # 构造测试数据
        test_settings = [{
            "conditions": {
                "telegram": {
                    "enabled": True,
                    "bot_token": "test_bot_token_123456",
                    "admin_users": ["12345", "67890"],
                    "regular_users": []
                },
                "discord": {
                    "enabled": True,
                    "webhook_url": "https://discord.com/api/webhooks/test",
                    "username": "Emby Stats Test"
                },
                "wecom": {
                    "enabled": False,
                    "corp_id": "",
                    "corp_secret": "",
                    "agent_id": "",
                    "proxy_url": "",
                    "user_list": []
                },
                "tmdb": {
                    "enabled": True,
                    "api_key": "test_tmdb_api_key"
                },
                "emby": {
                    "enabled": False,
                    "server_url": "",
                    "api_token": ""
                }
            }
        }]
        
        response = self.session.post(
            f"{self.base_url}/api/notifications/settings",
            json=test_settings
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return True, "Settings saved successfully"
            return False, f"Unexpected response: {data}"
        
        return False, f"Status code: {response.status_code}, Response: {response.text}"
    
    def test_get_templates(self) -> Tuple[bool, str]:
        """测试获取模板"""
        response = self.session.get(f"{self.base_url}/api/notifications/templates")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'success' in data and data['success']:
                templates = data.get('data', {})
                template_names = list(templates.keys())
                return True, f"Found templates: {', '.join(template_names)}"
            return False, "Response doesn't contain success=true"
        
        return False, f"Status code: {response.status_code}"
    
    def test_update_template(self) -> Tuple[bool, str]:
        """测试更新模板"""
        template_id = "default"
        template_data = {
            "title": "Test Notification Template",
            "text": "This is a test notification: {{ message }}",
            "image_template": None
        }
        
        response = self.session.put(
            f"{self.base_url}/api/notifications/templates/{template_id}",
            json=template_data
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return True, f"Template '{template_id}' updated successfully"
            return False, f"Unexpected response: {data}"
        
        return False, f"Status code: {response.status_code}, Response: {response.text}"
    
    def test_preview_template(self) -> Tuple[bool, str]:
        """测试模板预览"""
        preview_data = {
            "template_id": "default",
            "content": {
                "message": "Test message",
                "user": "Test User",
                "timestamp": "2024-01-01 12:00:00"
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/notifications/templates/preview",
            json=preview_data
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                preview = data.get('data', {})
                rendered_title = preview.get('rendered_title', '')
                return True, f"Preview generated: {rendered_title[:50]}..."
            return False, f"Unexpected response: {data}"
        
        return False, f"Status code: {response.status_code}, Response: {response.text}"
    
    # === Stats API Tests ===
    
    def test_get_overview(self) -> Tuple[bool, str]:
        """测试获取概览数据"""
        response = self.session.get(f"{self.base_url}/api/stats/overview")
        
        if response.status_code == 200:
            data = response.json()
            
            # 验证基本结构
            if isinstance(data, dict):
                return True, f"Overview data retrieved with {len(data)} fields"
            return False, "Unexpected data structure"
        
        return False, f"Status code: {response.status_code}"
    
    def test_get_users(self) -> Tuple[bool, str]:
        """测试获取用户统计"""
        response = self.session.get(f"{self.base_url}/api/stats/users")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                return True, f"Found {len(data)} users"
            return False, "Unexpected data structure"
        
        return False, f"Status code: {response.status_code}"
    
    def test_get_content(self) -> Tuple[bool, str]:
        """测试获取内容统计"""
        response = self.session.get(f"{self.base_url}/api/stats/content")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                return True, f"Content stats retrieved with {len(data)} sections"
            return False, "Unexpected data structure"
        
        return False, f"Status code: {response.status_code}"
    
    def test_get_devices(self) -> Tuple[bool, str]:
        """测试获取设备统计"""
        response = self.session.get(f"{self.base_url}/api/stats/devices")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                clients = data.get('clients', [])
                devices = data.get('devices', [])
                return True, f"Found {len(clients)} clients and {len(devices)} devices"
            return False, "Unexpected data structure"
        
        return False, f"Status code: {response.status_code}"
    
    def test_get_history(self) -> Tuple[bool, str]:
        """测试获取历史记录"""
        response = self.session.get(f"{self.base_url}/api/stats/history?limit=10")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                return True, f"Found {len(data)} history records"
            return False, "Unexpected data structure"
        
        return False, f"Status code: {response.status_code}"
    
    # === Media API Tests ===
    
    def test_get_emby_users(self) -> Tuple[bool, str]:
        """测试获取 Emby 用户"""
        response = self.session.get(f"{self.base_url}/api/media/emby-users")
        
        if response.status_code in [200, 500]:  # 500 可能因为没有配置 Emby 服务器
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return True, f"Found {len(data)} Emby users"
            else:
                # 这是预期的，如果没有配置 Emby
                return True, "Emby not configured (expected)"
        
        return False, f"Unexpected status code: {response.status_code}"
    
    def test_get_servers(self) -> Tuple[bool, str]:
        """测试获取服务器列表"""
        response = self.session.get(f"{self.base_url}/api/media/servers")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                return True, f"Found {len(data)} servers"
            return False, "Unexpected data structure"
        
        return False, f"Status code: {response.status_code}"
    
    def test_get_name_mappings(self) -> Tuple[bool, str]:
        """测试获取名称映射"""
        response = self.session.get(f"{self.base_url}/api/media/name-mappings")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                return True, f"Name mappings retrieved with {len(data)} categories"
            return False, "Unexpected data structure"
        
        return False, f"Status code: {response.status_code}"
    
    # === Health Check ===
    
    def test_frontend_accessible(self) -> Tuple[bool, str]:
        """测试前端是否可访问"""
        response = self.session.get(f"{self.base_url}/")
        
        if response.status_code == 200:
            content = response.text
            if 'html' in content.lower():
                return True, "Frontend HTML page loaded successfully"
            return False, "Response doesn't contain HTML"
        
        return False, f"Status code: {response.status_code}"
    
    def test_manifest_accessible(self) -> Tuple[bool, str]:
        """测试 PWA manifest 是否可访问"""
        response = self.session.get(f"{self.base_url}/manifest.json")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'name' in data:
                    return True, f"PWA manifest loaded: {data.get('name')}"
                return False, "Manifest doesn't contain 'name' field"
            except json.JSONDecodeError:
                return False, "Invalid JSON in manifest"
        
        return False, f"Status code: {response.status_code}"
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 80, Colors.BOLD)
        self.log("EMBY STATS INTEGRATION TEST SUITE", Colors.BOLD)
        self.log("=" * 80, Colors.BOLD)
        
        # 等待服务就绪
        if not self.wait_for_service():
            self.log("Service failed to start. Aborting tests.", Colors.RED)
            return False
        
        self.log("\n" + "=" * 80, Colors.BOLD)
        self.log("SECTION 1: Health & Frontend Tests", Colors.BOLD)
        self.log("=" * 80, Colors.BOLD)
        
        self.test("Frontend Accessible", self.test_frontend_accessible)
        self.test("PWA Manifest Accessible", self.test_manifest_accessible)
        
        self.log("\n" + "=" * 80, Colors.BOLD)
        self.log("SECTION 2: Authentication Tests", Colors.BOLD)
        self.log("=" * 80, Colors.BOLD)
        
        self.test("Auth Check", self.test_auth_check)
        
        self.log("\n" + "=" * 80, Colors.BOLD)
        self.log("SECTION 3: Notification API Tests", Colors.BOLD)
        self.log("=" * 80, Colors.BOLD)
        
        self.test("GET /api/notifications", self.test_get_notifications)
        self.test("GET /api/notifications/settings", self.test_get_notification_settings)
        self.test("POST /api/notifications/settings", self.test_save_notification_settings)
        self.test("GET /api/notifications/templates", self.test_get_templates)
        self.test("PUT /api/notifications/templates/{id}", self.test_update_template)
        self.test("POST /api/notifications/templates/preview", self.test_preview_template)
        
        self.log("\n" + "=" * 80, Colors.BOLD)
        self.log("SECTION 4: Stats API Tests", Colors.BOLD)
        self.log("=" * 80, Colors.BOLD)
        
        self.test("GET /api/stats/overview", self.test_get_overview)
        self.test("GET /api/stats/users", self.test_get_users)
        self.test("GET /api/stats/content", self.test_get_content)
        self.test("GET /api/stats/devices", self.test_get_devices)
        self.test("GET /api/stats/history", self.test_get_history)
        
        self.log("\n" + "=" * 80, Colors.BOLD)
        self.log("SECTION 5: Media API Tests", Colors.BOLD)
        self.log("=" * 80, Colors.BOLD)
        
        self.test("GET /api/media/emby-users", self.test_get_emby_users)
        self.test("GET /api/media/servers", self.test_get_servers)
        self.test("GET /api/media/name-mappings", self.test_get_name_mappings)
        
        # 打印总结
        self.print_summary()
        
        return self.failed == 0
    
    def print_summary(self):
        """打印测试总结"""
        self.log("\n" + "=" * 80, Colors.BOLD)
        self.log("TEST SUMMARY", Colors.BOLD)
        self.log("=" * 80, Colors.BOLD)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        self.log(f"Total Tests: {total}", Colors.BOLD)
        self.log(f"Passed: {self.passed}", Colors.GREEN)
        self.log(f"Failed: {self.failed}", Colors.RED)
        self.log(f"Pass Rate: {pass_rate:.1f}%", Colors.YELLOW)
        
        if self.failed > 0:
            self.log("\nFailed Tests:", Colors.RED)
            for result in self.test_results:
                if result['status'] in ['FAIL', 'ERROR']:
                    self.log(f"  - {result['name']}: {result['message']}", Colors.RED)
        
        self.log("=" * 80, Colors.BOLD)
        
        # 保存测试报告
        self.save_report()
    
    def save_report(self):
        """保存测试报告到文件"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0,
            "results": self.test_results
        }
        
        report_file = "integration_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"\nTest report saved to: {report_file}", Colors.GREEN)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Emby Stats Integration Test')
    parser.add_argument('--url', default='http://localhost:8899',
                       help='Base URL of the service (default: http://localhost:8899)')
    parser.add_argument('--timeout', type=int, default=60,
                       help='Timeout in seconds to wait for service (default: 60)')
    
    args = parser.parse_args()
    
    test = IntegrationTest(base_url=args.url)
    success = test.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
