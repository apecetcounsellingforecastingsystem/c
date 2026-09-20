"""
Comprehensive Automated Test Suite for AP ECET Counselling Forecasting System.
Tests Flask endpoints, Authentication, Predictions, What-If simulator, Preferences,
PDF generators, and Admin Viva evaluation reports.
"""

import os
import json
import unittest
from app import app
from database import get_db_connection

class APECETSystemTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_home_page_renders(self):
        """Verify root renders the landing home page with status 200 and required elements."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AP ECET', response.data)
        self.assertIn(b'Predict Your Engineering Seat', response.data)
        self.assertIn(b'Data-Driven Precision', response.data)
        self.assertIn(b'JNTUK Univ. College of Engg.', response.data)

    def test_02_login_page_renders(self):
        """Verify login page renders with status 200 and required fields."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)
        self.assertIn(b'password-toggle-btn', response.data)

    def test_03_student_login_and_dashboard(self):
        """Verify student login redirects to profile page and saving profile proceeds to dashboard."""
        # 1. Login redirects immediately to profile page
        login_res = self.client.post('/login', data={
            'email': 'student@apecet.gov.in',
            'password': 'Student@12345'
        }, follow_redirects=False)
        self.assertEqual(login_res.status_code, 302)
        self.assertIn('/profile', login_res.headers['Location'])

        # 2. Student visits profile page
        profile_res = self.client.get('/profile')
        self.assertEqual(profile_res.status_code, 200)
        self.assertIn(b'Student profile', profile_res.data)
        self.assertIn(b'Save profile', profile_res.data)

        # 3. Saving profile proceeds to dashboard
        save_res = self.client.post('/profile', data={
            'username': 'student',
            'rank': 850,
            'category': 'OC',
            'gender': 'Boys',
            'region': 'AU',
            'diploma_branch': 'Computer Engineering',
            'preferred_branch': 'Computer Science & Engineering',
            'alternative_branch': 'None',
            'district': 'Any',
            'college_type': 'Any',
            'phone': '9123456780'
        }, follow_redirects=True)
        self.assertEqual(save_res.status_code, 200)
        self.assertIn(b'Dashboard', save_res.data)
        self.assertIn(b'Active Candidate Session', save_res.data)

    def test_04_prediction_flow(self):
        """Verify prediction run produces recommendations and Safe/Moderate/Dream classifications."""
        # Login first
        self.client.post('/login', data={'email': 'student@apecet.gov.in', 'password': 'Student@12345'})
        
        response = self.client.post('/run-prediction', data={
            'student_rank': 850,
            'branch': 'COMPUTER SCIENCE AND ENGINEERING',
            'category': 'BC-B',
            'gender': 'BOYS',
            'region': 'AU',
            'counselling_round': 'Phase 1',
            'district': 'ALL',
            'college_type': 'ALL',
            'max_budget': 100000,
            'save_to_profile': '1'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admission Forecasting Results', response.data)
        self.assertIn(b'Explainable AI Forecasting Breakdown', response.data)

    def test_05_what_if_simulator(self):
        """Verify What-If Simulator runs comparative outcomes."""
        self.client.post('/login', data={'email': 'student@apecet.gov.in', 'password': 'Student@12345'})
        response = self.client.get('/what-if?rank_a=850&branch_a=COMPUTER SCIENCE AND ENGINEERING&round_a=Phase 1&rank_b=1200&branch_b=ELECTRONICS AND COMMUNICATION ENGINEERING&round_b=Final Phase&category=BC-B&gender=BOYS')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'What-If Counselling Simulator', response.data)
        self.assertIn(b'Scenario A Outcomes', response.data)
        self.assertIn(b'Scenario B Outcomes', response.data)

    def test_06_preference_list_flow(self):
        """Verify adding, viewing, and exporting preference lists."""
        self.client.post('/login', data={'email': 'student@apecet.gov.in', 'password': 'Student@12345'})
        
        # Add a preference
        add_res = self.client.post('/api/preference-list/add', json={
            'college_code': 'AEC',
            'college_name': 'ADITYA ENGINEERING COLLEGE',
            'branch_name': 'COMPUTER SCIENCE AND ENGINEERING',
            'district': 'EG',
            'classification': 'Safe',
            'probability': 88.5,
            'closing_rank': 1250,
            'fees': 45000
        })
        self.assertEqual(add_res.status_code, 200)
        self.assertTrue(add_res.get_json()['success'])

        # View preference page
        pref_page = self.client.get('/preferences')
        self.assertEqual(pref_page.status_code, 200)
        self.assertIn(b'ADITYA ENGINEERING COLLEGE', pref_page.data)

        # Export PDF
        pdf_res = self.client.get('/export/preference-pdf')
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, 'application/pdf')

    def test_07_colleges_search_and_detail(self):
        """Verify colleges directory and detail profile."""
        self.client.post('/login', data={'email': 'student@apecet.gov.in', 'password': 'Student@12345'})
        
        dir_res = self.client.get('/colleges?q=ABR')
        self.assertEqual(dir_res.status_code, 200)
        self.assertIn(b'COLLEGE OF ENGG', dir_res.data)

        det_res = self.client.get('/college/ABRK')
        self.assertEqual(det_res.status_code, 200)
        self.assertIn(b'ABRK', det_res.data)

    def test_08_analytics_page(self):
        """Verify Cutoff Analytics renders with status 200."""
        self.client.post('/login', data={'email': 'student@apecet.gov.in', 'password': 'Student@12345'})
        res = self.client.get('/analytics')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Cutoff Analytics & Trend Visualizer', res.data)
        self.assertIn(b'yearlyTrendChart', res.data)

    def test_09_admin_viva_reports(self):
        """Verify admin can view model evaluation metrics (MAE, RMSE, R2, F1)."""
        self.client.post('/login', data={'email': 'admin@apecet.gov.in', 'password': 'Admin@12345'})
        
        rep_res = self.client.get('/admin/reports')
        self.assertEqual(rep_res.status_code, 200)
        self.assertIn(b'Model Performance & Evaluation', rep_res.data)
        self.assertIn(b'Linear Regression', rep_res.data)
        self.assertIn(b'Random Forest Regressor', rep_res.data)
        self.assertIn(b'MAE', rep_res.data)
        self.assertIn(b'F1-Score', rep_res.data)

if __name__ == '__main__':
    unittest.main()
