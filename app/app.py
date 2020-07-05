# Import relevant packages
import os
import shutil
from typing import Dict
from fastapi import FastAPI, HTTPException, Request, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# TODO: DOCKERIZE THE APP AND TEST THE DOCKER CONTAINER ON THE WORK WINDOWS COMPUTER
# TODO: CREATE A HELM CHART

######## POTENTIAL NEXT STEPS:
# TODO: Add another variable for create_permissions that only allows file creation if admin access is available
# TODO: The success messages can be deleted if it is not necessary

# Instantiate the FastAPI 
app = FastAPI(name = 'Local File Directory Browsing Service', 
            description = "An app that can browse a local file system given a root directory upon launching and can add or empty/delete files or folders",
            version = "0.1.0")

# Get the environment variable from the .sh script
root_path = os.environ.get("ROOT_DIR", os.getcwd())

def does_exist(path: str):
    """Checks whether a file path exists on the local file system and raises an error if not. This can be used for both files and folders. 

    Args:
        path (str): A string path to a folder or file

    Raises:
        HTTPException: File or folder not found, check input
    """    

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File or folder not found")


def get_file_metadata(file_path: str):
    """Gets the file metadata so that if a GET request is sent to retrieve a file, the metadata is presented

    Args:
        file_path (str): An appropriate file path that has been checked with the does_exist function above

    Returns:
        dict: A dictionary that contains name, owner, size and permissions (in octal representation)
    """    

    # Get the file stats which is returned as an os.stats object
    file_stats = os.stat(file_path) 
    
    # Get the relevant attributes (ones that start with st_) from file_stats
    file_stats_dict = {k: getattr(file_stats, k) for k in dir(file_stats) if k.startswith('st_')}

    name = os.path.basename(file_path).split('.')[0]
    owner = file_stats_dict['st_uid']
    size = os.path.getsize(file_path)
    permissions = oct(file_stats_dict['st_mode'])[-3:]

    # Return as a dictionary that can be merged with file contents as a JSON response
    file_metadata = {'name' : name, 
                'owner' : owner, 
                'size' : size, 
                'permissions' : permissions}
    
    return file_metadata


def get_file_content(file_path: str):
    """Get the contents of a text file

    Args:
        file_path (str): An appropriate file path that has been checked with the does_exist function above

    Raises:
        HTTPException: If not a .txt file, raise a BadRequest Error

    Returns:
        dict: This single valued dictionary returns the contents of the file
    """    

    # Run a quick test to make sure the file path is a text file
    if not file_path.endswith('.txt'):
        raise HTTPException(status_code=422, detail="Only a file with extension .txt can be opened")

    with open(file_path, 'rb') as f:
        contents = f.read().decode('utf-8')

    return {'file_contents': contents}


def request_output(path: str):
    """An internal function that is called by the 2 get requests below depending on whether it is a file or folder

    Args:
        path (str): A file or folder path

    Returns:
        fastapi.responses.JSONResponse: A JSON Response dictionary containing the keys:
        
        If folder:
        - is_folder: True
        - folder_contents: A list of folders and files in the folder sent into the get request

        If file:
        - is_file: True
        - file_contents: A dictionary that contains all the metadata and file contents (that is assumed to fit comfortably within a JSON blob)
    """    

    # Make sure the path exists
    does_exist(path)

    # If it is a folder, return the appropriate content as a JSONResponse
    if os.path.isdir(path):
        contents = {'is_folder': True, 'folder_contents' : os.listdir(path)}

        return JSONResponse(content = contents)
    
    # If the get request is a file, merge the metadata and file_data dictionaries and return as a JSONResponse that can be easily parsed
    elif os.path.isfile(path):
        file_metadata = get_file_metadata(path)
        file_data = get_file_content(path)
        file_contents = {'is_file': True, **file_metadata, **file_data}
    
        return JSONResponse(content = file_contents)

# The home folder that is specified in the shell script or the command line
@app.get('/')
def root_folder():
    """Show the contents of the root folder as inputted by the user in the shell script

    Returns:
        fastapi.response.JSONResponse: A JSON result showing the folders and files in the root directory
    """    

    return request_output(root_path)


@app.get('/{sub_path:path}')
def sub_folder(sub_path: str):
    """Calls the same request_output function above to return the contents of either a file or folder

    Args:
        sub_path (str): The path starting at the home directory

    Returns:
        fastapi.response.JSONResponse: A JSON result showing the folders and files in the root directory or file contents
    """    

    # Join this sub-path from the root_path which is the home directory
    full_sub_path = os.path.join(root_path, sub_path)
    return request_output(full_sub_path)


class CreateFolder(BaseModel):

    create_name: str

    class Config:
        schema_extra = {
            "example": {
                "create_name": "test1/test1_1",
            }
    }

@app.post('/createfolder')
def create_folder(create: CreateFolder):
    """Send a POST request to create a folder as a JSON formatted request where (key, value) = (create_name, 'folder_name'). Note that to create a folder, it must be in relation to the root directory set up when launching the app. 

    Args:
        create (CreateFolder): Inherits from the CreateFolder class. If the request is incorrect, it is verified by Pydantic's data validation object. folder_name should be a str

    Returns:
        fastapi.response.JSONResponse: Returns a success message if a folder has been created in the full path provided. This dict is automatically converted to a JSONReponse in FastAPI's backend.
    """    

    # Create the full path and make sure it exists
    full_folder_path = os.path.join(root_path, create.create_name)

    # If a file path exists, then no action is taken. This can be changed to return an error if needed.
    if os.path.exists(full_folder_path):
        raise HTTPException(status_code=422, detail="Folder already exists, no action taken")

    os.mkdir(full_folder_path)

    return {'detail' : 'Folder Created Successfully'}
    

