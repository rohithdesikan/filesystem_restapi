# When running pytest, please make sure to set the environment variable to be inside a test_folder
import os
import shutil
import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# Make a test folder in this directory with all the necessary sub files and folders to make sure all the tests work
@pytest.fixture(scope = "session")
def create_test_folder():
    os.mkdir('test_folder')

    # Create a hidden file and a non txt file for testing
    with open("test_folder/.hidden.txt", "w") as file:
        file.write("Sample Hidden File")

    with open("test_folder/nontxtfile.py", "w") as file:
        file.write("Sample non txt file")


    # Create a file for testing file contents
    with open("test_folder/filecontents.txt", "w") as file:
        file.write("This text file is tested in file contents")

    # Create a test folder for testing folder contents
    os.mkdir('test_folder/foldercontents')

    with open("test_folder/foldercontents/test1.txt", "w") as file:
        file.write("Testing folder contents file 1")

    with open("test_folder/foldercontents/test2.txt", "w") as file:
        file.write("Testing folder contents file 2")

    os.mkdir('test_folder/blankfolder')


    # Create a folder and a file to test that creating these files again will lead to an error
    os.mkdir('test_folder/existingfolder')

    with open("test_folder/existingfolder/existingfile.txt", "w") as file:
        file.write("Testing folder contents file 1")


    # Create a test folder for emptying its contents
    os.mkdir('test_folder/emptyfoldercontents')

    with open("test_folder/emptyfoldercontents/test1.txt", "w") as file:
        file.write("Testing folder contents file 1")

    with open("test_folder/emptyfoldercontents/test2.txt", "w") as file:
        file.write("Testing folder contents file 2")

    # Because these folders and files will be checked for deletion, they will be deleted if the test works, so they should be created everytime
    # Create a folder for deletion
    os.mkdir('test_folder/delete_folder')

    # Create a file to be deleted
    with open("test_folder/test_delete_file.txt", "w") as file:
        file.write("This test file will tested for deletion")

    yield os.path.join(os.getcwd(), 'test_folder')

    # Remove the entire test_folder which was only created to test each of these methods
    shutil.rmtree('test_folder')


# Steps in all tests:
# - Make sure the response code is appropriate. It may be appropriate in many cases even if the request is not processable by the API
# - Convert the response to a dict 

# Create the test_folder location as a script variable
test_path = os.path.join(os.getcwd(), 'test_folder')


# TEST THE BASE ROOT FOLDER AND CONTENTS
# --------------------------------------------------------
# Check if the root folder launches properly and if the response is a dictionary/json
def test_existing_root_folder(create_test_folder):
    response = client.get("/")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

# Test if hidden files are shown
def test_existing_folder_contents(create_test_folder):
    response = client.get("/test_folder")
    assert response.status_code == 200
    rjson = response.json()
    assert rjson['is_folder'] == True

    # Make sure the hidden file is shown
    assert '.hidden.txt' in rjson['folder_contents']

# TEST SUB FILE OUTPUTS
# --------------------------------------------------------
# Open a txt file and make sure it works (Just create 1 separate method for opening a txt file and only test that 1 method to make sure the txt file reads properly)
def test_sub_file(create_test_folder):
    response = client.get("/test_folder/filecontents.txt")
    assert response.status_code == 200
    rjson = response.json()

    # Make sure the file metadata is reported properly by checking the expected output set with the response set
    expected_outputs = ['is_file', 'name', 'owner', 'size', 'permissions', 'file_contents']
    assert set(expected_outputs) == set(list(rjson.keys()))

    # Make sure this really is a file, the name does not contain a '.txt at the end and the file contents for this simple file
    assert rjson['is_file'] == True
    assert rjson['name'] == 'filecontents'
    assert rjson['file_contents'] == ['This text file is tested in file contents']

# Test to make sure a non existing file returns an error 404 with the appropriate message
def test_sub_file_no_exists(create_test_folder):
    response = client.get("/test_folder/test_noexist.txt")
    assert response.status_code == 404
    rjson = response.json()
    assert rjson['detail'] == 'File or folder not found'

# Make sure a non text file cannot be opened with the appropriate detailed error message
def test_open_file_nottxt(create_test_folder):
    response = client.get("/test_folder/nontxtfile.py")
    assert response.status_code == 422
    rjson = response.json()
    assert rjson['detail'] == "Only a file with extension .txt can be opened"


