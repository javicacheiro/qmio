def test_desktops_admin(client):
    response = client.get("/desktops/v1/admin/desktops")
    assert response.status_code == 200
