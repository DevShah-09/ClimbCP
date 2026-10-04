import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema
from app.database.base import Base
from app.models import CFUser, Contest, ContestParticipation, Problem, ProblemAttempt, Topic
from app.services import codeforces_service as cf


@unittest.skipUnless(os.getenv('PROFILE_TEST_POSTGRES_URL'), 'Set PROFILE_TEST_POSTGRES_URL to an isolated PostgreSQL test database')
class ConcurrentProfileSyncTests(unittest.TestCase):
    def setUp(self):
        self.schema = 'profile_sync_test_' + uuid.uuid4().hex
        self.base_engine = create_engine(os.environ['PROFILE_TEST_POSTGRES_URL'])
        with self.base_engine.begin() as connection:
            connection.execute(CreateSchema(self.schema))
        self.engine = self.base_engine.execution_options(schema_translate_map={None: self.schema})
        names = {'cf_users', 'contests', 'contest_participations', 'problems', 'topics', 'problem_topics', 'problem_attempts'}
        Base.metadata.create_all(self.engine, tables=[t for t in Base.metadata.sorted_tables if t.name in names])
        with Session(self.engine) as db:
            db.add(Topic(name='Math'))
            db.commit()

    def tearDown(self):
        with self.base_engine.begin() as connection:
            connection.execute(DropSchema(self.schema, cascade=True))
        self.base_engine.dispose()

    def run_syncs(self, handles, synchronize_contests=False):
        ready = threading.Barrier(len(handles), timeout=15)
        insert_ready = threading.Barrier(len(handles), timeout=15)
        ratings = [dict(contestId=c, contestName=f'Round {c}', rank=100, oldRating=1000,
                        newRating=1200, ratingUpdateTimeSeconds=1700000000) for c in [2263, 2266]]
        def submissions(handle):
            ready.wait()
            return [dict(problem=dict(contestId=c, index='A', name='Shared problem', rating=1000,
                                      tags=['math']), verdict='OK', author=dict(participantType='CONTESTANT'),
                         creationTimeSeconds=1700000000, relativeTimeSeconds=300) for c in [2263, 2266]]
        real_insert = cf._insert_missing
        def insert(db, model, rows, key):
            if synchronize_contests and model is Contest:
                insert_ready.wait()
            return real_insert(db, model, rows, key)
        def sync(handle):
            with Session(self.engine, autoflush=False) as db:
                return cf.sync_user_data(db, handle)
        with patch.object(cf, 'get_user_info', side_effect=lambda h: dict(handle=h, rating=1200, maxRating=1200)), \
             patch.object(cf, 'get_user_rating_history', return_value=ratings), \
             patch.object(cf, 'get_user_submissions', side_effect=submissions), \
             patch.object(cf, '_insert_missing', side_effect=insert), ThreadPoolExecutor(max_workers=len(handles)) as pool:
            results = list(pool.map(sync, handles))
        self.assertTrue(all(r['status'] == 'success' for r in results))
        with Session(self.engine) as db:
            for model, expected in [(CFUser, len(set(handles))), (Contest, 2), (Problem, 2),
                                    (ContestParticipation, 2 * len(set(handles))),
                                    (ProblemAttempt, 2 * len(set(handles)))]:
                self.assertEqual(db.scalar(select(func.count()).select_from(model)), expected, model.__name__)

    def test_different_users_insert_the_same_contests_and_problems_concurrently(self):
        self.run_syncs(['FirstUser', 'SecondUser'], synchronize_contests=True)

    def test_two_first_logins_of_the_same_user(self):
        self.run_syncs(['SameUser', 'SameUser'])

    def test_two_refreshes_of_an_existing_user(self):
        self.run_syncs(['ReturningUser'])
        self.run_syncs(['ReturningUser', 'ReturningUser'])

    def test_existing_unique_code_with_legacy_platform_is_reused(self):
        with Session(self.engine) as db:
            for c in [2263, 2266]:
                db.add(Contest(platform='Codeforces', contest_code=str(c), contest_name='Existing',
                               start_time=datetime(2026, 1, 1), end_time=datetime(2026, 1, 1)))
                db.add(Problem(platform='Codeforces', problem_code=f'{c}A', title='Existing'))
            db.commit()
        self.run_syncs(['ReturningUser'])


if __name__ == '__main__':
    unittest.main()
