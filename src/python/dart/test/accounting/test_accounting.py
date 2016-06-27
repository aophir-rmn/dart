import unittest
import os, sys, json
from collections import namedtuple

testfile = os.path.realpath(__file__)
test_dir = os.path.dirname(testfile)
src_dir = '../../web/api/'
sys.path.append(test_dir + '/' + src_dir)
from utils import generate_accounting_event


import subprocess

class TestGenerateAccountingEvent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fakeRequest = namedtuple('FakeRequest', 'method path query_string get_json')

    def setUp(self):
        json_getter = lambda: '{}'

        self.dummyRequest = self.fakeRequest(method='GET',
                                             path='/api/1/engine/MY_ENGINE_ID',
                                             query_string='limit=10&page=0',
                                             get_json=json_getter)


    def test_dummy_request_parsing(self):
        self.assertEqual('GET', self.dummyRequest.method, "Expecting GET method")
        self.assertEqual('/api/1/engine/MY_ENGINE_ID', self.dummyRequest.path, "Expecting /api/1/engine/MY_ENGINE_ID path")
        self.assertEqual('limit=10&page=0', self.dummyRequest.query_string, "Expecting 'limit=10&page=0' query_string")
        self.assertEqual('{}', self.dummyRequest.get_json(), "Expecting {} json body")


    def test_generating_accounting_event_from_dummy_request(self):
        event = generate_accounting_event(200, self.dummyRequest)
        json_params = json.loads(event.params)

        p = subprocess.Popen(['env'], stdout=subprocess.PIPE,  stderr = subprocess.PIPE)
        out, err = p.communicate()
        print "=="+out

        self.assertEqual('200', event.return_code, "Expecting 200 return code")
        self.assertEqual('anonymous', event.user_id, "Expecting anonymous user id")
        self.assertEqual('engine/param', event.entity, "Expecting /engine/param as the path without the params")

        self.assertEqual([u'MY_ENGINE_ID'], json_params["URI"], "Expecting MY_ENGINE_ID sanitized URI")
        self.assertEqual('10', json_params["URL"]["limit"], "Expecting limit query string to be 10")
        self.assertEqual('0', json_params["URL"]["page"], "Expecting page query string to be 0")
        self.assertEqual('0', json_params["URL"]["page"], "Expecting ")
        self.assertEqual('{}', json_params["json_body"], "Expecting ")
