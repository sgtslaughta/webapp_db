# webapp_db
## Description:
A web application that allows users to create and approve requests. The front
end is written in Python using the Streamlit framework. The backend is a 
Mariadb
database. The application is containerized using docker-compose.
## Building:
`docker-compose` must be installed on the host machine and a working connection
to PyPi must be available.
```bash
sudo docker-compose up -d --build
```
## Usage:
The database must be initialized to apply the correct schema ( Only 
required the first time ). This can be 
done by running the following command:
```bash
sudo docker exec webapp python3 /app/lib/db_init.py
```
The application is available at `http://localhost:80`. 

## Known Issues:
- The application is not secure. It is indended to be run behind a reverse proxy
  with TLS enabled.
- The application is not scalable. It is intended to be run on a single host.
- The application is not fault-tolerant.
    - Shutting down the host while the DB is running is problematic. 
- The application is not highly available.
- Removing group items is bugged and only removes some items.
- There is currently no mechanism to remove users.
- There is currently no mechanism to send requests downstream.
- There is currently no mechanism to notify users of new requests.
