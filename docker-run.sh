read -p 'Home Directory: ': homedir
docker run -d --name fbappv1 --publish 8000:8000 --volume $homedir:/mnt/location --env ROOT_DIR=/mnt/location fbapp:1.0
docker ps -f name=fbappv1