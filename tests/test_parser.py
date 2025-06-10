from datetime import datetime, timezone, timedelta
import sys
import os

# Add src directory to path to import log_parser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from log_parser import parse_log_line, parse_timestamp

def test_parse_timestamp_zulu():
    ts_str = "10/Jun/2025:21:18:06.100000Z"
    expected = datetime(2025, 6, 10, 21, 18, 6, 100000, tzinfo=timezone.utc)
    assert parse_timestamp(ts_str) == expected

def test_parse_timestamp_offset():
    ts_str = "10/Jun/2025:11:06:44.711859+0200"
    tz = timezone(timedelta(hours=2))
    expected = datetime(2025, 6, 10, 11, 6, 44, 711859, tzinfo=tz)
    assert parse_timestamp(ts_str) == expected

def test_parse_log_line_bind():
    line = '[10/Jun/2025:21:18:06.100000Z] conn=100 op=0 BIND dn="uid=test,ou=people,dc=example,dc=com" method=128 version=3'
    parsed = parse_log_line(line)
    assert parsed is not None
    assert parsed['type'] == 'BIND'
    assert parsed['conn'] == 100
    assert parsed['op'] == 0
    assert parsed['dn'] == 'uid=test,ou=people,dc=example,dc=com'
    assert parsed['timestamp'] == datetime(2025, 6, 10, 21, 18, 6, 100000, tzinfo=timezone.utc)

def test_parse_log_line_result():
    line = '[10/Jun/2025:21:18:06.200000Z] conn=100 op=0 RESULT err=0 tag=97 nentries=1 etime=0.0'
    parsed = parse_log_line(line)
    assert parsed is not None
    assert parsed['type'] == 'RESULT'
    assert parsed['conn'] == 100
    assert parsed['op'] == 0
    assert parsed['err'] == 0

def test_parse_log_line_closed():
    line = '[10/Jun/2025:21:18:07.200000Z] conn=100 op=-1 fd=12 closed'
    parsed = parse_log_line(line)
    assert parsed is not None
    assert parsed['type'] == 'Disconnect'
    assert parsed['conn'] == 100
    assert parsed['op'] == -1

def test_parse_log_line_unindexed():
    line = '[10/Jun/2025:11:06:44.711859+0200] conn=105 op=1 RESULT err=0 tag=101 nentries=1 wtime=0.000063 optime=0.000346 etime=0.000409 details="Partially Unindexed Filter"'
    parsed = parse_log_line(line)
    assert parsed is not None
    assert parsed['type'] == 'RESULT'
    assert parsed['conn'] == 105
    assert parsed['details'] == 'Partially Unindexed Filter'
