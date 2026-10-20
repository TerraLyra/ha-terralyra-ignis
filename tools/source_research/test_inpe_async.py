import asyncio
import unittest
from inpe_package import load
from test_tasalert_async_fetch import Response, Session
from test_inpe_centroids import payload, feature
fetch_state=load('client').fetch_state
FetchError=load('client').FetchError


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_success_and_request_contract(self):
        response=Response([payload([])],headers={'Content-Type':'application/json'})
        session=Session(response)
        self.assertEqual(await fetch_state(session,'AC'),())
        self.assertEqual(session.calls[0][1]['params'],{'id_tipo_reg':'1','uf':'ac'})
        self.assertFalse(session.calls[0][1]['allow_redirects'])
        self.assertTrue(response.closed)

    async def test_error_is_not_empty_success(self):
        for response in (Response(status=429),Response([b'{}'],headers={'Content-Type':'application/json'}),
                         Response([payload([])],headers={'Content-Type':'text/html'}),
                         Response([payload([])],headers={'Content-Type':'application/json','Content-Length':'999'})):
            with self.assertRaises(ValueError): await fetch_state(Session(response),'AC')
            self.assertTrue(response.closed)

    async def test_membership_is_checked(self):
        f=feature();f['properties']['estados']=['AM']
        response=Response([payload([f])],headers={'Content-Type':'application/json'})
        with self.assertRaises(ValueError): await fetch_state(Session(response),'AC')

    async def test_deadline_and_cancellation(self):
        response=Response(wait=True,headers={'Content-Type':'application/json'})
        with self.assertRaises(TimeoutError): await fetch_state(Session(response),'AC',total_timeout=.01)
        self.assertTrue(response.closed)
        response=Response(wait=True,headers={'Content-Type':'application/json'})
        task=asyncio.create_task(fetch_state(Session(response),'AC'))
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertTrue(response.closed)
