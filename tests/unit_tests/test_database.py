def test_timescale_hypertable():
    from backend.database.timescale_schema import engine
    with engine.connect() as conn:
        result = conn.execute("""
            SELECT hypertable_name 
            FROM timescaledb_information.hypertables
            WHERE hypertable_name = 'sensor_readings'
        """)
        assert result.fetchone() is not None

def test_influx_continuous_query():
    from backend.database.influxdb_config import client
    query_api = client.query_api()
    query = '''
        SHOW CONTINUOUS QUERIES
    '''
    result = query_api.query(query)
    assert any(cq.name == 'hourly_avg' 
              for bucket in result 
              for cq in bucket.records)
