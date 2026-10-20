import uvicorn

if __name__ == "__main__":
    print("🔥 Starting FIRELINE Data & Intelligence Service on http://0.0.0.0:8000...")
    print("📖 Swagger UI documentation available at: http://localhost:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
