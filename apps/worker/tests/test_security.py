import time
from product_twin.security import sign,verify
def test_hmac_roundtrip():
    ts=str(int(time.time())); s=sign('POST','/internal/jobs/1/start',ts,b'', 'x'*32); assert verify('POST','/internal/jobs/1/start',ts,b'',s,'x'*32)
def test_rejects_tampering():
    ts=str(int(time.time())); s=sign('POST','/x',ts,b'a','x'*32); assert not verify('POST','/x',ts,b'b',s,'x'*32)
