def test_desktops(client):
    response = client.get("/desktops/v1/desktops")
    print(response.json)
    assert response.json["desktops"] == ["id1", "id2"]
    assert response.status_code == 200
