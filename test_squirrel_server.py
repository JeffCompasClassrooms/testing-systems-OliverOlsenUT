import http.client
import json
import os
import pytest
import shutil
import threading
import sys
import time
import urllib

from squirrel_db import SquirrelDB
from squirrel_server import HTTPServer, SquirrelServerHandler

skip = pytest.mark.skip(reason='temporary skip')

def assert_404(response):
    assert response.status == 404
    assert response.getheader('Content-Type') == "text/plain"
    assert response.read() == b"404 Not Found"

def describe_squirrel_server():
    @pytest.fixture()
    def setup_and_cleanup_db():
        db_name, db_copy_name, empty_db_name = "squirrel_db.db", "__squirrel_db.db", "empty_squirrel_db.db"
        shutil.copyfile(db_name, db_copy_name)
        shutil.copyfile(empty_db_name, db_name)
        yield
        shutil.move(db_copy_name, db_name)
    
    

    @pytest.fixture
    def http_client():
        conn = http.client.HTTPConnection('localhost:8080')
        return conn
        conn.close()
    
    @pytest.fixture(autouse=True)
    def start_and_stop_server(setup_and_cleanup_db):
        server = HTTPServer(("127.0.0.1", 8080), SquirrelServerHandler)

        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()

        yield

        # Shutdown and wait for thread to finish
        server.shutdown()
        thread.join()
    
    @pytest.fixture
    def request_body():
        return urllib.parse.urlencode({ 'name': 'Miney', 'size': 'small' })
    
    @pytest.fixture
    def request_headers():
        return { 'Content-Type': 'application/x-www-form-urlencoded' }
    
    @pytest.fixture
    def db():
        return SquirrelDB()
    
    @pytest.fixture
    def make_a_squirrel(db):
        db.createSquirrel("Mo", "large")

    # ok, here go the tests...
    def describe_get_squirrels():

        # just checking to see that it returns 200 is valuable, but very incomplete.
        def it_returns_200_status_code(http_client):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()

            assert response.status == 200

        # yes, you need to test that it returns the correct content type. 
        # Probably EVERY type of request should return the right content type, shouldn't it? (hint)
        def it_returns_json_content_type_header(http_client):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()

            assert response.getheader('Content-Type') == "application/json"

        # empty
        def it_returns_empty_json_array(http_client):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            response_body = response.read()

            # assert response_body == b'[]'
            assert json.loads(response_body) == []

        # one
        def it_returns_json_array_with_one_squirrel(http_client, make_a_squirrel):
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            response_body = response.read()

            # assert response_body == b'[]'
            assert json.loads(response_body) == [{"id": 1, "name": "Mo", "size": "large"}]

        # many...
        def it_returns_json_array_with_many_squirrels(db, http_client):
            db.createSquirrel("Mo", "large")
            db.createSquirrel("Miney", "small")
            http_client.request("GET", "/squirrels")
            response = http_client.getresponse()
            response_body = response.read()

            # assert response_body == b'[]'
            assert json.loads(response_body) == [{"id": 1, "name": "Mo", "size": "large"}, {"id": 2, "name": "Miney", "size": "small"}]
        
        def it_returns_404_status_for_invalid_path(http_client):
            http_client.request("GET", "/squires")
            response = http_client.getresponse()

            assert_404(response)
    
    def describe_get_squirrel():
        def it_returns_correct_response_for_valid_squirrel(http_client, make_a_squirrel):
            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            

            assert response.status == 200
            assert response.getheader('Content-Type') == "application/json"
            assert json.loads(response.read()) == {"id": 1, "name": "Mo", "size": "large"}

        def it_returns_404_response_for_invalid_squirrel(http_client, make_a_squirrel):
            http_client.request("GET", "/squirrels/2")
            response = http_client.getresponse()
            

            assert_404(response)

    def describe_create_squirrel():
        def it_returns_correct_response_for_valid_squirrel(http_client):
            # make sure the squirrel doesn't exist yet
            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            assert_404(response)
            
            # create the squirrel
            http_client.request("POST", "/squirrels", body="name=Mo&size=large")
            response = http_client.getresponse()
            assert response.status == 201

            # make sure it's actually created
            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            

            assert response.status == 200
            assert response.getheader('Content-Type') == "application/json"
            assert json.loads(response.read()) == {"id": 1, "name": "Mo", "size": "large"}

        def it_returns_404_response_for_providing_resource_id(http_client):
            http_client.request("POST", "/squirrels/1", body="name=Mo&size=large")
            response = http_client.getresponse()

            assert_404(response)
        
        def it_returns_404_response_for_invalid_path(http_client):
            http_client.request("POST", "/squires", body="name=Mo&size=large")
            response = http_client.getresponse()

            assert_404(response)

        # reinforcing bad behavior!!!!! only doing this because you want me to
        def it_errors_for_invalid_request_body(http_client):
            http_client.request("POST", "/squirrels", body="name=Mo")
            try:
                response = http_client.getresponse()
            except Exception as e:
                assert True
                return
            assert False
        
    def describe_update_squirrel():
        def it_returns_the_correct_response_for_valid_squirrel(http_client, make_a_squirrel):
            http_client.request("PUT", "/squirrels/1", body="name=Jess&size=medium")
            response = http_client.getresponse()
            assert response.status == 204

            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            

            assert response.status == 200
            assert response.getheader('Content-Type') == "application/json"
            assert json.loads(response.read()) == {"id": 1, "name": "Jess", "size": "medium"}
        
        # trigger 404 in handleSquirrelsUpdate
        def it_returns_404_for_nonexistent_squirrel(http_client):
            http_client.request("PUT", "/squirrels/1", body="name=Jess&size=medium")
            response = http_client.getresponse()
            assert_404(response)

        # trigger 404 in do_PUT (if not resourceId)
        def it_returns_404_for_not_providing_squirrel_id(http_client, make_a_squirrel):
            http_client.request("PUT", "/squirrels", body="name=Jess&size=medium")
            response = http_client.getresponse()
            assert_404(response)
        
        def it_returns_404_for_providing_the_wrong_path(http_client, make_a_squirrel):
            http_client.request("PUT", "/squires/1", body="name=Jess&size=medium")
            response = http_client.getresponse()
            assert_404(response)

        # reinforcing bad behavior!!!!! only doing this because you want me to
        def it_errors_for_invalid_request_body(http_client, make_a_squirrel):
            http_client.request("PUT", "/squirrels/1", body="name=Jess")
            try:
                response = http_client.getresponse()
            except Exception as e:
                assert True
                return
            assert False
    
    def describe_delete_squirrel():
        def it_returns_the_correct_response_for_valid_squirrel(http_client, make_a_squirrel):
            http_client.request("DELETE", "/squirrels/1", body="name=Mo&size=large")
            response = http_client.getresponse()
            assert response.status == 204

            http_client.request("GET", "/squirrels/1")
            response = http_client.getresponse()
            

            assert_404(response)
        
        def it_returns_404_for_nonexistent_squirrel(http_client):
            http_client.request("DELETE", "/squirrels/1")
            response = http_client.getresponse()
            assert_404(response)

        def it_returns_404_for_not_providing_squirrel_id(http_client, make_a_squirrel):
            http_client.request("DELETE", "/squirrels")
            response = http_client.getresponse()
            assert_404(response)
        
        def it_returns_404_for_providing_the_wrong_path(http_client, make_a_squirrel):
            http_client.request("DELETE", "/squires/1")
            response = http_client.getresponse()
            assert_404(response)
        