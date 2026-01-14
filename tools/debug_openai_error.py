#!/usr/bin/env python3
"""
Debug OpenAI API error details
"""
import requests
import json
import os
from datetime import datetime

def test_openai_directly():
    """Test OpenAI API directly to get exact error details"""
    print("🔍 Testing OpenAI API directly...")
    
    # Get API key from .env
    api_key = None
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except Exception as e:
        print(f"❌ Could not read .env file: {e}")
        return
    
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ No valid OpenAI API key found in .env file")
        return
    
    print(f"✅ Found API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Test the API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    try:
        print("📡 Making request to OpenAI API...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers:")
        for key, value in response.headers.items():
            if 'rate' in key.lower() or 'limit' in key.lower() or 'retry' in key.lower():
                print(f"   {key}: {value}")
        
        if response.status_code == 429:
            print("🚨 CONFIRMED: Rate limit exceeded!")
            try:
                error_data = response.json()
                print(f"📄 Error Details:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"📄 Raw Error Response: {response.text}")
                
        elif response.status_code == 401:
            print("🔑 AUTHENTICATION ERROR: Invalid API key")
            try:
                error_data = response.json()
                print(f"📄 Error Details:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"📄 Raw Error Response: {response.text}")
                
        elif response.status_code == 200:
            print("✅ SUCCESS: OpenAI API is working!")
            try:
                data = response.json()
                message = data['choices'][0]['message']['content']
                print(f"🤖 Response: {message}")
            except:
                print("📄 Raw Response:", response.text[:200])
                
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def check_openai_account_info():
    """Check OpenAI account information"""
    print("\n🔍 Checking OpenAI account information...")
    
    # Get API key
    api_key = None
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except:
        print("❌ Could not read .env file")
        return
    
    if not api_key:
        print("❌ No API key found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Check account usage
    try:
        print("📊 Checking account usage...")
        response = requests.get(
            "https://api.openai.com/v1/usage",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Account usage endpoint accessible")
        else:
            print(f"⚠️ Usage endpoint returned: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Usage check failed: {e}")
    
    # Check models
    try:
        print("🤖 Checking available models...")
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Models endpoint accessible")
            data = response.json()
            model_count = len(data.get('data', []))
            print(f"📋 Available models: {model_count}")
        else:
            print(f"⚠️ Models endpoint returned: {response.status_code}")
            if response.status_code == 429:
                print("🚨 Rate limited on models endpoint too!")
                
    except Exception as e:
        print(f"❌ Models check failed: {e}")

if __name__ == "__main__":
    print("🚀 DEBUGGING OPENAI API ISSUES")
    print("=" * 60)
    print(f"🕐 Time: {datetime.now()}")
    print("=" * 60)
    
    test_openai_directly()
    check_openai_account_info()
    
    print("\n" + "=" * 60)
    print("💡 WHAT TO CHECK ON OPENAI PLATFORM:")
    print("=" * 60)
    print("1. 🌐 Go to: https://platform.openai.com/usage")
    print("2. 📊 Check your current usage and limits")
    print("3. 💳 Go to: https://platform.openai.com/account/billing")
    print("4. 💰 Check if you have credits/payment method")
    print("5. 🔑 Go to: https://platform.openai.com/api-keys")
    print("6. ✅ Verify your API key is active")
    print("7. 📈 Check rate limits at: https://platform.openai.com/account/limits")
    print("\n🔍 Common Issues:")
    print("   - Free tier has very low rate limits")
    print("   - Need to add payment method for higher limits")
    print("   - API key might be invalid or expired")
    print("   - Account might be suspended")