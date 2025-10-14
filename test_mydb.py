import os.path
import pickle
import pytest

from mydb import MyDB

"""
For the first test suite, test each of the four methods within 
the provided MyDB class using black-box system testing. 
Assume the implementations of the MyDB methods are correct.

Do not use test doubles. Instead, invoke the test subject's 
procedures and manually verify that each anticipated side effect
occurs as expected. Take care to set up and tear down each test case as
needed to guarantee test reliability.
"""

todo = pytest.mark.skip(reason='todo: pending spec')

@pytest.fixture
def db_filename():
    return "mydatabase.db"

@pytest.fixture
def nonempty_db(db_filename):
    with open(db_filename, 'wb') as f:
        pickle.dump(['stuff', 'more stuff'], f)

@pytest.fixture(autouse=True)
def cleanup(db_filename):
    # before each test case
    yield
    # after each test case
    if os.path.exists(db_filename):
        os.remove(db_filename)

def describe_MyDB():
    def describe_init():

        def it_assigns_fname_attribute(db_filename):
            db = MyDB(db_filename)
            assert db.fname == db_filename

        def it_creates_empty_database_if_it_does_not_exist(db_filename):
            assert not os.path.isfile(db_filename)
            db = MyDB(db_filename)
            assert os.path.isfile(db_filename)
            with open(db_filename, 'rb') as f:
                assert pickle.load(f) == []
        
        def it_doesnt_empty_database_if_it_does_exist(db_filename):
            with open(db_filename, 'wb') as f:
                pickle.dump(["existing data"], f)
            db = MyDB(db_filename)
            with open(db_filename, 'rb') as f:
                assert pickle.load(f) == ["existing data"]



    def describe_loadStrings():

        def it_loads_empty_database_if_no_data(db_filename):
            db = MyDB(db_filename)
            assert db.loadStrings() == []
        
        def it_loads_database_if_data(db_filename):
            strs = ["first string", "second string"]
            with open(db_filename, 'wb') as f:
                pickle.dump(strs, f)
            
            db = MyDB(db_filename)
            assert db.loadStrings() == strs
    
    def describe_saveStrings():

        def it_saves_array_data(db_filename):
            db = MyDB(db_filename)
            db.saveStrings(["array data"])
            with open(db_filename, 'rb') as f:
                assert pickle.load(f) == ["array data"]
        
    def describe_saveString():

        def it_saves_a_string(db_filename):
            db = MyDB(db_filename)
            db.saveString("string")
            # separate db to ensure no weird shenanigans are being done
            db2 = MyDB(db_filename)
            assert db2.loadStrings() == ["string"]
        
        def it_saves_on_top_of_an_existing_database(db_filename):
            db = MyDB(db_filename)
            db.saveString("string")
            # separate db to ensure no weird shenanigans are being done
            db2 = MyDB(db_filename)
            db2.saveString("another string")
            db3 = MyDB(db_filename)
            assert db3.loadStrings() == ["string", "another string"]
        


            

