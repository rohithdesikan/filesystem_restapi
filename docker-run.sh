read -p 'Home Directory: ': homevar
docker run -d --name fbappv1 -p 8000:8000 -v $homevar:/mnt/location --env ROOT_DIR=/mnt/location fbapp:1.0
docker ps -f name=fbappv1
