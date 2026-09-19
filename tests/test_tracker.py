import unittest
from tracker import (parse_money, make_expense, category_totals, monthly_expenses,
                     read_csv, write_csv, merge_expenses)

class TrackerTests(unittest.TestCase):
    def test_money(self):
        self.assertEqual(parse_money(' $1,250.00 '), 125000)
        self.assertEqual(parse_money('0.10') + parse_money('0.20'), 30)
        for invalid in ['0', '-1', 'NaN', 'inf', '1,2,3', '1.001', '', '1e5', '$$2']:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_money(invalid)

    def test_dates_and_empty_fields(self):
        for day in ['2026-02-30', '2026-9-18', '10-13-88']:
            with self.assertRaises(ValueError):
                make_expense(day, 'Food', '10', 'Lunch')
        with self.assertRaises(ValueError):
            make_expense('2026-09-18', '  ', '10', 'Lunch')
        with self.assertRaises(ValueError):
            make_expense('2026-09-18', 'Food', '10', ' ')

    def test_categories_and_months(self):
        expenses = [make_expense('2026-09-18','food','25','Lunch'),
                    make_expense('2026-09-19','FOOD','15','Dinner'),
                    make_expense('2026-08-01','Travel','10','Bus')]
        self.assertEqual(category_totals(monthly_expenses(expenses,'2026-09')), {'Food':4000})

    def test_csv_round_trip(self):
        expense = make_expense('2026-09-18','Food','25','Lunch, with "friends"\nCafé')
        restored, errors = read_csv(write_csv([expense]))
        self.assertFalse(errors)
        self.assertEqual(restored[0]['description'], expense['description'])
        self.assertEqual(restored[0]['cents'], 2500)
        self.assertNotEqual(restored[0]['id'], expense['id'])

    def test_csv_bad_rows(self):
        raw = b'date,category,amount,description\n2026-09-18,Food,25,Good\n2026-02-30,Food,10,Bad\n2026-09-18,Food,abc,Bad\n2026-09-18,,10,Bad\n2026-09-18,Food,10,Lunch,extra\n'
        valid, errors = read_csv(raw)
        self.assertEqual(len(valid),1)
        self.assertEqual(len(errors),4)
        for invalid in [b'wrong,header\n', b'date,category,amount,description\n"broken', b'\xff']:
            with self.assertRaises(ValueError):
                read_csv(invalid)

    def test_duplicates(self):
        one = make_expense('2026-09-18','Food','10','Lunch')
        two = make_expense('2026-09-18','food','10','Lunch')
        merged, skipped = merge_expenses([one], [two])
        self.assertEqual((len(merged),skipped),(1,1))
        merged, skipped = merge_expenses([one], [two], False)
        self.assertEqual((len(merged),skipped),(2,0))

if __name__ == '__main__':
    unittest.main()
