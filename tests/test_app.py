from datetime import date
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'

def element(elements, label):
    return next(item for item in elements if item.label == label)

class AppTests(unittest.TestCase):
    def test_budget_add_delete_and_session_isolation(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)
        element(app.button, 'Set budget').click().run()
        self.assertEqual(app.metric[0].value, '$2,000.00')
        element(app.text_input, 'Amount ($)').input('$25')
        element(app.text_input, 'Description').input('Lunch')
        element(app.button, 'Add expense').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value, '$25.00')
        self.assertEqual(app.metric[2].value, '$1,975.00')
        element(app.text_input, 'Amount ($)').input('abc')
        element(app.text_input, 'Description').input('Bad')
        element(app.button, 'Add expense').click().run()
        self.assertTrue(app.error)
        self.assertEqual(len(app.session_state['expenses']), 1)
        element(app.button, 'Delete selected expense').click().run()
        self.assertEqual(len(app.session_state['expenses']), 1)
        element(app.checkbox, 'Confirm deletion of the selected expense').check()
        element(app.button, 'Delete selected expense').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state['expenses']), 0)
        second = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertEqual(second.metric[0].value, 'Not set')
        self.assertFalse(second.session_state['expenses'])

    def test_demo_month_filter_and_reset(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        element(app.button, 'Try sample expenses').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state['expenses']),5)
        self.assertEqual(app.metric[1].value,'$241.50')
        current_month = date.today().month
        other = 1 if current_month != 1 else 2
        element(app.selectbox, 'Month').select(other).run()
        self.assertEqual(app.metric[1].value, '$0.00')
        element(app.checkbox, 'Show every month').check().run()
        self.assertEqual(len(app.dataframe[0].value), 5)
        element(app.button, 'Start fresh').click().run()
        self.assertEqual(len(app.session_state['expenses']),5)
        element(app.checkbox, 'Clear all my session data').check()
        element(app.button, 'Start fresh').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.session_state['expenses'])
        self.assertFalse(app.session_state['budgets'])

if __name__ == '__main__':
    unittest.main()
