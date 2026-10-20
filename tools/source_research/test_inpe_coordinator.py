from datetime import datetime, timezone
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock
from inpe_package import load
from test_inpe_snapshot import record
Coordinator=load('coordinator').Coordinator


class CoordinatorTests(IsolatedAsyncioTestCase):
    async def test_found_empty_found_and_failed_recovery(self):
        clock=[0]
        receipt=[datetime(2026,10,20,tzinfo=timezone.utc)]
        r=record(('AC',))
        fetch=AsyncMock(side_effect=[(r,),(),(r,),OSError('private server text'),()])
        owner=Coordinator(None,['AC'],fetch=fetch,monotonic=lambda:clock[0],now=lambda:receipt[0],jitter=lambda:0)
        first=await owner.async_refresh()
        self.assertEqual(len(first.records),1)
        self.assertIs(await owner.async_refresh(),first)
        for step,count,status in ((1,0,'success'),(2,1,'success'),(3,1,'error'),(4,0,'success')):
            clock[0]=step*3600
            receipt[0]=datetime(2026,10,20,step,tzinfo=timezone.utc)
            result=await owner.async_refresh()
            self.assertEqual(len(result.records),count)
            self.assertEqual(result.response_status,status)
            self.assertFalse(result.complete)
            if status=='error':
                self.assertEqual(result.last_success.hour,2)
                self.assertEqual(result.error,'retrieval_failed')
            else:self.assertEqual(result.last_success.hour,step)
        self.assertEqual(fetch.await_count,5)

    async def test_partial_failure_does_not_publish_partial_list(self):
        fetch=AsyncMock(side_effect=[(record(('AC',)),),OSError()])
        owner=Coordinator(None,['AC','AM'],fetch=fetch,jitter=lambda:0)
        result=await owner.async_refresh()
        self.assertEqual(result.response_status,'error')
        self.assertEqual(result.records,())
        self.assertIsNone(result.last_success)
        await owner.async_refresh()
        self.assertEqual(fetch.await_count,2)
