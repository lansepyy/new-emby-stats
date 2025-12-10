#!/usr/bin/env python3
"""
Test script for notification templates API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/notifications"

def test_get_templates():
    """Test getting all templates"""
    try:
        response = requests.get(f"{BASE_URL}/templates")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Templates retrieved successfully:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def test_update_template():
    """Test updating a template"""
    try:
        template_data = {
            "title": "测试标题",
            "text": "测试内容 - {{ user_name }}",
            "image_template": "{{ item_image }}"
        }
        response = requests.put(f"{BASE_URL}/templates/playback", json=template_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Template updated successfully:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def test_preview_template():
    """Test template preview"""
    try:
        preview_data = {
            "template_id": "playback",
            "content": {
                "user_name": "test_user",
                "item_name": "Example Movie",
                "client": "Web Player",
                "device": "Chrome Browser",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
        response = requests.post(f"{BASE_URL}/templates/preview", json=preview_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Template preview generated successfully:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Notification Templates API")
    print("=" * 50)
    
    print("\n1. Testing get templates...")
    test_get_templates()
    
    print("\n2. Testing update template...")
    test_update_template()
    
    print("\n3. Testing template preview...")
    test_preview_template()
    
    print("\n" + "=" * 50)
    print("API testing completed")