from fastapi import status


def test_root(client):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Welcome to the boilerplate API"

def test_probe(client):
    response = client.get("/probe")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "I am the Python FastAPI API responding"
