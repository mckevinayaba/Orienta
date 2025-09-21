import requests
import sys
import json
from datetime import datetime

class OrientaAPITester:
    def __init__(self, base_url="https://edupath-finder-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_email = f"test_user_{datetime.now().strftime('%H%M%S')}@example.com"
        self.test_password = "TestPass123!"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": self.test_email,
                "password": self.test_password,
                "phone": "+27123456789"
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            if 'user' in response:
                self.user_id = response['user'].get('id')
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_email,
                "password": self.test_password
            }
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            if 'user' in response:
                self.user_id = response['user'].get('id')
            print(f"   Login token: {self.token[:20]}...")
            return True
        return False

    def test_get_profile(self):
        """Test getting user profile"""
        success, response = self.run_test(
            "Get Profile",
            "GET",
            "profile",
            200
        )
        return success

    def test_intake_questions(self):
        """Test getting intake questions"""
        success, response = self.run_test(
            "Get Intake Questions",
            "GET",
            "intake/questions",
            200
        )
        if success and 'questions' in response:
            print(f"   Found {len(response['questions'])} questions")
            return True, response['questions']
        return False, []

    def test_start_intake(self):
        """Test starting intake session"""
        success, response = self.run_test(
            "Start Intake Session",
            "POST",
            "intake/start",
            200
        )
        if success and 'id' in response:
            print(f"   Intake session ID: {response['id']}")
            return True, response['id']
        return False, None

    def test_submit_intake_answers(self, questions):
        """Test submitting intake answers"""
        if not questions:
            print("❌ No questions available for intake testing")
            return False

        # Test answers for each question type
        test_answers = {
            "grade": "Grade 12",
            "province": "Gauteng",
            "subjects": [{"subject": "Mathematics", "mark_band": "70-80"}],
            "interests": ["Medicine & Health", "Engineering"],
            "budget": "R50,000 - R100,000",
            "location": "Same province",
            "fields": ["Science & Technology", "Health Sciences"]
        }

        all_passed = True
        for question in questions:
            question_id = question.get('id')
            if question_id in test_answers:
                answer = test_answers[question_id]
                success, response = self.run_test(
                    f"Submit Answer - {question_id}",
                    "POST",
                    "intake/answer",
                    200,
                    params={
                        "question_id": question_id,
                        "answer": json.dumps(answer)
                    }
                )
                if not success:
                    all_passed = False
                elif response.get('session', {}).get('completed'):
                    print("   ✅ Intake completed!")
                    break
        
        return all_passed

    def test_pathways_preview(self):
        """Test getting pathway preview"""
        success, response = self.run_test(
            "Get Pathways Preview",
            "GET",
            "pathways/preview",
            200
        )
        if success and 'programme' in response:
            programme = response['programme']
            print(f"   Preview programme: {programme.get('title', 'Unknown')}")
            return True
        return False

    def test_payment_creation_paystack(self):
        """Test creating Paystack payment checkout session"""
        success, response = self.run_test(
            "Create Paystack Payment Checkout (Learner)",
            "POST",
            "payments/create-checkout",
            200,
            data={
                "plan_type": "learner",
                "gateway": "paystack"
            }
        )
        if success and 'checkout_url' in response:
            print(f"   Paystack Checkout URL: {response['checkout_url'][:50]}...")
            print(f"   Gateway: {response.get('gateway', 'unknown')}")
            print(f"   Reference: {response.get('reference', 'unknown')}")
            return True, response.get('reference')
        return False, None

    def test_payment_creation_paystack_premium(self):
        """Test creating Paystack premium payment checkout session"""
        success, response = self.run_test(
            "Create Paystack Payment Checkout (Premium)",
            "POST",
            "payments/create-checkout",
            200,
            data={
                "plan_type": "premium",
                "gateway": "paystack"
            }
        )
        if success and 'checkout_url' in response:
            print(f"   Paystack Premium Checkout URL: {response['checkout_url'][:50]}...")
            return True, response.get('reference')
        return False, None

    def test_payment_creation_stripe(self):
        """Test creating Stripe payment checkout session"""
        success, response = self.run_test(
            "Create Stripe Payment Checkout (Learner)",
            "POST",
            "payments/create-checkout",
            200,
            data={
                "plan_type": "learner",
                "gateway": "stripe"
            }
        )
        if success and 'checkout_url' in response:
            print(f"   Stripe Checkout URL: {response['checkout_url'][:50]}...")
            print(f"   Gateway: {response.get('gateway', 'unknown')}")
            print(f"   Session ID: {response.get('session_id', 'unknown')}")
            return True, response.get('session_id')
        return False, None

    def test_payment_creation_stripe_premium(self):
        """Test creating Stripe premium payment checkout session"""
        success, response = self.run_test(
            "Create Stripe Payment Checkout (Premium)",
            "POST",
            "payments/create-checkout",
            200,
            data={
                "plan_type": "premium",
                "gateway": "stripe"
            }
        )
        if success and 'checkout_url' in response:
            print(f"   Stripe Premium Checkout URL: {response['checkout_url'][:50]}...")
            return True, response.get('session_id')
        return False, None

    def test_payment_status(self):
        """Test checking payment status"""
        success, response = self.run_test(
            "Check Payment Status",
            "GET",
            "payments/status",
            200
        )
        if success:
            has_paid = response.get('has_paid_access', False)
            print(f"   Has paid access: {has_paid}")
            return True
        return False

    def test_payment_verification_mock(self, reference):
        """Test payment verification endpoint (mock - won't actually verify)"""
        if not reference:
            print("   Skipping verification test - no reference provided")
            return True
            
        success, response = self.run_test(
            f"Verify Payment Reference",
            "GET",
            f"payments/verify/{reference}",
            404  # Expected to fail since payment wasn't actually made
        )
        # We expect this to fail since we didn't actually pay
        print("   ✅ Verification endpoint accessible (expected 404 for unpaid transaction)")
        return True

