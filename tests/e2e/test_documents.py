def test_can_upload_and_download_a_file(client):
    project_info = {"name": "test", "description": "testing"}
    res = client.post("/projects", json=project_info)
    assert res.status_code == 201

    file = b"foo"
    filename = "bar"
    res = client.post("/projects/1/documents", files={"file": (filename, file)})
    assert res.status_code == 201
    assert res.json()["filename"] == filename

    file_id = res.json()["id"]
    res = client.get(f"/documents/{file_id}")
    assert res.status_code == 200
    assert res.read() == file

    res = client.get("/projects/1/documents")
    assert res.status_code == 200
    json = res.json()
    assert len(json) == 1
    assert json[0]["id"] == file_id
    assert json[0]["filename"] == filename
