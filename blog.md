# Securing FastAPI with JWT Token-based Authentication

In this tutorial, you'll learn how to secure a FastAPI app by enabling authentication using JSON Web Tokens (JWTs). We'll be using [PyJWT](https://pyjwt.readthedocs.io/) to sign, encode, and decode JWT tokens.

## Authentication in FastAPI

Authentication is the process of verifying users before granting them access to secured resources. When a user is authenticated, the user is allowed to access secure resources not open to the public.

We'll be looking at authenticating a FastAPI app with [Bearer](https://swagger.io/docs/specification/authentication/bearer-authentication/) (or Token-based) authentication, which involves generating security tokens called bearer tokens. The bearer tokens in this case will be JWTs.

> [Authentication in FastAPI](https://fastapi.tiangolo.com/tutorial/security/) can also be handled by OAuth.

## Initial Setup

Start by creating a new folder to hold your project called "fastapi-jwt":

```sh
$ mkdir fastapi-jwt
$ cd fastapi-jwt
```

Next, create and activate a virtual environment:

```sh
$ python3.9 -m venv venv
$ source venv/bin/activate
(venv)$ export PYTHONPATH=$PWD
```

> Feel free to swap out virtualenv and Pip for [Poetry](https://python-poetry.org/) or [Pipenv](https://pipenv.pypa.io/). For more, review [Modern Python Environments](/blog/python-environments/).

Install FastAPI and [Uvicorn](https://www.uvicorn.org/):

```sh
(venv)$ pip install fastapi==0.62.0 uvicorn==0.12.3
```

Next, create the following files and folders:

```sh
fastapi-jwt
├── app
│   ├── __init__.py
│   ├── api.py
│   ├── auth
│   └── model.py
└── main.py
```

In the *main.py* file, define an entry point for running the application:

```python
# main.py

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.api:app", host="0.0.0.0", port=8081, reload=True)
```

Here, we instructed the file to run a Uvicorn server on port 8081 and reload on every file change.

Before starting the server via the entry point file, create a base route in *app/api.py*:

```python
# app/api.py

from fastapi import FastAPI

app = FastAPI()

@app.get("/", tags=["Root"])
async def read_root() -> dict:
    return {"message": "Welcome to your blog!."}

```

Run the entry point file from your console:

```sh
(venv)$ python main.py
```

Navigate to [http://localhost:8081](http://localhost:8081) in your browser. You should see:

```json
{
    "message": "Welcome to your blog!."
}
```

## What Are We Building?

For the remainder of this tutorial, you'll be building a secured mini-blog CRUD app for creating, reading, updating, and deleting blog posts. By the end, your app will look like this:

<img data-src="/static/images/blog/fastapi-jwt-auth/final_app.gif" loading="lazy" class="lazyload" style="max-width:100%;text-align:center;" alt="Final blog app">

TODO: re-record image

## Models

Before we proceed, let's define the schema for the posts.

In *model.py*, add:

```python
# app/model.py

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

## Routes

### GET Route

Start by importing the `PostSchema` then adding a list of dummy posts and an empty user dictionary variable in *app/api.py*:

```python
# app/api.py

from app.model import PostSchema

posts = [
    {
        "id": 1,
        "title": "Pancake",
        "content": "Lorem Ipsum ..."
    }
]

users = []
```

Then, add the route handler for getting all the posts and an individual post by ID:

```python
# app/api.py

@app.get("/posts", tags=["posts"])
async def get_posts() -> dict:
    return { "data": posts }


@app.get("/posts/{id}", tags=["posts"])
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

*app/api.py* should now look like this:

```python
# app/api.py
from fastapi import FastAPI

from app.model import PostSchema

posts = [
    {
        "id": 1,
        "title": "Pancake",
        "content": "Lorem Ipsum ..."
    }
]

users = []

app = FastAPI()

@app.get("/", tags=["Root"])
async def read_root() -> dict:
    return {"message": "Welcome to your blog!."}


@app.get("/posts", tags=["posts"])
async def get_posts() -> dict:
    return { "data": posts }


@app.get("/posts/{id}", tags=["posts"])
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

Manually test the routes at [http://localhost:8081/posts](http://localhost:8081/posts) and [http://localhost:8081/posts/1](http://localhost:8081/posts/1)

### POST Route

Just below the GET routes, add the following handler for creating a new post:


```python
# app/api.py

@app.post("/posts", tags=["posts"])
async def add_post(post: PostSchema) -> dict:
    post.id = len(posts) + 1
    posts.append(post.dict())
    return {
        "data": "post added."
    }
```

With the backend running, test the POST route via the interactive docs at [http://localhost:8081/docs](http://localhost:8081/docs).

You can also test with curl:

```sh
$ curl -X POST http://localhost:8081/posts \
    -d  '{ "id": 2, "title": "Lorem Ipsum tres", "content": "content goes here"}' \
    -H 'Content-Type: application/json'
```

You should see:

```json
{
    "data": [
        "post added."
    ]
}
```

## JWT Authentication

In this section, we'll build the user authentication system which comprises of registration, signing in, and singing out routes as well as a JWT token handler and a class to handle the bearer token. We'll begin by building the JWT components as the tokens will be used for user authentication activities.

Before we begin, install [PyJWT](https://pyjwt.readthedocs.io/), for encoding and decoding JWTs. We'll also be using and [python-decouple](https://github.com/henriquebastos/python-decouple/) for reading environment variables:

```sh
(venv)$ pip install PyJWT==1.7.1 python-decouple==3.3
```

### JWT Handler

The JWT handler will be responsible for signing, encoding, decoding, and returning JWT tokens. In the "auth" folder, create a file called *auth_handler.py*:

```python
# app/auth/auth_handler.py

import time
from typing import Dict

import jwt
from decouple import config


JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")


def token_response(token: str):
    return {
        "access_token": token
    }
```

In the code block above, we imported the `time`, `typing`, and `jwt` module. The `time` module is responsible for setting an expiry for the tokens. Every JWT has an expiry date and/or time where it becomes invalid. The `jwt` module is responsible for encoding and decoding generated token strings. Lastly, the `token_response` function is a helper function for returning generated tokens.

> JSON Web Tokens are encoded into strings from a [dictionary payload](https://jwt.io/introduction).

#### JWT Secret and Algorithm

Next, create an environment file called *.env* in the base directory:

```
secret=pleasepleaseupdatemeplease
algorithm=HS256
```

The secret in the environment file should be substituted with something stronger and should not be disclosed. For example:

```python
>>> import os
>>> import binascii
>>> binascii.hexlify(os.urandom(24))
b'deff1952d59f883ece260e8683fed21ab0ad9a53323eca4f'
```

The secret key is used for encoding and decoding JWT strings.

The algorithm value on the other hand is the type of algorithm used in the encoding process.

Back in *auth_handler.py*, add the function for signing the JWT string:

```python
# app/auth/auth_handler.py

def signJWT(user_id: str) -> Dict[str, str]:
    payload = {
        "user_id": user_id,
        "expires": time.time() + 600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token_response(token)
```

In the `signJWT` function, we defined the payload, a dictionary containing the `user_id` passed into the function, and an expiry time of ten minutes from when it is generated. Next, we created a token string comprising of the payload, the secret, and the algorithm type and then returned it.

Next, add the `decodeJWT` function:

```python
# app/auth/auth_handler.py

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
```

The `decodeJWT` function takes the token and decodes it with the aid of the `jwt` module and then stores it in a `decoded_token` variable. Next, we returned `decoded_token` if the expiry time is valid, otherwise, we returned `None`.

### User Registration and Login

Moving along, let's wire up the routes, schemas, and helpers for handling user registration and login.

In *model.py*, add the user schema:

```python
# app/model.py

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

Next, update the imports in *app/api.py*:

```python
# app/api.py

from fastapi import FastAPI, Body

from app.model import PostSchema, UserSchema, UserLoginSchema
from app.auth.auth_handler import signJWT
```

Add the the user registration route:

```python
# app/api.py

@app.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    users.append(user) # replace with db call, making sure to hash the password first
    return signJWT(user.email)
```

Since we're using an [email validator](https://pydantic-docs.helpmanual.io/usage/types/#pydantic-types), `EmailStr`, install [email-validator](https://github.com/JoshData/python-email-validator):

```sh
(venv)$ pip install "pydantic[email]"
```

Run the server:

```sh
(venv)$ python main.py
```

Test it via the interactive documentation at [http://localhost:8081/docs](http://localhost:8081/docs).

TODO: add image

> In a production environment, make sure to hash your password using [bcrypt](https://github.com/pyca/bcrypt/) or [passlib](https://passlib.readthedocs.io/) before saving the user to the database.

Next, define a helper function to check if a user exists:

```python
# app/api.py

def check_user(data: UserLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False
```

The above function checks to see if a user exists before creating a JWT with the user email.

Next, define the login route:

```python
# app/api.py

@app.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }
```

Test the try the login route by first creating a user and then logging in.

TODO: add image

> Since users are stored in memory, you'll have to create a new user each time the application reloads to test out logging in.

## Securing Routes

With the authentication in place, let's secure the create, update, and delete routes.

### JWT Bearer

Now we need to verify each protected route, by checking whether the request is authorized or not. This is done by scanning the request for the JWT under `Authorization` header. FastAPI provides the basic validation using the `HTTPBearer` class. We use the *HTTPBearer* class to extract and parse the token and verify it using the `decodeJWT` function defined in *app/auth/auth_handler.py*. 

Create a new file in the "auth" folder called *auth_bearer.py*:

```python
# app/auth/auth_bearer.py

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth_handler import decodeJWT


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

So, the `JWTBearer` class is a subclass of FastAPI's [HTTPBearer](https://github.com/tiangolo/fastapi/blob/0.62.0/fastapi/security/http.py#L94) class that will be used to persist authentication on our routes.

#### Init

In the `__init__` method, we enabled automatic error reporting by setting the boolean [auto_error](https://github.com/tiangolo/fastapi/blob/0.62.0/fastapi/security/http.py#L100) to `True`.

#### Call

In the `__call__` method, we defined a variable credential of type [HTTPAuthorizationCredentials](https://github.com/tiangolo/fastapi/blob/0.62.0/fastapi/security/http.py#L20), which is filled when the `JWTBearer` class is invoked. We then proceeded to check if the credentials passed in during the course of invoking the class are valid:

1. If the credential scheme isn't a bearer scheme, we raised an exception for an invalid token scheme.
1. If a bearer token was passed, verify that the JWT is valid.
1. If no credentials were received, we raised an invalid authorization error.

#### Verify

The `verify_jwt` method verifies whether a token is valid. The method takes a `jwtoken` string which it then passes to the `decodeJWT` function and returns a boolean value based on the outcome from `decodeJWT`.

### Depends

To secure the routes, we'll be setting a dependency for our routes with FastAPI's [Depends](https://fastapi.tiangolo.com/tutorial/dependencies/?h=+depends#import-depends).

Start by updating the imports by adding the `JWTBearer` class as well as `Depends`:

```python
# app/api.py

from fastapi import FastAPI, Body, Depends

from app.model import PostSchema, UserSchema, UserLoginSchema
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import signJWT
```

In the POST route, add the `dependencies` argument to the `@app` property like so:

```python
# app/api.py

@app.post("/posts", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def add_post(post: PostSchema) -> dict:
    post.id = len(posts) + 1
    posts.append(post.dict())
    return {
        "data": "post added."
    }
```

Refresh your interactive docs page:

TODO: add image

Test the authentication by trying to visit a protected route without passing in a token:

TODO: add image

Test the routes by creating a new user and copying the generated access token:

TODO: add image

After copying it, click on the authorize button in the top right corner and paste the token:

TODO: add image

You should now be able to use the protected routes:

TODO: add image

## Conclusion

This post covered the process of securing a FastAPI application with JSON Web Tokens.

Check your understanding by reviewing the objectives from the beginning of this post. You can find the source code in the [fastapi-jwt](https://github.com/testdrivenio/fastapi-jwt) repository. Thanks for reading.

Looking for some challenges?

1. Hash the passwords before saving it using passlib or bcrypt.
2. Move the user and post from temporary storage to either MongoDB or MySQL. You can follow the steps in [Building a CRUD App with FastAPI and MongoDB](https://testdriven.io/blog/fastapi-mongo/) to set up a MongoDB database and deploy to Heroku.
3. Add a refresh token to automatically issue new JWT when it expires. You can start by reading a great explanation by the [author of flask-jwt](https://stackoverflow.com/questions/46197050/flask-jwt-extend-validity-of-token-on-each-request/46284627#46284627)