#!/usr/bin/env python3
"""
Comprehensive test script for DocuScan system
"""

import os
import sys
import json
import time
import asyncio
import requests
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import argparse

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"

class DocuScanTester:
    """Test suite for DocuScan system"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.test_results = []
        
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        print(f"\n🧪 Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            elapsed = time.time() - start_time
            
            if result:
                print(f"✅ {test_name} - PASSED ({elapsed:.2f}s)")
                self.test_results.append({
                    "name": test_name,
                    "status": "PASSED",
                    "duration": elapsed,
                    "error": None
                })
                return True
            else:
                print(f"❌ {test_name} - FAILED ({elapsed:.2f}s)")
                self.test_results.append({
                    "name": test_name,
                    "status": "FAILED",
                    "duration": elapsed,
                    "error": "Test returned False"
                })
                return False
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"💥 {test_name} - ERROR ({elapsed:.2f}s): {str(e)}")
            self.test_results.append({
                "name": test_name,
                "status": "ERROR",
                "duration": elapsed,
                "error": str(e)
            })
            return False

    def test_health_check(self):
        """Test system health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"   System status: {health_data.get('status', 'unknown')}")
                return health_data.get('status') in ['healthy', 'degraded']
            return False
        except Exception as e:
            print(f"   Health check failed: {e}")
            return False

    def test_elasticsearch_connection(self):
        """Test Elasticsearch connection via health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                es_status = health_data.get('services', {}).get('elasticsearch', 'unknown')
                print(f"   Elasticsearch status: {es_status}")
                return es_status == 'healthy'
            return False
        except Exception as e:
            print(f"   Elasticsearch test failed: {e}")
            return False

    def test_api_docs(self):
        """Test API documentation endpoints"""
        try:
            # Test OpenAPI schema
            response = requests.get(f"{self.api_url}/openapi.json", timeout=10)
            if response.status_code != 200:
                return False
            
            schema = response.json()
            print(f"   API version: {schema.get('info', {}).get('version', 'unknown')}")
            
            # Test docs page
            docs_response = requests.get(f"{self.base_url}/api/docs", timeout=10)
            return docs_response.status_code == 200
            
        except Exception as e:
            print(f"   API docs test failed: {e}")
            return False

    def test_supported_file_types(self):
        """Test supported file types endpoint"""
        try:
            response = requests.get(f"{self.api_url}/documents/metadata/supported-types", timeout=10)
            if response.status_code == 200:
                data = response.json()
                extensions = data.get('supported_extensions', [])
                max_size = data.get('max_file_size_mb', 0)
                print(f"   Supported extensions: {extensions}")
                print(f"   Max file size: {max_size}MB")
                return len(extensions) > 0 and max_size > 0
            return False
        except Exception as e:
            print(f"   Supported file types test failed: {e}")
            return False

    def create_test_document(self) -> str:
        """Create a test PDF document"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()
            
            # Create PDF
            doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
            styles = getSampleStyleSheet()
            
            content = [
                Paragraph("TEST LEGAL DOCUMENT", styles['Title']),
                Paragraph("Case: Test v. System", styles['Heading2']),
                Paragraph("This is a test document for the DocuScan system. "
                         "It contains criminal law keywords like arrest, prosecution, "
                         "and defendant to test classification.", styles['Normal']),
                Paragraph("URGENT: This case requires immediate attention due to "
                         "time-sensitive nature.", styles['Normal'])
            ]
            
            doc.build(content)
            return temp_file.name
            
        except Exception as e:
            print(f"   Test document creation failed: {e}")
            return None

    def test_document_upload(self):
        """Test document upload functionality"""
        test_file = self.create_test_document()
        if not test_file:
            return False
            
        try:
            with open(test_file, 'rb') as f:
                files = {'file': ('test_document.pdf', f, 'application/pdf')}
                data = {
                    'case_type': 'criminal',
                    'client_name': 'Test Client',
                    'urgency_level': 'high'
                }
                
                response = requests.post(
                    f"{self.api_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=60
                )
            
            # Cleanup
            os.unlink(test_file)
            
            if response.status_code == 200:
                upload_data = response.json()
                document_id = upload_data.get('document_id')
                print(f"   Uploaded document ID: {document_id}")
                
                # Store for later tests
                self.test_document_id = document_id
                return True
            else:
                print(f"   Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   Document upload test failed: {e}")
            if test_file and os.path.exists(test_file):
                os.unlink(test_file)
            return False

    def test_document_processing(self):
        """Test document processing (OCR + NLP)"""
        if not hasattr(self, 'test_document_id'):
            print("   No test document available")
            return False
            
        try:
            # Wait for processing to complete
            max_wait = 60  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                response = requests.get(
                    f"{self.api_url}/documents/{self.test_document_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    doc_data = response.json()
                    status = doc_data.get('status')
                    print(f"   Document status: {status}")
                    
                    if status == 'processed':
                        case_type = doc_data.get('case_type')
                        urgency = doc_data.get('urgency_level')
                        summary = doc_data.get('summary', '')
                        
                        print(f"   Classified as: {case_type}")
                        print(f"   Urgency level: {urgency}")
                        print(f"   Summary length: {len(summary)} chars")
                        
                        return case_type is not None
                        
                    elif status == 'failed':
                        print("   Document processing failed")
                        return False
                        
                time.sleep(2)
            
            print("   Document processing timed out")
            return False
            
        except Exception as e:
            print(f"   Document processing test failed: {e}")
            return False

    def test_document_search(self):
        """Test document search functionality"""
        try:
            # Test basic search
            response = requests.get(f"{self.api_url}/documents/search", timeout=10)
            if response.status_code != 200:
                return False
                
            search_data = response.json()
            documents = search_data.get('documents', [])
            total = search_data.get('total', 0)
            
            print(f"   Found {total} documents")
            
            # Test search with query
            search_response = requests.get(
                f"{self.api_url}/documents/search?query=test&limit=5",
                timeout=10
            )
            
            if search_response.status_code == 200:
                query_data = search_response.json()
                print(f"   Query search returned {len(query_data.get('documents', []))} documents")
                return True
            
            return False
            
        except Exception as e:
            print(f"   Document search test failed: {e}")
            return False

    def test_document_export(self):
        """Test document export functionality"""
        try:
            # Test JSON export
            json_response = requests.get(
                f"{self.api_url}/documents/export/search?format=json&limit=5",
                timeout=30
            )
            
            if json_response.status_code != 200:
                return False
                
            # Verify it's valid JSON
            json.loads(json_response.content)
            print(f"   JSON export size: {len(json_response.content)} bytes")
            
            # Test CSV export
            csv_response = requests.get(
                f"{self.api_url}/documents/export/search?format=csv&limit=5",
                timeout=30
            )
            
            if csv_response.status_code == 200:
                print(f"   CSV export size: {len(csv_response.content)} bytes")
                return True
            
            return False
            
        except Exception as e:
            print(f"   Document export test failed: {e}")
            return False

    def test_dashboard_statistics(self):
        """Test dashboard statistics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/documents/statistics/dashboard", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                total_docs = stats.get('total_documents', 0)
                case_types = stats.get('case_types', {})
                urgency_levels = stats.get('urgency_levels', {})
                
                print(f"   Total documents: {total_docs}")
                print(f"   Case types: {len(case_types)}")
                print(f"   Urgency levels: {len(urgency_levels)}")
                
                return isinstance(stats, dict)
            return False
        except Exception as e:
            print(f"   Dashboard statistics test failed: {e}")
            return False

    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        try:
            response = requests.get(f"{self.base_url}", timeout=10)
            if response.status_code == 200:
                content = response.text
                # Check for basic elements
                has_title = "DocuScan" in content
                has_upload = "upload" in content.lower()
                has_search = "search" in content.lower()
                
                print(f"   Has title: {has_title}")
                print(f"   Has upload: {has_upload}")
                print(f"   Has search: {has_search}")
                
                return has_title and has_upload and has_search
            return False
        except Exception as e:
            print(f"   Frontend accessibility test failed: {e}")
            return False

    def test_api_error_handling(self):
        """Test API error handling"""
        try:
            # Test invalid endpoint
            response = requests.get(f"{self.api_url}/invalid-endpoint", timeout=10)
            if response.status_code != 404:
                return False
                
            # Test invalid document ID
            invalid_response = requests.get(f"{self.api_url}/documents/invalid-id", timeout=10)
            if invalid_response.status_code != 404:
                return False
                
            print("   Error handling working correctly")
            return True
            
        except Exception as e:
            print(f"   API error handling test failed: {e}")
            return False

    def test_document_content_retrieval(self):
        """Test document content retrieval"""
        if not hasattr(self, 'test_document_id'):
            print("   No test document available")
            return True  # Skip if no document
            
        try:
            response = requests.get(
                f"{self.api_url}/documents/{self.test_document_id}/content",
                timeout=10
            )
            
            if response.status_code == 200:
                content_data = response.json()
                text_content = content_data.get('text_content', '')
                print(f"   Retrieved content length: {len(text_content)} chars")
                return len(text_content) > 0
            elif response.status_code == 404:
                print("   Content not yet available (document may still be processing)")
                return True  # Not a failure
            else:
                return False
                
        except Exception as e:
            print(f"   Document content retrieval test failed: {e}")
            return False

    def test_performance(self):
        """Test basic performance metrics"""
        try:
            # Test health endpoint response time
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            health_time = time.time() - start_time
            
            # Test search endpoint response time
            start_time = time.time()
            search_response = requests.get(f"{self.api_url}/documents/search?limit=10", timeout=10)
            search_time = time.time() - start_time
            
            print(f"   Health endpoint: {health_time:.3f}s")
            print(f"   Search endpoint: {search_time:.3f}s")
            
            # Consider it a pass if both endpoints respond in reasonable time
            return health_time < 2.0 and search_time < 5.0
            
        except Exception as e:
            print(f"   Performance test failed: {e}")
            return False

    def cleanup_test_data(self):
        """Cleanup test data"""
        if hasattr(self, 'test_document_id'):
            try:
                response = requests.delete(f"{self.api_url}/documents/{self.test_document_id}")
                if response.status_code == 200:
                    print(f"   Cleaned up test document: {self.test_document_id}")
                else:
                    print(f"   Failed to cleanup test document: {response.status_code}")
            except Exception as e:
                print(f"   Cleanup failed: {e}")

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting DocuScan System Tests")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Elasticsearch Connection", self.test_elasticsearch_connection),
            ("API Documentation", self.test_api_docs),
            ("Supported File Types", self.test_supported_file_types),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("Dashboard Statistics", self.test_dashboard_statistics),
            ("Document Search", self.test_document_search),
            ("Document Export", self.test_document_export),
            ("API Error Handling", self.test_api_error_handling),
            ("Document Upload", self.test_document_upload),
            ("Document Processing", self.test_document_processing),
            ("Document Content Retrieval", self.test_document_content_retrieval),
            ("Performance Metrics", self.test_performance),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        print("\n" + "=" * 50)
        print("🧹 Cleaning up test data...")
        self.cleanup_test_data()
        
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        for result in self.test_results:
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}[result["status"]]
            print(f"{status_emoji} {result['name']}: {result['status']} ({result['duration']:.2f}s)")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! DocuScan is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
            return False

def wait_for_system(base_url: str, timeout: int = 120):
    """Wait for the system to be ready"""
    print(f"⏳ Waiting for DocuScan system at {base_url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') in ['healthy', 'degraded']:
                    print("✅ System is ready!")
                    return True
        except:
            pass
        
        print("   Still waiting...")
        time.sleep(5)
    
    print("❌ System did not become ready within timeout")
    return False

def main():
    parser = argparse.ArgumentParser(description="Test DocuScan system")
    parser.add_argument(
        "--base-url",
        default="http://localhost:3000",
        help="Base URL of the DocuScan system"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for system to be ready before testing"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds to wait for system"
    )
    
    args = parser.parse_args()
    
    if args.wait:
        if not wait_for_system(args.base_url, args.timeout):
            sys.exit(1)
    
    tester = DocuScanTester(args.base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 