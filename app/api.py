from fastapi import FastAPI, Body, Depends

from app.model import PostSchema, PostUpdateSchema, UserSchema, UserLoginSchema
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import signJWT


posts = [
    {
        "id": 1,
        "title": "Pancake",
        "content": "Lorem Ipsum ..."
    }
]

users = []

app = FastAPI()


# helpers

def check_user(data: UserLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False


# routes

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


@app.post("/posts", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def add_post(post: PostSchema) -> dict:
    post.id = len(posts) + 1
    posts.append(post.dict())
    return {
        "data": "post added."
    }


@app.put("/posts/{id}", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def update_post(id: int, body: PostUpdateSchema) -> dict:
    for post in posts:
        if post["id"] == id:
            post["title"] = body.title
            post["content"] = body.content
            return {
                "data": f"post with id {id} has been updated."
            }

    return {
        "data": f"post with id {id} not found."
    }


@app.delete("/posts/{id}", dependencies=[Depends(JWTBearer())], tags=["posts"])
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


@app.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    users.append(user) # replace with db call, making sure to hash the password first
    return signJWT(user.email)


@app.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }
