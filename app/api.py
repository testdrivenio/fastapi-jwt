from fastapi import FastAPI, Body, Depends

from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import signJWT
from app.model import UserSchema, UserLoginSchema, PostSchema, PostUpdateSchema

app = FastAPI()

users = []
posts = [{"id": 1, "title": "Pancake", "content": "Lorem Ipsum ..."}]


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your post list."}


@app.get("/post", tags=["posts"])
async def get_posts() -> dict:
    return {"data": posts}


@app.get("/post/{id}", tags=["posts"])
async def get_single_post(id: int) -> dict:
    if id > len(posts):
        return {"error": "No such post with this ID."}

    for post in posts:
        if post["id"] == id:
            return {"data": post}


@app.post("/post", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def add_post(post: PostSchema) -> dict:
    post.id = len(posts) + 1
    posts.append(post.dict())
    return {"data": "post added."}


@app.put("/post/{id}", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def update_post(id: int, body: PostUpdateSchema) -> dict:
    for post in posts:
        if post["id"] == id:
            post["title"] = body.title
            post["content"] = body.content
            return {"data": f"post with id {id} has been updated."}

    return {"data": f"post with id {id} not found."}


@app.delete("/post/{id}", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def delete_post(id: int) -> dict:
    for post in posts:
        if int(post["id"]) == id:
            posts.remove(post)
            return {"data": f"post with id {id} has been removed."}
    return {"data": f"post with id {id} not found."}


@app.post("/user/signup", tags=["User"])
async def create_user(user: UserSchema = Body(...)):
    users.append(user)
    return signJWT(user.email)


def check_user(data: UserLoginSchema):
    print(data)
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False


@app.post("/user/login", tags=["User"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {"error": "Wrong login details!"}
