#!/usr/bin/env python3
"""
Comprehensive API Test Script for Receipt Spending Analyzer
Tests all endpoints using the API server at http://192.168.100.186:5015
"""

import requests
import json
import time
import os

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_TOKEN = "test-user-api-demo"
TEST_IMAGE_PATH = "test.jpg"

# Global variables to store created resources
workspace_id = None
category_id = None
receipt_id = None

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test(test_name, method, endpoint):
    """Print test information"""
    print(f"\n🧪 Testing: {test_name}")
    print(f"   {method} {endpoint}")

def make_request(method, endpoint, data=None, files=None, params=None):
    """Make HTTP request with proper headers"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json" if not files else None
    }
    
    if files:
        headers.pop("Content-Type", None)  # Let requests set this for multipart
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            if files:
                response = requests.post(url, headers={k:v for k,v in headers.items() if k != "Content-Type"}, data=data, files=files)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"❌ Unsupported method: {method}")
            return None
            
        print(f"   Status: {response.status_code}")
        
        if response.status_code < 400:
            try:
                result = response.json()
                print(f"   ✅ Success: {json.dumps(result, indent=2)[:200]}...")
                return result
            except:
                print(f"   ✅ Success: {response.text[:200]}...")
                return response.text
        else:
            try:
                error = response.json()
                print(f"   ❌ Error: {error}")
            except:
                print(f"   ❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return None

def test_health_check():
    """Test health check endpoint"""
    print_section("HEALTH CHECK")
    
    print_test("Health Check", "GET", "/v1/health")
    return make_request("GET", "/v1/health")

def test_workspace_management():
    """Test workspace management endpoints"""
    global workspace_id
    print_section("WORKSPACE MANAGEMENT")
    
    # 1. Create workspace
    print_test("Create Workspace", "POST", "/v1/instances")
    result = make_request("POST", "/v1/instances", data={"name": "Test Workspace API Demo"})
    if result and "instance_id" in result:
        workspace_id = result["instance_id"]
        print(f"   📝 Workspace ID: {workspace_id}")
    
    # 2. List workspaces
    print_test("List Workspaces", "GET", "/v1/instances")
    make_request("GET", "/v1/instances")
    
    # 3. Get workspace details
    if workspace_id:
        print_test("Get Workspace Details", "GET", f"/v1/instances/{workspace_id}")
        make_request("GET", f"/v1/instances/{workspace_id}")
    
    # 4. Update workspace
    if workspace_id:
        print_test("Update Workspace", "PUT", f"/v1/instances/{workspace_id}")
        make_request("PUT", f"/v1/instances/{workspace_id}", data={"name": "Updated Test Workspace"})

def test_category_management():
    """Test category management endpoints"""
    global category_id
    print_section("CATEGORY MANAGEMENT")
    
    if not workspace_id:
        print("❌ Skipping category tests - no workspace ID")
        return
    
    # 1. Initialize categories
    print_test("Initialize Categories", "POST", f"/v1/instances/{workspace_id}/initialize")
    make_request("POST", f"/v1/instances/{workspace_id}/initialize", 
                data={"categories": "Food, Transportation, Entertainment, Shopping, Utilities"})
    
    # 2. Add single category
    print_test("Add Single Category", "POST", f"/v1/instances/{workspace_id}/categories")
    result = make_request("POST", f"/v1/instances/{workspace_id}/categories", 
                         data={"name": "Healthcare"})
    if result and "id" in result:
        category_id = result["id"]
        print(f"   📝 Category ID: {category_id}")

def test_receipt_processing():
    """Test receipt processing endpoints"""
    global receipt_id
    print_section("RECEIPT PROCESSING")
    
    if not workspace_id:
        print("❌ Skipping receipt tests - no workspace ID")
        return
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return
    
    # 1. Upload and parse receipt
    print_test("Upload & Parse Receipt", "POST", "/v1/reciepts")
    with open(TEST_IMAGE_PATH, 'rb') as f:
        files = {"reciept": f}
        data = {"instance_id": workspace_id}
        result = make_request("POST", "/v1/reciepts", data=data, files=files)
        if result and "receipt_id" in result:
            receipt_id = result["receipt_id"]
            print(f"   📝 Receipt ID: {receipt_id}")
    
    # 2. Get parsed receipt
    if receipt_id:
        print_test("Get Parsed Receipt", "GET", f"/v1/reciepts/{receipt_id}")
        make_request("GET", f"/v1/reciepts/{receipt_id}")
    
    # 3. Correct parsed receipt
    if receipt_id:
        print_test("Correct Parsed Receipt", "PATCH", f"/v1/reciepts/{receipt_id}")
        correction_data = {
            "instance_id": workspace_id,
            "fixes": [
                {
                    "line": 0,
                    "text": "Corrected Item Name",
                    "price": 15.99
                }
            ]
        }
        make_request("PATCH", f"/v1/reciepts/{receipt_id}", data=correction_data)

def test_transactions_and_budgets():
    """Test transactions and budget endpoints"""
    print_section("TRANSACTIONS & BUDGETS")
    
    if not workspace_id:
        print("❌ Skipping transaction tests - no workspace ID")
        return
    
    # 1. List transactions
    print_test("List Transactions", "GET", f"/v1/instances/{workspace_id}/transactions")
    make_request("GET", f"/v1/instances/{workspace_id}/transactions")
    
    # 2. Create/Update budget
    if category_id:
        print_test("Create/Update Budget", "POST", f"/v1/instances/{workspace_id}/budgets")
        make_request("POST", f"/v1/instances/{workspace_id}/budgets", 
                    data={"category_id": category_id, "limit": 500.0})
    
    # 3. Get budget utilization
    print_test("Get Budget Utilization", "GET", f"/v1/instances/{workspace_id}/budgets")
    make_request("GET", f"/v1/instances/{workspace_id}/budgets")

def test_reports_and_analytics():
    """Test reports and analytics endpoints"""
    print_section("REPORTS & ANALYTICS")
    
    if not workspace_id:
        print("❌ Skipping reports tests - no workspace ID")
        return
    
    # 1. Get reports
    print_test("Get Instance Reports", "GET", f"/v1/instances/{workspace_id}/reports")
    params = {"report_type": "summary", "start_date": "2024-01-01", "end_date": "2024-12-31"}
    make_request("GET", f"/v1/instances/{workspace_id}/reports", params=params)
    
    # 2. Get graphs - Pie chart
    print_test("Get Pie Chart Data", "GET", f"/v1/instances/{workspace_id}/graphs")
    make_request("GET", f"/v1/instances/{workspace_id}/graphs", params={"chart_type": "pie", "format": "json"})
    
    # 3. Get graphs - Bar chart
    print_test("Get Bar Chart Data", "GET", f"/v1/instances/{workspace_id}/graphs")
    make_request("GET", f"/v1/instances/{workspace_id}/graphs", params={"chart_type": "bar", "format": "json"})
    
    # 4. Get graphs - Line chart
    print_test("Get Line Chart Data", "GET", f"/v1/instances/{workspace_id}/graphs")
    make_request("GET", f"/v1/instances/{workspace_id}/graphs", params={"chart_type": "line", "format": "json"})

def test_ai_insights():
    """Test AI insights and advice endpoints"""
    print_section("AI INSIGHTS & ADVICE")
    
    if not workspace_id:
        print("❌ Skipping AI tests - no workspace ID")
        return
    
    # 1. Generate advice
    print_test("Generate Financial Advice", "POST", f"/v1/instances/{workspace_id}/advice")
    make_request("POST", f"/v1/instances/{workspace_id}/advice", 
                data={"focus": "reduce spending on food"})
    
    # 2. Chat with AI
    print_test("Chat with AI Assistant", "POST", f"/v1/instances/{workspace_id}/chat")
    make_request("POST", f"/v1/instances/{workspace_id}/chat", 
                data={"message": "What are my top spending categories?"})
    
    # # 3. Get insights (if endpoint exists)
    # print_test("Get Predictive Insights", "GET", f"/v1/instances/{workspace_id}/insights")
    # params = {"insight_type": "spending_forecast", "timeframe": "next_month"}
    # make_request("GET", f"/v1/instances/{workspace_id}/insights", params=params)

def test_cors():
    """Test CORS support"""
    print_section("CORS TESTING")
    
    print_test("CORS Test Endpoint", "GET", "/v1/cors-test")
    make_request("GET", "/v1/cors-test")

def cleanup():
    """Clean up created resources"""
    print_section("CLEANUP")
    
    if workspace_id:
        print_test("Delete Test Workspace", "DELETE", f"/v1/instances/{workspace_id}")
        make_request("DELETE", f"/v1/instances/{workspace_id}")

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive API testing...")
    print(f"🌐 Server: {BASE_URL}")
    print(f"🔑 Token: {TEST_TOKEN}")
    print(f"🖼️  Test Image: {TEST_IMAGE_PATH}")
    
    try:
        # Run all test suites
        # test_health_check()
        # test_cors()
        test_workspace_management()
        test_category_management()
        test_receipt_processing()
        test_transactions_and_budgets()
        test_reports_and_analytics()
        test_ai_insights()
        
        # Cleanup
        cleanup()
        
        print_section("TEST COMPLETED")
        print("✅ All tests completed!")
        print(f"📊 Workspace ID used: {workspace_id}")
        print(f"📊 Category ID used: {category_id}")
        print(f"📊 Receipt ID used: {receipt_id}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        if workspace_id:
            print("🧹 Cleaning up...")
            cleanup()
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        if workspace_id:
            print("🧹 Cleaning up...")
            cleanup()

if __name__ == "__main__":
    main()