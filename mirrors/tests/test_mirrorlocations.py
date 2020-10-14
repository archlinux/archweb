from mirrors.tests.conftest import COUNTRY

def test_mirrorlocations_json(client, checklocation):
    response = client.get('/mirrors/locations/json/')
    assert response.status_code == 200
    data = response.json()
    assert 1 == data['version']
    location = data['locations'][0]['country_code']
    assert COUNTRY == location
