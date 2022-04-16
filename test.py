try:
    from server import app
    import unittest

except Exception as e:
    print("Some modules are missins {}".format(e))

class FlaskTest(unittest.TestCase):
    # class for the api parameters testing, for more detais please Check the readme.md file.
    
    # check for response 200
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get("/report")
        status_code = response.status_code
        self.assertEqual(status_code, 200)
    
    # check filter taxomony and mandatory fields.
    def test_report_filter(self): 
        tester = app.test_client(self)
        response = tester.get("/report/<filter>")
        print(response.data)
        self.assertFalse(b'Query failed, check your filter taxonomy' in response.data)
    
    # check json format.
    def test_index_data(self):
        tester = app.test_client(self)
        response = tester.get('/api/event/<event>')
        self.assertFalse(b'Invalid json format' in response.data)
        
if __name__ == "__main__":
    unittest.main()