class CreateFile(BaseModel):

    create_name: str
    create_content: str


    class Config:
        schema_extra = {
            "example": {
                'create_name': 'test1/test1_1.txt',
                'create_content': 'This is a sample text file that is generated with a create POST request'
            }
    }

@app.post('/createfile')
def create_file(create: CreateFile):
    """Send a POST request to create a file as a JSON formatted request where (key1: value1, key2: value2) = (create_name: 'file_name', 'create_content': 'Content'). Note that to create a file, it must be in relation to the root directory set up when launching the app. 

    Args:
        create (CreateFile): Inherits from the CreateFile class. If the request is incorrect, it is verified by Pydantic's data validation object. file_id and file_contents should be str

    Raises:
        HTTPException: If the file type desired is not a text file, creation will not work

    Returns:
        fastapi.response.JSONResponse: A simple dict showing a success message. 
    """    

    # Can only create text files
    if create.create_name.split('.')[-1] != 'txt':
        raise HTTPException(status_code=422, detail='Files of type other than .txt cannot be created')

    # Create the full path and make sure it exists
    full_file_path = os.path.join(root_path, create.create_name)

    # If a file path exists, then no action is taken. This can be changed to return an error if needed
    if os.path.exists(full_file_path):
        raise HTTPException(status_code=422, detail="File already exists, no action taken")

    with open(full_file_path, 'w') as file:
        file.write(create.create_content)

    return {'detail' : 'File Created Successfully'}


class EmptyFolder(BaseModel):

    delete_name: str

    class Config:
        schema_extra = {
            "example": {
                'delete_name': 'test1',
            }
    }

@app.delete('/emptyfolder')
def empty_folder(empty: EmptyFolder):
    """If a folder is not empty, empty all the data within the folder, including files and subfolders. Note that this folder must be specified relative to the root directory specified at startup. 

    Args:
        empty (EmptyFolder): Inherits from the EmptyFolder class. If the request is incorrect, it is verified by Pydantic's data validation object. delete_name has to be a str

    Raises:
        HTTPException: If this is a .txt file, raise an 400 error, this API cannot empty the contents of a text file. Can add this functionality if neede

    Returns:
        fastapi.response.JSONResponse: A simple dict showing a success message. 
    """    

    # Make sure the client is not trying to empty a file, only a folder
    if empty.delete_name.endswith('.txt'):
        raise HTTPException(status_code=422, detail="Note that empty_folder is only to empty a folder, not to empty the contents of files")

    # Create the full path and make sure it exists
    full_folder_path = os.path.join(root_path, empty.delete_name)
    does_exist(full_folder_path)

    # Walk through all the files and sub directories within this 1 and remove contents
    for root, dirs, files in os.walk(full_folder_path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
    
    return {'detail' : 'Folder Emptied Successfully'}


class DeleteFolder(BaseModel):

    delete_name: str

    class Config:
        schema_extra = {
            "example": {
                'delete_name': 'test1',
            }
    }

@app.delete('/deletefolder')
def delete_folder(delete: DeleteFolder):
    """If a folder is empty, this function deletes the folder. Note that this folder must be specified relative to the root directory specified at startup. 

    Args:
        delete (DeleteFolder): Inherits from the DeleteFolder class. If the request is incorrect, it is verified by Pydantic's data validation object. delete_name has to be a str

    Raises:
        HTTPException: If the folder is not empty, an error 400 is raised to tell the user to empty the folder first. This is to make sure that local data is not accidentally deleted. 

    Returns:
        fastapi.response.JSONResponse: A simple dict showing a success message. 
    """    

    # Create the full path and make sure it exists
    full_folder_path = os.path.join(root_path, delete.delete_name)
    does_exist(full_folder_path)

    if len(os.listdir(full_folder_path)) > 0:
        raise HTTPException(status_code=422, detail="A folder must be empty before deletion. Use the empty folder method")

    os.rmdir(full_folder_path)

    return {'detail' : 'Folder Deleted Successfully'}


class DeleteFile(BaseModel):

    delete_name: str

    class Config:
        schema_extra = {
            "example": {
                'delete_name': 'test1/test1.txt',
            }
    }

@app.delete('/deletefile')
def delete_file(delete: DeleteFile):
    """Deletes a file from the local file system. Note that this file must be specified relative to the root directory specified at startup. 

    Args:
        delete (DeleteFile): Inherits from the DeleteFile class. If the request is incorrect, it is verified by Pydantic's data validation object. delete_name has to be a str

    Returns:
        fastapi.response.JSONResponse: A simple dict showing a success message. 
    """    

    # Create the full path and make sure it exists
    full_file_path = os.path.join(root_path, delete.delete_name)
    does_exist(full_file_path)

    os.remove(full_file_path)

    return {'detail' : 'File Deleted Successfully'}