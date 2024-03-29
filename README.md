## Overview
This is a quick application that can be downloaded and run locally. When a local file directory is put in while running the application, all further directories can be explored using a REST API. For this project, I used the Python FastAPI + Pydantic framework to build the application and its internal testing tool (built off pytest and requests) called TestClient for testing. I chose to be explicit about getting, posting or deleting files/folders.


## Methods
`GET`, `POST` and `DELETE` methods are implemented. All responses are a JSON formatted dictionary containing the contents of a folder or a file. All inputs to `POST` and `DELETE` methods also receive JSON formatted bodies as input. 


### GET /
When the bash script is run, user input is requested. This is the home folder below which the user can browse folder or file contents. Note that all requests in this API need to begin at the home directory. For example, getting a file nested inside a sub folder will have to be `/subfolder/subfolder/test.txt`. Assuming the user input is a folder, this method returns the following:

`is_folder` : True 

`folder_contents`: 
* subfolder1
* subfolder2
* file1.txt
* etc

### GET /folder/subfolder
The user can go as deep as needed within sub folders. An error is raised if the folder does not exist. All sub folders will return results the same way as the root folder shown above.


### GET /file.txt or /folder/file.txt
The user is able to get the contents of a text file. For example, when inputting a request, it should be /test_file.txt. Note that the .txt extention must be provided. As an extension to the exercise, an appropriate error message is returned if the file in the request is not a txt file. For a text file, the return object is as follows:

* `is_file`: True
* `name`: "filename"
* `owner`: 100
* `size`: (bytes)
* `permissions`: (octal representation)
* `file_contents`: This is a sample text file


### POST /createfile or /createfolder
The POST method is split up into two types, the `createfile` and `createfolder`. This allows the user to be explicit in their request. For example, the JSON bodies for requesting the creation of a file is different from a folder as a file includes contents. Therefore they are split up into different requests. For example, the `createfolder` method only needs a name (or path) whereas the `createfile` request also needs a 'content' key. These can be combined within 1 method in the future where the 'content' key is a set of sub folders or files. Feel free to access the documentation below for examples. 


### DELETE /emptyfolder /deletefolder /deletefile
The DELETE method takes 3 requests, empty or delete folders or delete a file. This was designed to make sure folders with potentially important data was not erased during this process. First emptying a folder and then deleting it (like Amazon S3) ensures that data is not accidentally deleted. 

The `emptyfolder` documentation only takes a folder and will not empty the contents of a file. The `deletefolder` can then delete an empty folder. 

As for the `deletefile` request, this directly deletes the file given the location. Examples are shown in the Swagger UI documentation. 


## Running the application
Since this app has been Dockerized, 2 bash scripts have been provided for convenience. The first is a docker-build.sh file which builds the docker image based on the Dockerfile. The Dockerfile pulls the fastapi image from DockerHub, then creates a working directory, copies the contents of this directory (including the requirements.txt) into the working directory inside the container, installs the necessary python packages and runs the uvicorn app/app:app bash command on the local host. 

As for starting up the actual container, in the docker-run.sh bash script, it asks for a user input, which is the home directory from where to launch the app. Once user input is received, the app is named `fbappv1`, port 8000 is mapped from the host to the container and the `homedir` bash variable that was received as input is the volume that is bind mounted so that the home directory and all sub folders/files are replicated inside the container. Finally, an internal environment variable, `ROOT_DIR` is set to be this bind mounted directory inside the Docker container which is read by the app. Note that the FastAPI specific inputs (uvicorn app/app:app) was provided in the Dockerfile whereas the runtime parameters are set in the docker-run.sh script.

So, to build and run the image, in the terminal (Mac), run the following commands
* cd << folder where this Dockerfile is stored>>
* bash docker-build.sh
* bash docker-run.sh: When it asks for a home directory, put in: `/Users/<< username >>/...` to the directory you wish to browse. This is the `ROOT_DIR` variable in app.py which will open the app in this directory
* Then go to `localhost:8000` and browse the app on the web browser or from the command line or from a python script using the requests library. The docker ps command is also run automatically. 


## Documentation
Once the app is running, feel free to go to `localhost:8000/docs` to explore full Swagger UI documentation with examples and execute requests as needed. 

Furthermore, within app.py, each function has been documented to show the process. 


## Testing
I followed test driven development strategy writing up the necessary tests, especially for the `GET` method before testing. I used FastAPI's client testing service called TestClient which uses pytest, starlette and requests in the background. To run tests, first create a bash variable called `ROOT_DIR` which takes in the path to `.../app`. During the testing process, a new folder named `test_folder` will be created and torn down. However, since the app expects a bash variable, the rootdir needs to be changed from whatever directory being browsed through the Docker container above to this `app.py` and `test_app.py` directory. Once in the app directory, run:

`pytest`

## Additional Work
* Implement a `PUT` method, which will follow the same strategy as the `POST` and `DELETE` methods and some additional tests
* Do `emptyfolder` and `deletefolder` need to be separated? This is a design choice that can be changed. Likewise, `createfolder` and `createfile` can be combined into a single `create` if necessary. 
* Add permission and owner controls for file creation
* Create a helm chart