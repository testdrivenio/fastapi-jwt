In this tutorial, you'll learn how to secure your application by enabling authentication using JWT. We'll be using PyJWT to sign, encode and decode JWT tokens.

## Contents

- Objectives
- Authentication with FastAPI
- Initial setup
- What we will be building
- GET route
- POST route
- PUT route
- DELETE route
- Building Authentication
    - JWT Handler
    - JWT Bearer
    - User registration and Login
- Securing the routes
- Conclusion

## Objectives

By the end of this tutorial, you will be able to:
1. Develop a RESTful API with Python and FastAPI
2. Secure your FastAPI app with JWT

## Authentication in FastAPI

Authentication is the process of verifying users before granting them access to secured resources. When a user is authenticated, the user is now authorized to access secured resources not open to the public.

In this article, we will be looking at authenticating our FastAPI application with [Bearer Authentication](https://swagger.io/docs/specification/authentication/bearer-authentication/) which involves security tokens called bearer tokens. The bearer tokens in this case will be JSON Web Token (JWT).

> [Authentication in FastAPI](https://fastapi.tiangolo.com/tutorial/security/) can also be handled by OAuth.

## Initial Setup

Start by creating a new folder to hold your project called "fastapi-jwt":

```sh
mkdir fastapi-jwt
cd fastapi-jwt
```

Next, create and activate a virtual environment:

```sh
python3.9 -m venv venv
source venv/bin/activate
export PYTHONPATH=$PWD
```

> Feel free to swap out virtualenv and Pip for [Poetry](https://python-poetry.org/) or [Pipenv](https://pipenv.pypa.io/).

Install FastAPI:

```
(venv)$ pip3 install fastapi==0.61.1 uvicorn==0.11.8 python-decouple==3.3
```


Next, create the following files and folders:

```
├── fastapi-jwt
│   ├── main.py
│   └── app
│       ├── api.py
│       ├── model.py
│       ├── auth
```

In the *main.py* file, define an entry point for running the application:

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)
```

Here, we instructed the file to run a [Uvicorn](https://www.uvicorn.org/) server on port 8000 and reload on every file change.

Before starting the server via the entry point file, create a base route in *app/api.py*:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/", tags=["Root"])
async def read_root() -> dict:
    return {"message": "Welcome to your blog!."}

```

Run the entry point file from your console:


```
(venv)$ python main.py
```

Navigate to [http://localhost:8000](http://localhost:8000) in your browser. You should see:

```
{
    "message":"Welcome to your blog!."
}
```
## What Are We Building?

For the remainder of this tutorial, you'll be building a secured mini-blog CRUD app for creating, reading, updating, and deleting blogposts. By the end, your app will look like this:

![Simple MiniBlog](https://res.cloudinary.com/adeshina/image/upload/v1604438959/es41rkejx2mvpv7bqjkk.gif)

## Models

Before we proceed, let's define the schema for the posts. In `model.py`, add:

```python
from pydantic import BaseModel, Field, EmailStr

class PostSchema(BaseModel):
    id: int = Field(default=None)
    title: str = Field(...)
    content: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "title": "Securing FastAPI applications with JWT.",
                "content": "In this tutorial, you'll learn how to secure your application by enabling authentication using JWT. We'll be using PyJWT to sign, encode and decode JWT tokens...."
            }
        }
```

## GET Route

Start by importing the PostSchema then adding a list of dummy posts and an empty user dictionary variable in *app/api.py*:

```json
from app.model import PostSchema

posts = [
    {
        "id": 1,
        "title": "Pancake",
        "content": "Lorem Ipsum ..."
    }
]
users = {}
```

Then, add the route handler for getting all the posts and an individual post by ID:

```python
@app.get("/post", tags=["posts"])
async def get_posts() -> dict:
    return { "data": posts }

@app.get("/post/{id}", tags=["posts"])
async def get_single_post(id: int) -> dict:
    if id > len(posts):
        return {
            "error": "No such post with the supplied ID."
        }

    for post in posts:
        if post["id"] == id:
            return {
                "data": post
            }
```

Manually test the routes at [http://localhost:8000/post](http://localhost:8000/post) and [http://localhost:8000/post/1](http://localhost:8000/post/1)

## POST Route

Just below the GET route, add the following handler for creating a new post:


```python
@app.post("/post", tags=["posts"])
async def add_post(post: PostSchema) -> dict:
    post.id = len(posts) + 1
    posts.append(post)
    return {
        "data": "post added."
    }
```

With the backend running, test the POST route on the interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs)

```sh
$ curl -X POST http://localhost:8000/post -d \
    '{ "id": 2, "title": "Lorem Ipsum tres", "content": "content goes here"}' \ -H 'Content-Type: application/json'
```

You should see:

```json
{
    "data": [
        "post added."
    ]
}
```

## PUT Route

Next, add the route for updating the post:

```python
@app.put("/post/{id}", tags=["posts"])
async def update_post(id: int, body: dict) -> dict:
    for post in posts:
        if post["id"] == id:
            post["title"] = body["title"]
            post["content"] = body["content"]
            return {
                "data": f"post with id {id} has been updated."
            }

    return {
        "data": f"post with id {id} not found."
    }
```

So, we checked for the post with an ID matching the one supplied and then, if found, updated the post's title and content.

## DELETE Route

Next, add the delete route:

```python
@app.delete("/post/{id}", tags=["posts"])
async def delete_post(id: int) -> dict:
    for post in posts:
        if int(post["id"]) == id:
            posts.remove(post)
            return {
                "data": f"post with id {id} has been removed."
            }

    return {
        "data": f"post with id {id} not found."
    }
```

## Building Authentication

In this section, we'll build the user authentication system which comprises of registration route, signing in and singing out routes, JWT token handler and bearer. We'll begin by building the JWT components as the tokens will be used for user authentication activities.

Before we begin, install PyJWT, the JWT library. We will be using and python-decouple for reading environment variables:

```sh
pip3 install PyJWT
```

### JWT Handler

The JWT Hander file will be responsible for signing and encoding, decoding and returning JWT tokens. In the *auth* folder, create a file `auth_handler.py`:

```python
import time
from typing import Dict
import jwt
from decouple import config

def token_response(token: str):
    return {
        "access_token": token
    }

JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")
```

In the code block above, we start by importing the time, typing and jwt module. The time module is responsible for setting an expiry for the tokens. Every JSON Web Token has an expiry date and or time where it becomes invalid. The `jwt` module is going to be responsible for encoding and decoding generated token strings. Lastly, the `token_response` function is a helper function for returning generated tokens.


> JSON Web Tokens are encoded into strings from a dictionary payload.

Next, create an environment file `.env` in the base directory:

```
secret=astrongjwtsecret
algorithm=HS256
```

#### JWT secret and Algorithm

The secret in the environment file should be substituted with something stronger and should not be disclosed. It is used in the encoding and decoding process of JWT strings.

The algorithm value on the other hand is the type of algorithm used in  the encoding process.

Back to `auth_handler.py`, write the functions for signing and decoding the JWT string:


```python
def signJWT(user_id: str) -> Dict[str, str]:
    payload = {
        "user_id": user_id,
        "expires": time.time() + 2400
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM).decode()

    return token_response(token)
```

In the `signJWT` function, we define the payload, a dictionary containing the user_id passed into the function and an expiry time of 10 minutes from when it is generated. Next, we create a token string comprising of the payload, the secret and the algorithm type and then return it.

Then the `decodeJWT` function:

```python
def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token.encode(), JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
```

The `decodeJWT` function takes the token and decodes it with the aid of the `jwt` module and then stores it in a `decoded_token` variable. Next, we return the decoded_token if the expiry time is valid, otherwise return None.

### JWT Bearer

The JWTBearer class is a subclass of FastAPI's **HTTPBearer** class that will be used to persist authentication on our routes. Create a new file `auth_bearer.py` in the auth folder:

```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth_handler import decodeJWT
```

We started off by importing the Request and HTTPException class from FastAPI after which we imported the HTTPBearer and HTTPAuthorizationCredentials from `fastapi.security` module and lastly, imported the `decodeJWT` function.

Next, let's build the JWTBearer subclass:

```python
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = decodeJWT(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid
```

In the code block above, we defined the subclass and in the `__init__` method, enabled automatic error reporting by setting the boolean `auto_error` to True. 

#### The `verify_jwt` method

This method helps in verifying if a token passed is valid. The method takes a jwt string which it passes to the `decodeJWT` function and returns a boolean value based on the outcome from `decodeJWT`.

#### The __call__ method

In the `__call__` method, we defined a variable credentials of type `HTTPAuthorizationCredentials` which is filled when the JWTBearer class is invoked. We then proceed to check if the credentials passed in the course of invoking the class is valid:

    1. If the credential scheme isn't a Bearer scheme, raise an exception for invalid token scheme.
    
    2. If a bearer token was passed, verify that the JWT token is valid.
    
If no credentials was gotten, raise an invalid authorization error.

With the token register in place. Let's add routes for signing up, signing in and logging out users. 

### User registration and Login

In `model.py`, add the user schema:

```pytho
class UserSchema(BaseModel):
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "fullname": "Abdulazeez Abdulazeez Adeshina",
                "email": "abdulazeez@x.com",
                "password": "weakpassword"
            }
        }

class UserLoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "email": "abdulazeez@x.com",
                "password": "weakpassword"
            }
        }
```

Next, update the model import and update the FastAPI's import:

```python
from fastapi import FastAPI, Body
...
from app.model import PostSchema, UserSchema, UserLoginSchema
```


Next, add the user sign up route:

```python
@app.post("/user/signup", tags=["User"])
async def create_user(user: UserSchema = Body(...)):
    users.append(user)
    return signJWT(user.email)
```

Test it on the [interactive documentation](http://localhost:8000/docs)

> In a production server, you should hash your password using bcrypt or any secure hashing library.

Next, define a helper function to check if a user exists:

```python
def check_user(data: UserLoginSchema):
    print(data)
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False
```

The above function checks if a user exists before creating a JWToken with the user email. Next, define the login route:

```python
@app.post("/user/login", tags=["User"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }
```

Again, try the login route by first creating a user and then logging in. 

> You're creating a new user because the application reloads on every change ton the application.


## Securing Routes.

With the authentication in place, let's secure the create, update and delete route. To secure the routes, we'll be setting a dependency for our routes with FastAPI's [Depends](https://fastapi.tiangolo.com/tutorial/dependencies/).

Start by importing the JWTBearer class:

```python
from app.auth.auth_bearer import JWTBearer
```

In the GET, CREATE and DELETE post routes, add the dependencies argument to the `@app` property: such that they look exactly like this

```python
@app.post("/post", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def add_post(post: PostSchema) -> dict:
    post.id = len(posts) + 1
    posts.append(post)
    return {
        "data": "post added."
    }

@app.put("/post/{id}", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def update_post(id: int, body: dict) -> dict:
    for post in posts:
        if post["id"] == id:
            post["title"] = body["title"]
            post["content"] = body["content"]
            return {
                "data": f"post with id {id} has been updated."
            }

    return {
        "data": f"post with id {id} not found."
    }

@app.delete("/post/{id}", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def delete_post(id: int) -> dict:
    for post in posts:
        if int(post["id"]) == id:
            posts.remove(post)
            return {
                "data": f"post with id {id} has been removed."
            }
    return {
        "data": f"post with id {id} not found."
    }
```

Refresh your interactive docs page and you should have the screen:

![Interactive Documentation](https://res.cloudinary.com/adeshina/image/upload/v1604437598/zc9fi3hzflw2jzprpx9s.png)

Test the authentication by trying to visit a protected route without passing in a token:

![Not Authenticated](https://res.cloudinary.com/adeshina/image/upload/v1604438059/vimshs5uh3wsun6nrnfa.png)

Test the routes by creating a new user and copying the access token generated:

![Access token](https://res.cloudinary.com/adeshina/image/upload/v1604437768/msqxam3jcmealkhtup3e.png)

After copying it, click on the authorize button on the top right corner and paste the token:
![Authorize user](https://res.cloudinary.com/adeshina/image/upload/v1604438183/vaejageag2njn7vjkyqj.png)

After that, you can use the routes.

## Conclusion

This post covered the process of securing a FastAPI application using JWTokens.

Check your understanding by reviewing the objectives from the beginning of this post. You can find the source code in the [fastapi-jwt](https://github.com/testdrivenio/fastapi-jwt) repository. Thanks for reading.

Looking for some challenges?
1. Hash the passwords before saving it using passlib or bcrypt.
2. Move the user and post from temporary storage to either MongoDB or MySQL. You can follow the steps in [Building a CRUD App with FastAPI and MongoDB](https://testdriven.io/blog/fastapi-mongo/) to setup a MongoDB database and deploy to Heroku.