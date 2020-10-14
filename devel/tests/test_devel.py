def test_clock(user_client):
    response = user_client.get('/devel/clock/')
    assert response.status_code == 200


def test_profile(user_client):
    response = user_client.get('/devel/profile/')
    assert response.status_code == 200
    # Test changing


def test_stats(user_client):
    response = user_client.get('/devel/stats/')
    assert response.status_code == 200
