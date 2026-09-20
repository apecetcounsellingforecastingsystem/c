import os
import glob
import unittest
from app import app

class ArchitectureAndUITestSuite(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_landing_page_renders_index_html(self):
        """1. GET / renders templates/index.html with status 200."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        
        # Branding & Header
        self.assertIn('AP ECET', html)
        self.assertIn('COUNSELLING FORECASTER', html)
        self.assertIn('themeToggleBtn', html)
        self.assertIn('Student Login', html)
        self.assertIn('Admin', html)
        self.assertIn('Register', html)

        # Hero content
        self.assertIn('Predict Your Engineering Seat with', html)
        self.assertIn('Data-Driven Precision', html)
        self.assertIn('JNTUK Univ. College of Engg., Kakinada', html)
        self.assertIn('Computer Science & Engineering', html)

    def test_02_password_svg_icons(self):
        """2. Password visibility icons use SVG vectors, no emojis."""
        # Login page
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('<svg', html)
        self.assertNotIn('👁️', html)
        self.assertNotIn('👁️🗨️', html)

        # Register page
        res_reg = self.client.get('/register')
        self.assertEqual(res_reg.status_code, 200)
        html_reg = res_reg.data.decode('utf-8')
        self.assertIn('<svg', html_reg)
        self.assertNotIn('👁️', html_reg)
        self.assertNotIn('👁️🗨️', html_reg)

        # Admin login page
        res_adm = self.client.get('/admin/login')
        self.assertEqual(res_adm.status_code, 200)
        html_adm = res_adm.data.decode('utf-8')
        self.assertIn('<svg', html_adm)
        self.assertNotIn('👁️', html_adm)

    def test_03_separated_login_portals_and_role_guard(self):
        """3. Separated Student (/login) and Admin (/admin/login) Portals with Role Guard."""
        # Student portal page
        res_student_page = self.client.get('/login')
        self.assertEqual(res_student_page.status_code, 200)
        self.assertIn('Student Portal Login', res_student_page.data.decode('utf-8'))
        self.assertIn('Access Admin Portal →', res_student_page.data.decode('utf-8'))

        # Admin portal page
        res_admin_page = self.client.get('/admin/login')
        self.assertEqual(res_admin_page.status_code, 200)
        self.assertIn('Administrator Portal', res_admin_page.data.decode('utf-8'))
        self.assertIn('Go to Student Login →', res_admin_page.data.decode('utf-8'))

        # Role Guard: Student trying to sign in at /admin/login is rejected and sent to /login
        guarded_res = self.client.post('/admin/login', data={
            'email': 'student@apecet.gov.in',
            'password': 'Student@12345'
        }, follow_redirects=False)
        self.assertEqual(guarded_res.status_code, 302)
        self.assertIn('/login', guarded_res.headers['Location'])

        # Admin logging in at /admin/login succeeds and redirects to /admin
        admin_res = self.client.post('/admin/login', data={
            'email': 'admin@apecet.gov.in',
            'password': 'Admin@12345'
        }, follow_redirects=False)
        self.assertEqual(admin_res.status_code, 302)
        self.assertIn('/admin', admin_res.headers['Location'])

    def test_04_no_demo_accounts_hints(self):
        """4. Verify no demo account credentials or placeholder hints exist in templates."""
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        html_files = glob.glob(os.path.join(templates_dir, '**', '*.html'), recursive=True)
        self.assertTrue(len(html_files) > 5)

        forbidden_phrases = [
            'Student@12345',
            'Admin@12345',
            'Demo Account',
            'Demo Credentials',
            'Quick Demo',
            'student@apecet.gov.in',
            'admin@apecet.gov.in'
        ]

        for filepath in html_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                for phrase in forbidden_phrases:
                    self.assertNotIn(
                        phrase,
                        content,
                        f"Forbidden demo text '{phrase}' found in {os.path.basename(filepath)}"
                    )

    def test_05_student_post_login_profile_flow_and_left_drawer(self):
        """5. Student Login redirects to /profile, profile has 11 fields, save proceeds to dashboard."""
        # 1. Login redirects immediately to /profile
        login_res = self.client.post('/login', data={
            'email': 'student@apecet.gov.in',
            'password': 'Student@12345'
        }, follow_redirects=False)
        self.assertEqual(login_res.status_code, 302)
        self.assertIn('/profile', login_res.headers['Location'])

        # 2. Inspect Student Profile page for 11 fields and screenshot UI matching
        prof_res = self.client.get('/profile')
        self.assertEqual(prof_res.status_code, 200)
        prof_html = prof_res.data.decode('utf-8')

        # Header title and theme button
        self.assertIn('Student profile', prof_html)
        self.assertIn('profileThemeToggleBtn', prof_html)

        # 11 Fields
        self.assertIn('Username', prof_html)
        self.assertIn('Mobile', prof_html)
        self.assertIn('ECET rank', prof_html)
        self.assertIn('Category', prof_html)
        self.assertIn('Gender', prof_html)
        self.assertIn('Local area', prof_html)
        self.assertIn('Diploma branch', prof_html)
        self.assertIn('Preferred B.Tech branch', prof_html)
        self.assertIn('Alternative branch', prof_html)
        self.assertIn('Preferred district', prof_html)
        self.assertIn('College type preference', prof_html)

        # Buttons
        self.assertIn('Save profile', prof_html)
        self.assertIn('Change password', prof_html)
        self.assertIn('btn-cyan-save', prof_html)

        # Left Sliding Drawer (☰) in base template
        self.assertIn('openDrawerBtn', prof_html)
        self.assertIn('studentSidebarDrawer', prof_html)
        self.assertIn('drawerOverlay', prof_html)
        self.assertIn('Forecast Chances', prof_html)
        self.assertIn('What-If Simulator', prof_html)
        self.assertIn('Preference List', prof_html)

        # 3. Saving profile updates database and redirects to /dashboard
        save_res = self.client.post('/profile', data={
            'username': 'student_updated',
            'phone': '9876543210',
            'rank': 720,
            'category': 'BC-B',
            'gender': 'Boys',
            'region': 'AU',
            'diploma_branch': 'Computer Engineering',
            'preferred_branch': 'Computer Science & Engineering',
            'alternative_branch': 'Information Technology',
            'district': 'Visakhapatnam',
            'college_type': 'Govt / University'
        }, follow_redirects=False)
        self.assertEqual(save_res.status_code, 302)
        self.assertIn('/dashboard', save_res.headers['Location'])

        # 4. Visit dashboard
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn('Active Candidate Session', dash_res.data.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()
