from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>MySite</title>
        </head>
        <body>
            <h1>Добро пожаловать на мой сайт!</h1>
            <p>Это стартовая страница моего FastAPI приложения.</p>
        </body>
    </html>
    """