# TEST SUB FOLDER OUTPUTS
# --------------------------------------------------------
# Test if a sub folder created here contains the files expected
def test_sub_folder(create_test_folder):
    response = client.get("/test_folder/foldercontents")
    assert response.status_code == 200
    rjson = response.json()
    assert rjson['is_folder'] == True
    assert len(rjson['folder_contents']) == 2

    expected_output = ['test1.txt', 'test2.txt']

    assert set(expected_output) == set(rjson['folder_contents'])

# Make sure that even if a blank folder is presented that it simply returns an empty list
def test_sub_folder_blank(create_test_folder):
    response = client.get("/test_folder/blankfolder")
    assert response.status_code == 200
    rjson = response.json()
    assert rjson['is_folder'] == True
    assert len(rjson['folder_contents']) == 0


# TEST THE CREATE FOLDER AND CREATE FILE POST METHODS
# --------------------------------------------------------
def test_create_folder(create_test_folder):
    response = client.post("/createfolder", json = {'create_name': 'test_folder/newfolder'})
    assert response.status_code == 200
    assert 'newfolder' in os.listdir(test_path)

def test_create_folder_exists(create_test_folder):
    response = client.post("/createfolder", json = {'create_name': 'test_folder/existingfolder'})
    assert response.status_code == 422
    rjson = response.json()
    assert rjson['detail'] == 'Folder already exists, no action taken'

def test_create_file(create_test_folder):
    response = client.post("/createfile", json = {'create_name': 'test_folder/newfile.txt', 'create_content': 'This is a sample text file that is generated with a create POST request'})
    assert response.status_code == 200
    assert 'newfile.txt' in os.listdir(test_path)

def test_create_file_exists(create_test_folder):
    response = client.post("/createfile", json = {'create_name': 'test_folder/existingfolder/existingfile.txt', 'create_content': 'This is a sample text file that is generated with a create POST request'})
    assert response.status_code == 422
    rjson = response.json()
    assert rjson['detail'] == 'File already exists, no action taken'

def test_create_file_nontxt(create_test_folder):
    response = client.post("/createfile", json = {'create_name': 'test_folder/newfile.py', 'create_content': 'This is a sample non text file for expected error'})
    assert response.status_code == 422
    rjson = response.json()
    assert rjson['detail'] == 'Files of type other than .txt cannot be created'


# TEST THE EMPTY FOLDER DELETE METHODS
# --------------------------------------------------------
def test_empty_folder(create_test_folder):
    response = client.delete("/emptyfolder", json = {'delete_name': 'test_folder/emptyfoldercontents'})
    assert response.status_code == 200
    rjson = response.json()
    assert rjson['detail'] == 'Folder Emptied Successfully'
    assert len(os.listdir('test_folder/emptyfoldercontents')) == 0

def test_empty_file(create_test_folder):
    response = client.delete("/emptyfolder", json = {'delete_name': 'test_folder/emptyfoldercontents/test1.txt'})
    assert response.status_code == 422
    rjson = response.json()
    assert rjson['detail'] == 'Note that empty_folder is only to empty a folder, not to empty the contents of files'

def test_empty_folder_noexist(create_test_folder):
    response = client.delete("/emptyfolder", json = {'delete_name': 'test_folder/test_no_exist'})
    assert response.status_code == 404


# TEST THE DELETE FOLDER METHODS
# --------------------------------------------------------
def test_delete_folder(create_test_folder):
    response = client.delete("/deletefolder", json = {'delete_name': 'test_folder/delete_folder'})
    assert response.status_code == 200
    rjson = response.json()
    assert rjson['detail'] == 'Folder Deleted Successfully'

def test_delete_folder_noexist(create_test_folder):
    response = client.delete("/deletefolder", json = {'delete_name': 'test_folder/folder_no_exist'})
    assert response.status_code == 404

# Try deleting a non empty folder to make sure the right result is returned
def test_delete_folder_notempty(create_test_folder):
    response = client.delete("/deletefolder", json = {'delete_name': 'test_folder/foldercontents'})
    assert response.status_code == 422
    rjson = response.json()
    assert rjson['detail'] == "A folder must be empty before deletion. Use the empty folder method"


# TEST THE DELETE FILE METHODS
# --------------------------------------------------------
def test_delete_file(create_test_folder):
    response = client.delete("/deletefile", json = {'delete_name': 'test_folder/test_delete_file.txt'})
    assert response.status_code == 200
    rjson = response.json()
    assert rjson['detail'] == 'File Deleted Successfully'

def test_delete_file_noexist(create_test_folder):
    response = client.delete("/deletefile", json = {'delete_name': 'test_folder/file_no_exist.txt'})
    assert response.status_code == 404