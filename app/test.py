try:
    from server import app
    import unittest
    from clickhouse_driver import Client

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

    def connection(): # create clickhouse connection
        connect = Client(host='localhost', password='c6n3s2')
        try:
            connect.execute("select now();")
            return connect
        except:
            False
        
if __name__ == "__main__":
    unittest.main()