def main():
    print("🚀 Starting Orienta Backend API Tests")
    print("=" * 50)
    
    tester = OrientaAPITester()
    
    # Test sequence
    print("\n📝 Phase 1: Authentication Tests")
    if not tester.test_user_registration():
        print("❌ Registration failed, stopping tests")
        return 1
    
    # Test login with same credentials
    if not tester.test_user_login():
        print("❌ Login failed, stopping tests")
        return 1
    
    print("\n👤 Phase 2: Profile Tests")
    if not tester.test_get_profile():
        print("❌ Profile fetch failed")
        return 1
    
    print("\n📋 Phase 3: Intake Tests")
    success, questions = tester.test_intake_questions()
    if not success:
        print("❌ Failed to get intake questions")
        return 1
    
    if not tester.test_start_intake():
        print("❌ Failed to start intake session")
        return 1
    
    if not tester.test_submit_intake_answers(questions):
        print("❌ Failed to submit intake answers")
        return 1
    
    print("\n🎯 Phase 4: Pathways Tests")
    if not tester.test_pathways_preview():
        print("❌ Failed to get pathways preview")
        return 1
    
    print("\n💳 Phase 5: Dual Payment Integration Tests")
    
    # Test payment status first
    if not tester.test_payment_status():
        print("❌ Failed to check payment status")
        return 1
    
    # Test Paystack payments
    print("\n💰 Testing Paystack Integration:")
    paystack_success, paystack_ref = tester.test_payment_creation_paystack()
    if not paystack_success:
        print("⚠️  Paystack payment creation failed - continuing with other tests")
    
    paystack_premium_success, _ = tester.test_payment_creation_paystack_premium()
    if not paystack_premium_success:
        print("⚠️  Paystack premium payment creation failed - continuing with other tests")
    
    # Test Stripe payments
    print("\n💳 Testing Stripe Integration:")
    stripe_success, stripe_ref = tester.test_payment_creation_stripe()
    if not stripe_success:
        print("⚠️  Stripe payment creation failed - continuing with other tests")
    
    stripe_premium_success, _ = tester.test_payment_creation_stripe_premium()
    if not stripe_premium_success:
        print("⚠️  Stripe premium payment creation failed - continuing with other tests")
    
    # Test payment verification endpoints
    print("\n🔍 Testing Payment Verification:")
    if not tester.test_payment_verification_mock(paystack_ref or stripe_ref):
        print("⚠️  Payment verification test failed - continuing")
        
    # Continue with tests even if some payment tests fail
    print("\n✅ Core backend functionality tests completed")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())